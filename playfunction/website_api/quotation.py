import frappe
import json
from frappe import _
from frappe.utils import has_common, flt
from erpnext.selling.doctype.quotation.quotation import make_sales_order

item_fields = ["item_code", "item_name","qty", "discount_percentage", "description", "rate", "amount", "image"]
@frappe.whitelist()
def get_cart_details(quote_id):
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
		frappe.log_error(message=frappe.get_traceback() , title="Wishlist API: get_cart_details")
	finally:
		return response

@frappe.whitelist()
def add_to_cart(items):
	"""
	:param data: {
		items: {
			item_code:
			qty:
		}
	}
	"""
	try:
		response = frappe._dict()
		items = json.loads(items)
		user= frappe.get_doc("User",frappe.session.user)
		#check customer exists or not for the current user
		customer = frappe.db.get_value("Customer",{'user':user.name},"name")
		if not customer:
			response["message"] = "Customer doesn't exists."
			frappe.local.response['http_status_code'] = 200
		else:
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
				response = get_cart_details(quote.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Quotation Creation failed".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title="Wishlist API: add_to_cart")
	finally:
		return response

@frappe.whitelist()
def update_cart(quote_id, items):
	"""
	:params 
		quote_id: quotation
		items: {
		item_code:
		qty:
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
				response = get_cart_details(quote.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Quotation Update failed"
		frappe.log_error(message=frappe.get_traceback() , title="Wishlist API: update_cart")
	finally:
		return response

@frappe.whitelist()
def delete_cart_item(quote_id, item_code):
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
				response = get_cart_details(quote_id)
			frappe.db.commit()
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to Delete Quote Item"
		frappe.log_error(message=frappe.get_traceback() , title="Wishlist API: delete_cart_item")
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
		frappe.log_error(message=frappe.get_traceback() , title="Wishlist API: place_order")
	finally:
		return response

@frappe.whitelist()
def order_details(order_id):
	"""Return Sales Order Details"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Sales Order", order_id):
			response["message"] = "Sales Order not found"
			frappe.local.response["http_status_code"] = 404
		else:
			doc = frappe.get_doc("Sales Order", order_id)
			response["customer"] = doc.customer
			response["order_id"] = doc.name

			# item details
			items = []
			fields = ["item_code", "description", "qty", "rate",
				"discount_percentage", "discount_amount", "amount"]
			for item in doc.get("items"):
				row_data = {}
				for f in fields:
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
		response["message"] = "Failed to fetch Sales Order Details"
		frappe.log_error(message=frappe.get_traceback() , title="Wishlist API: order_details")
	finally:
		return response

@frappe.whitelist()
def update_order(order_id, items):
	"""
	:params
		order_id: sales_order
		items: {
		item_code:
		qty:
	"""
	try:
		fields = ["item_code", "description", "qty", "rate", "discount_percentage"]
		response = frappe._dict()
		items = json.loads(items)
		if not frappe.db.exists("Sales Order", order_id):
			response["message"] = "Sales Order not found"
			frappe.local.response['http_status_code'] = 404
		else:
			if not all([ f in fields for f in items.keys()]) or not items.get("item_code"):
				response["message"] = "Invalid Data"
				frappe.local.response["http_status_code"] = 422
			else:
				order = frappe.get_doc("Sales Order", order_id)
				existing_item = False
				for row in order.get("items"):
					# update item row
					if row.get("item_code") == items.get("item_code"):
						existing_item = True
						row.update(items)
				# add new item
				if not existing_item:
					order.append("items", items)
				order.save()
				frappe.db.commit()
				response = order_details(order.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Sales Order update failed"
		frappe.log_error(message=frappe.get_traceback() , title="Wishlist API: update_order")
	finally:
		return response

@frappe.whitelist()
def request_for_quotation(items):
	"""
	:param data: {
		items: {
			item_code:
			qty:
		}
	}
	"""
	try:
		response = frappe._dict()
		items = json.loads(items)
		rfq = frappe.new_doc("Request for Quotation")
		# update price list price
		item_rate = frappe.db.get_value("Item", items.get("item_code"), ["cost_price", "last_purchase_rate"], as_dict=True)
		items["price_list_rate"] = item_rate.get("cost_price") or item_rate.get("last_purchase_rate") or 0
		if "discount_percentage" in items:
			items["margin_type"] = "Percentage"
		rfq.append("items", items)
		rfq.flags.ignore_mandatory = True
		rfq.save()
		frappe.db.commit()
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Request For Quotation creation failed".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title="Wishlist API: request_for_quotation")
	finally:
		return response

@frappe.whitelist()
def get_rfq_details(rfq_id):
	try:
		response = frappe._dict()
		if not frappe.db.exists("Request for Quotation", rfq_id):
			response["message"] = "Request for Quotation not found"
			frappe.local.response["http_status_code"] = 404
		else:
			doc = frappe.get_doc("Request for Quotation", rfq_id)
			# item details
			items = []
			fields = ["item_code", "item_name", "image_view", "description", "qty",]
			for item in doc.get("items"):
				row_data = {}
				for f in fields:
					row_data[f] = item.get(f)
				items.append(row_data)
			response["items"] = items
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Failed to fetch request for quotation Details"
		frappe.log_error(message=frappe.get_traceback() , title="Wishlist API: get_rfq_details")
	finally:
		return response