import frappe
import json
from frappe import _
from frappe.utils import has_common


item_fields = ["item_code", "qty", "discount_percentage", "notes", "rate", "amount"]


@frappe.whitelist()
def get_quote_details(quote_id):
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
			items = []
			# fetch required item details
			for row in quote.get("items"):
				row_data = {}
				for f in item_fields:
					row_data[f] = row.get(f)
				items.append(row_data)
			response["items"] = items

			#check delivery charges
			# TODO - delivery charges condition
			delivery_charges = 0
			for tax_ in quote.get("taxes", []):
				if tax_.get("charge_type") == "Actula": #and tax_.get("account_head"):
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
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: create_quote")
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
		discount:
		notes:
	}
	"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Quotation", quote_id):
			response["message"] = "Quotation not found"
			frappe.local.response = 404
		else:
			if not all([ f in item_fields for f in items.keys()]):
				response["message"] = "Invalid Data"
				frappe.local.response["http_status_code"] = 422
			else:
				quote = frappe.get_doc("Quotation", quote_id)
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
		response["message"] = "Quotation Creation failed"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: update_quote")
	finally:
		return response