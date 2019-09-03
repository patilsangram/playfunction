import frappe
import json
from frappe import _


fields = ["name", "full_name", "profession", "bio", "image"]

@frappe.whitelist(allow_guest=True)
def get_expert_list(page_index=0, page_size=10):
	"""Returns expert List"""
	try:
		response = frappe._dict()
		all_records = frappe.get_all("Playfunction Expert")
		expert_list = frappe.get_all("Playfunction Expert", fields=fields,\
			start=page_index, limit=page_size, order_by="creation")
		response.update({
			"data": expert_list,
			"total": len(all_records)
		})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch expert list"
		frappe.log_error(message=frappe.get_traceback() , title="website API: get_expert_list")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def get_expert_details(expert_id):
	try:
		response = frappe._dict()
		if frappe.db.exists("Playfunction Expert", expert_id):
			blog_data = frappe.db.get_value("Playfunction Expert", expert_id, fields, as_dict=True)
			response["data"] = blog_data
		else:
			frappe.local.response['http_status_code'] = 404
			response["message"] = "Given Expert ID Not found"
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch expert Details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title="website API: get_expert_details")
	finally:
		return response