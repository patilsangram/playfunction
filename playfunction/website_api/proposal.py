import frappe
import json
from frappe import _



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