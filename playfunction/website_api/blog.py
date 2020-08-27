import frappe
import json
from frappe import _


fields = ["name", "title", "content", "category as blog_category", "image"]

@frappe.whitelist(allow_guest=True)
def get_blog_list(page_index=0, page_size=10):
	"""Returns blog post List"""
	try:
		response = frappe._dict()
		filters = {"published": 1}
		all_records = frappe.get_all("Blog Post", filters=filters)
		blog_list = frappe.get_all("Blog Post", filters=filters, fields=fields, start=page_index,\
			limit=page_size, order_by="creation")
		response.update({
			"data": blog_list,
			"total": len(all_records)
		})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		# msg = "Unable to fetch blog list"
		response["message"] = "{} המערכת זיהתה בעיה בהשגת הנתונים".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title="website API: get_blog_list")
	finally:
		return response


@frappe.whitelist(allow_guest=True)
def get_blog(blog_id):
	"""Return single Blog Details"""
	try:
		response = frappe._dict()
		if frappe.db.exists("Blog Post", blog_id):
			blog_data = frappe.db.get_value("Blog Post", blog_id, fields, as_dict=True)
			response["data"] = blog_data
		else:
			frappe.local.response['http_status_code'] = 404
			response["message"] = "בלוג לא נמצא"
			# msg = "Blog not found"
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		# msg = "Unable to fetch blog Details: {}"
		response["message"] = "{} : המערכת זיהתה בעיה בהשגת הנתונים".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title="website API: get_blog")
	finally:
		return response
