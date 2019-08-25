import frappe


@frappe.whitelist(allow_guest=True)
def get_faq():
	try:
		response = frappe.get_all("FAQ Item", fields=["question", "answer"])
	except Exception as e:
		frappe.local.response['http_status_code'] = getattr(e, "http_status_code", 500)
		response = "Failed to fetch FAQ"
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: get_faq")
	finally:
		return response