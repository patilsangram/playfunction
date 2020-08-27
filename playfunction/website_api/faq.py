import frappe


@frappe.whitelist(allow_guest=True)
def get_faq():
	try:
		response = frappe.get_all("FAQ Item", fields=["question", "answer"])
	except Exception as e:
		frappe.local.response['http_status_code'] = getattr(e, "http_status_code", 500)
		# msg = "Failed to fetch FAQ"
		response = "המערכת זיהתה בעיה בקבלת הנתונים"
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: get_faq")
	finally:
		return response
