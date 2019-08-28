import frappe
import json
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_project_list():
	"""Returns project List"""
	try:
		response = frappe._dict()
		fields = ["project_name", "title", "description", "image"]
		project_list = frappe.get_all('Playfunction Project',fields = fields)
		response.update({"data":project_list})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch order list"
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: get_project_list")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def get_project_details(project_name):
	try:
		response = frappe._dict()
		if frappe.db.exists("Playfunction Project", project_name):
			doc = frappe.get_doc("Playfunction Project", project_name)
			response["project_name"] = doc.get("project_name")
			response["title"] = doc.get("title")
			response["description"] = doc.get("description")
			response["image"] = doc.get("image")
		else:
			response["status_code"] = 404
			response["message"] = "Projects not found"
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch project Details: {}".format(str(e))
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: get_project_details")
	finally:
		return response