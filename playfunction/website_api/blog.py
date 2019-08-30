import frappe
import json
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_blog_list():
	"""Returns blog List"""
	try:
		response = frappe._dict()
		fields = ["name", "title", "content", "blog_category", "image"]
		blog_list = frappe.get_all('Blog Post',fields = fields, limit=None, start=None)
		response.update({"data":blog_list})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch blog list".format(str(e))
		frappe.log_error(message = frappe.get_traceback() , title = "website API: get_blog_list")
	finally:
		return response


@frappe.whitelist(allow_guest=True)
def get_blog(blog_id):
	try:
		response = frappe._dict()
		if frappe.db.exists("Blog Post", blog_id):
			doc = frappe.get_doc("Blog Post", blog_id)
			response["blog_id"] = doc.name
			response["title"] = doc.title
			response["content"] = doc.content
			response["blog_category"] = doc.blog_category
			response["image"] = doc.image
		else:
			response["status_code"] = 404
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch blog Details: {}".format(str(e))
		frappe.log_error(message = frappe.get_traceback() , title = "website API: get_blog")
	finally:
		return response