import frappe
import json
from frappe import _


fields = ["name","project_name", "title", "description", "image", "category"]

@frappe.whitelist(allow_guest=True)
def get_project_list(page_index=0, page_size=10):
	"""Returns project List"""
	try:
		response = frappe._dict()
		all_records = frappe.get_all("Playfunction Project")
		project_list = frappe.get_all("Playfunction Project", fields=fields, start=page_index,
			limit=page_size, order_by="creation")
		response.update({
			"data": project_list,
			"total": len(all_records)
		})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		# msg = "Unable to fetch Project list"
		response["message"] = "המערכת זיהתה בעיה בהצגת הפרויקט"
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: get_project_list")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def get_project_details(project_id):
	try:
		response = frappe._dict()
		if frappe.db.exists("Playfunction Project", project_id):
			project_data = frappe.db.get_value("Playfunction Project", project_id, fields, as_dict=True)
			response["data"] = project_data
		else:
			# msg = "Given Project ID not found"
			response["message"] = "המערכת זיהתה בעיה בהצגת הפרויקט"
			frappe.local.response["http_status_code"] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		# msg = "Unable to fetch Project Details:"
		response["message"] = "{} המערכת זיהתה בעיה בהצגת הפרויקט".format(str(e))
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: get_project_details")
	finally:
		return response
