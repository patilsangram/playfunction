import frappe
import json
from frappe import _
from frappe.utils import has_common, flt
from order import order_details
from erpnext.selling.doctype.quotation.quotation import make_sales_order


item_fields = ["item_code", "item_name","qty", "discount_percentage", "description", "notes", "rate", "amount"]


@frappe.whitelist()
def get_quotation_list():
	"""Return Quotation List"""
	try:
		response = frappe._dict()
		filters = {}
		fields = ["name as quote_id", "party_name as customer", "transaction_date", "grand_total", "status"]
		quotation_list = frappe.get_list("Quotation",filters=filters, fields=fields)
		response["data"] = quotation_list
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch Quotations."
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: get_quotation_list")
	finally:
		return response

@frappe.whitelist()
def get_quote_details(quote_id=None):
	"""
		return quotation details.
		items, taxes and total
	"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Quotation", quote_id):
			response["message"] = "Invalid Quotation"
			frappe.local.response["http_status_code"] = 404
		else:
			quote = frappe.get_doc("Quotation", quote_id)
			response["customer"] = quote.party_name
			response["quote_id"] = quote.name
			items = []
			# fetch required item details
			for row in quote.get("items"):
				row_data = {}
				for f in item_fields:
					row_data[f] = row.get(f)
				items.append(row_data)
			response["items"] = items

			#check delivery charges
			delivery_account = frappe.db.get_value("Account", {
				"account_name": "Delivery Charge"
			}, "name")

			delivery_charges = 0
			for tax_ in quote.get("taxes", []):
				if tax_.get("account_head") == delivery_account:
					delivery_charges = tax_.get("tax_amount")
					break;

			# taxes & total section
			response["discount"] = quote.get("discount_amount", 0)
			response["total"] = quote.get("total", 0)
			response["delivery_charges"] = delivery_charges
			response["amount_due"] = quote.get("total")
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch Quotation Details"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: get_quote_details")
	finally:
		return response

@frappe.whitelist()
def create_quote(customer, items):
	"""
	:param data: {
		customer:
		items: {
			item_code:
			qty:
			discount_percentage:
			notes:
		}
	}
	"""
	try:
		response = frappe._dict()
		items = json.loads(items)
		if not has_common(["item_code", "qty"], items.keys()) or \
			not all([ f in item_fields for f in items.keys()]):
			response["message"] = "Invalid data"
			frappe.local.response["http_status_code"] = 422
		else:
			quote = frappe.new_doc("Quotation")
			quote.party_name = customer
			# update price list price
			item_rate = frappe.db.get_value("Item", items.get("item_code"), ["cost_price", "last_purchase_rate"], as_dict=True)
			items["price_list_rate"] = item_rate.get("cost_price") or item_rate.get("last_purchase_rate") or 0
			if "discount_percentage" in items:
				items["margin_type"] = "Percentage"
			quote.append("items", items)
			quote.save()
			frappe.db.commit()
			response = get_quote_details(quote.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Quotation Creation failed"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: create_quote")
	finally:
		return response

@frappe.whitelist()
def update_quote(quote_id, items):
	"""
	:params 
		quote_id: quotation
		items: {
		item_code:
		qty:
		rate: Unit Price
		discount_percentage:
		description:
		notes: 
	}
	"""
	try:
		response = frappe._dict()
		items = json.loads(items)

		if not frappe.db.exists("Quotation", quote_id):
			response["message"] = "Quotation not found"
			frappe.local.response['http_status_code'] = 404
		else:
			if not all([ f in item_fields for f in items.keys()]):
				response["message"] = "Invalid Data"
				frappe.local.response["http_status_code"] = 422
			else:
				quote = frappe.get_doc("Quotation", quote_id)
				if items.get("discount_percentage"):
					items["margin_type"] = "Percentage"
					items["price_list_rate"] = items.get("rate") or \
						frappe.db.get_value("Item", items.get("item_code"), "cost_price")
					items["rate"] = 0
				existing_item = False
				for row in quote.get("items"):
					# update item row
					if row.get("item_code") == items.get("item_code"):
						existing_item = True
						row.update(items)
				# add new item
				if not existing_item:
					quote.append("items", items)
				quote.save()
				frappe.db.commit()
				response = get_quote_details(quote.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Quotation Update failed"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: update_quote")
	finally:
		return response

@frappe.whitelist()
def delete_quote_item(quote_id, item_code):
	"""Delete given item_codes from Quote if all deleted then delete Quote"""
	try:
		response = frappe._dict()
		item_code = item_code.encode('utf-8')
		item_list= [ i.strip() for i in item_code.split(",")]

		if not isinstance(item_code, list):
			item_code = [item_code]
		if not frappe.db.exists("Quotation", quote_id):
			response["message"] = "Quotation not found"
			frappe.local.response['http_status_code'] = 404
		else:
			quote = frappe.get_doc("Quotation", quote_id)
			new_items = []
			for idx, row in enumerate(quote.get("items")):
				if not row.item_code in item_list:
					new_items.append(row)
			quote.items = new_items
			quote.flags.ignore_mandatory = True
			quote.save()
			if not len(quote.get("items", [])):
				frappe.delete_doc("Quotation", quote_id)
				response["message"] = "Deleted all items"
				frappe.local.response["http_status_code"] = 200
			else:
				response = get_quote_details(quote_id)
			frappe.db.commit()
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to Delete Quote Item"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: delete_quote_item")
	finally:
		return response

@frappe.whitelist()
def quotation_details(quote_id):
	"""Get Detailed Quotation"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Quotation", quote_id):
			response["message"] = "Quotation not found"
			frappe.local.response["http_status_code"] = 404
		else:
			doc = frappe.get_doc("Quotation", quote_id)
			response["customer"] = doc.party_name
			response["quote_id"] = doc.name

			# item details
			items = []
			for item in doc.get("items"):
				row_data = {}
				for f in item_fields:
					row_data[f] = item.get(f)
				items.append(row_data)
			response["items"] = items

			# tax, delivery & totals
			response["total"] = doc.get("total")
			response["additional_discount_percentage"] = doc.get("additional_discount_percentage")
			response["after_discount"] = doc.get("net_total")
			response["grand_total"] = doc.get("grand_total")
			response["delivery_charges"] = 0
			response["vat"] = 0

			delivery_account = frappe.db.get_value("Account", {
				"account_name": "Delivery Charge"
			}, "name")

			vat_account = frappe.db.get_value("Account", {
				"account_name": "VAT 17%"
			}, "name")

			for t in doc.get("taxes"):
				if t.account_head == delivery_account:
					response["delivery_charges"] = t.get("tax_amount")
				elif t.account_head == vat_account:
					response["vat"] = t.get("tax_amount")
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Failed to fetch Quotation Details"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: quotation_details")
	finally:
		return response

@frappe.whitelist()
def place_order(quote_id):
	try:
		response = frappe._dict()
		if not frappe.db.exists("Quotation", quote_id):
			response["message"] = "Quotation not found"
			frappe.local.response["http_status_code"] = 404
		else:
			doc = frappe.get_doc("Quotation", quote_id)
			doc.workflow_state = "Approved"
			doc.save()
			doc.submit()

			# sales order
			sales_order = make_sales_order(doc.name)
			if sales_order:
				sales_order.delivery_date = frappe.utils.today()
				sales_order.save()
				response["message"] = "Order Placed Successfully."
				response["order_id"] = sales_order.name
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Error occured while placing order"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: place_order")
	finally:
		return response

@frappe.whitelist()
def add_delivery_charges(dt, dn, delivery_charge):
	"""Add delivery charges in tax table"""
	try:
		response = frappe._dict()
		if not frappe.db.exists(dt, dn):
			response["message"] = "{} not found".format(dt)
			frappe.local.response["http_status_code"] = 404
		else:
			doc = frappe.get_doc(dt, dn)
			delivery_account = frappe.db.get_value("Account", {
				"account_name": "Delivery Charge"
			}, "name")

			if delivery_account:
				doc.append("taxes", {
					"charge_type": "Actual",
					"account_head": delivery_account,
					"tax_amount": flt(delivery_charge),
					"description": "Delivery Charges"
				})
				doc.save()
				if dt == "Quotation":
					response = quotation_details(doc.name)
				else:
					response = order_details(doc.name)
			else:
				response["message"] = "Delivery Account not found"
				frappe.local.response["http_status_code"] = 422
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to add Delivery Charges"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: add_delivery_charges")
	finally:
		return response


@frappe.whitelist()
def add_discount(dt, dn, discount):
	"""Add additional Discount percentage"""
	try:
		response = frappe._dict()
		if not frappe.db.exists(dt, dn):
			response["message"] = "{} not found".format(dt)
			frappe.local.response["http_status_code"] = 404
		else:
			# TODO - check apply_discount_on ?
			doc = frappe.get_doc(dt, dn)
			doc.apply_discount_on = "Grand Total"
			doc.additional_discount_percentage = flt(discount)
			doc.save()
			if dt == "Quotation":
				response = quotation_details(doc.name)
			else:
				response = order_details(doc.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to add Discount"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: add_discount")
	finally:
		return response