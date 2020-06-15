import frappe
import json
from frappe import _
from frappe.utils import has_common, flt

item_fields = ["item_code", "item_name","qty", "discount_percentage", "description", "rate", "amount", "image"]



@frappe.whitelist(allow_guest=True)
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
			sp_without_vat = 0
			for row in quote.get("items"):
				row_data = {}
				for f in item_fields:
					row_data[f] = row.get(f)
				# selling/before discount price of Item
				row_data["selling_price"] = frappe.db.get_value("Item",
					row.get("item_code"), "sp_with_vat") or 0
				item_details = frappe.db.get_value("Item", row.get("item_code"),["sp_with_vat", "last_purchase_rate", "discount_percentage"], as_dict=True)
				if item_details.get("discount_percentage") > 0:
					sp_without_vat = sp_without_vat + (frappe.db.get_value("Item",row.get("item_code"), "sp_without_vat") * row.get("qty"))*item_details.get("discount_percentage")/100
				else:
					sp_without_vat =  sp_without_vat + (frappe.db.get_value("Item",row.get("item_code"), "sp_without_vat") * row.get("qty") )
				items.append(row_data)
			response["items"] = items
			#delivery_details
			response["delivery_collection_point"] = quote.get("delivery_collection_point")
			response["shipping_type"] = quote.get("shipping_type")
			response["delivery_city"] = quote.get("delivery_city")

			#check delivery charges
			delivery_account = frappe.db.get_value("Account", {
				"account_name": "Delivery Charge"
			}, "name")

			# vat account
			vat_account = frappe.db.get_value("Account", {
				"account_name": "VAT 17%"
			}, "name")

			delivery_charges = sales_tax = 0
			for tax_ in quote.get("taxes", []):
				if tax_.get("account_head") == delivery_account:
					delivery_charges = tax_.get("tax_amount")
				elif tax_.get("account_head") == vat_account:
					sales_tax =  tax_.get("tax_amount")

			# taxes & total section
			response["discount"] = quote.get("discount_amount", 0)
			response["total"] = quote.get("grand_total", 0)
			# response["total"] = sp_without_vat
			response["delivery_charges"] = delivery_charges
			# response["sales_tax"] = sales_tax
			# response["sales_tax"] = quote.get("total")-sp_without_vat
			sales_tax = quote.get("total")-sp_without_vat if quote.get("total") != 0 and sp_without_vat !=0 else 0
			response["sales_tax"] = flt(sales_tax,2)
			response["amount_due"] = flt(sp_without_vat,2)
			# response["sub_total"] = sp_without_vat
			response["sub_total"] = quote.get("total")
			# proposal_stages
			proposal_state = ["Proposal Received", "Proposal Processing", "Proposal Ready"]
			if quote.get("workflow_state") in proposal_state:
				response["proposal_state"] = quote.get("workflow_state")
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch Quotation Details"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: get_cart_details")
	finally:
		return response

@frappe.whitelist()
def add_to_cart(items, is_proposal=False):
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
			if not has_common(["item_code", "qty"], items.keys()) or not all([ f in item_fields for f in items.keys()]):
				response["message"] = "Invalid data"
				frappe.local.response["http_status_code"] = 422
			else:
				quote = frappe.new_doc("Quotation")
				quote.party_name = customer
				# update price list price
				item_details = frappe.db.get_value("Item", items.get("item_code"),\
					["sp_with_vat", "last_purchase_rate", "discount_percentage"], as_dict=True)
				items["price_list_rate"] = item_details.get("sp_with_vat") or item_details.get("last_purchase_rate") or 0
				if item_details.get("discount_percentage") > 0:
					items["margin_type"] = "Percentage"
					items["discount_percentage"] = item_details.get("discount_percentage")
				quote.append("items", items)
				# proposal
				if is_proposal:
					quote.workflow_state = "Proposal Received"

				# #VAT 17%
				# vat_account = frappe.db.get_value("Account", {
				# 	"account_name": "VAT 17%"
				# }, ["name", "tax_rate"], as_dict=True)
				#
				# quote.taxes_and_charges = vat_account.get("name")
				# vat_tax = {
				# 	"account_head": vat_account.get("name"),
				# 	"rate": vat_account.get("tax_rate"),
				# 	"charge_type": "On Net Total",
				# 	"description": vat_account.get("name")
				# }
				# quote.append("taxes", vat_tax)
				quote.save(ignore_permissions=True)
				frappe.db.commit()
				response = get_cart_details(quote.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Quotation Creation failed".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title="Website API: add_to_cart")
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
				item_details = frappe.db.get_value("Item", items.get("item_code"),\
					["sp_with_vat", "discount_percentage"], as_dict=True)
				if item_details.get("discount_percentage", 0.00) > 0:
					items["margin_type"] = "Percentage"
					items["discount_percentage"] = item_details.get("discount_percentage")
				items["price_list_rate"] = item_details.get("sp_with_vat", 0)
				existing_item = False
				for row in quote.get("items"):
					# update item row
					if row.get("item_code") == items.get("item_code"):
						existing_item = True
						updatd_qty = row.get("qty") + items.get("qty")
						items["qty"] = int(updatd_qty)
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
		frappe.log_error(message=frappe.get_traceback() , title="Website API: update_cart")
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
		frappe.log_error(message=frappe.get_traceback() , title="Website API: delete_cart_item")
	finally:
		return response
