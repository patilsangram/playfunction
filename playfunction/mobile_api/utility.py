import frappe
import json
from .order import order_details
from .quotation import get_quote_details

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
					frappe.db.commit()
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

@frappe.whitelist()
def create_copy(dt, dn, customer):
	"""
		create record copy update customer and send record details
		:param dt -- doctype
		:param dn -- docname
		:param customer
	"""
	try:
		response = frappe._dict()
		customer_field = "party_name" if dt == "Quotation" else "customers"
		if not frappe.db.exists(dt, dn):
			response["message"] = "Record Not found"
			frappe.local.response["http_status_code"] = 404
		else:
			existing_doc = frappe.get_doc(dt, dn)
			record_copy = frappe.copy_doc(existing_doc)
			if dt == "Quotation":
				record_copy.party_name = customer
			else:
				record_copy.customer = customer
			record_copy.title = customer
			record_copy.save()
			response = get_quote_details(record_copy.name) if dt == "Quotation" \
				else order_details(record_copy.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to Create a Record Copy"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: create_copy")
	finally:
		return response


@frappe.whitelist(allow_guest=True)
def set_payment_status(data=None):
	try:
		data = data if data else {}
		data = json.loads(data)
		if data.get("order_id") and frappe.db.exists("Sales Order", data.get("order_id")):
			frappe.db.set_value("Sales Order", data.get("order_id"), "payment_status", "Paid")
		return "Payment Status Updated Successfully"
	except Exception as e:
		frappe.log_error(message=str(e) , title="Mobile API: set_payment_status")
