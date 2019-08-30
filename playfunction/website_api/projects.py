import frappe
import json
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_project_list():
	"""Returns project List"""
	try:
		response = frappe._dict()
		fields = ["project_name", "title", "description", "image"]
		project_list = frappe.get_all('Playfunction Project',fields = fields, limit=None, start=None)
		response.update({"data":project_list})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch order list"
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: get_project_list")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def get_project_details(project_id):
	try:
		response = frappe._dict()
		if frappe.db.exists("Playfunction Project", project_id):
			doc = frappe.get_doc("Playfunction Project", project_id)
			response["project_id"] = doc.project_name
			response["title"] = doc.title
			response["description"] = doc.description
			response["image"] = doc.image
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