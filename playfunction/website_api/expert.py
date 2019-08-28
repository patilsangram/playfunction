import frappe
import json
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_expert_list():
	"""Returns expert List"""
	try:
		response = frappe._dict()
		fields = ["full_name", "profession", "bio", "image"]
		expert_list = frappe.get_all('Playfunction Expert',fields = fields)
		response.update({"data":expert_list})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch expert list"
		frappe.log_error(message = frappe.get_traceback() , title = "website API: get_expert_list")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def get_expert_details(full_name):
	try:
		response = frappe._dict()
		if frappe.db.exists("Playfunction Expert", full_name):
			doc = frappe.get_doc("Playfunction Expert", full_name)
			response["full_name"] = doc.get("full_name")
			response["profession"] = doc.get("profession")
			response["bio"] = doc.get("bio")
			response["image"] = doc.get("image")
		else:
			response["status_code"] = 404
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch expert Details: {}".format(str(e))
		frappe.log_error(message = frappe.get_traceback() , title = "website API: get_expert_details")
	finally:
		return response