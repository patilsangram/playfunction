import frappe
import json


@frappe.whitelist()
def delete_record(dt, dn):
	try:
		response = frappe._dict()
		if not dt or not dn:
			response["message"] = "Invalid Data"
			frappe.local.response["http_status_code"] = 422
		else:
			if frappe.db.exists(dt, dn):
				if frappe.has_permission(dt, "delete"):
					frappe.delete_doc(dt, dn)
					response["message"] = "{}: {} Deleted Successfully.".format(dt, dn)
				else:
					response["message"] = "Don't have delete permission for {}: {}".format(dt, dn)
					frappe.local.response["http_status_code"] = 403
			else:
				response["message"] = "{}: {} Not found".format(dt, dn)
				frappe.local.response["http_status_code"] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable Delete Record"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: delete_record")
	finally:
		return response

@frappe.whitelist()
def send_mail(dt, dn, recipient):
	"""Send the mail to the recipients along with record copy
	:param dt - Doctype
	:param dn - record id
	:param recipient - email_ids
	"""
	try:
		response = frappe._dict()
		if not frappe.db.exists(dt, dn):
			response["message"] = "{}: {} Not found".format(dt, dn)
			frappe.local.response["http_status_code"] = 404
		else:
			subject = "{}-{}".format(dt, dn)
			recipients = [i.strip() for i in recipient.split(",")]
			content = "Hi<br>, Please check attached copy of {}: {}<br>\
				<br><br>Thanks<br>Playfunction Admin.".format(dt, dn)

			frappe.sendmail(recipients=recipients,
				message=content,
				subject=subject,
				delayed=False
			)
			response["message"] = "Mail Sent Successfully."
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Mail Sending failed"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: send_mail")
	finally:
		return response