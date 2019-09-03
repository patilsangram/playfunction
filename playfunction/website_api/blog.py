import frappe
import json
from frappe import _


fields = ["name", "title", "content", "blog_category", "image"]

@frappe.whitelist(allow_guest=True)
def get_blog_list(page_index=0, page_size=10):
	"""Returns blog post List"""
	try:
		response = frappe._dict()
		blog_list = frappe.get_all("Blog Post", fields=fields, start=page_index,\
			limit=page_size, order_by="creation")
		response.update({"data": blog_list})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch blog list".format(str(e))
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
			response["message"] = "Blog Not found"
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch blog Details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title="website API: get_blog")
	finally:
		return response