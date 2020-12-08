import frappe
import json
from frappe import _
from playfunction.website_api.customer import update_customer_profile


@frappe.whitelist()
def get_proposal_list(page_index=0, page_size=10):
	try:
		response = frappe._dict()
		customer = frappe.db.get_value("Customer",{"user": frappe.session.user},"name")
		if not customer:
			# msg ="Customer doesn't exists."
			response["message"] = "שם משתמש אינו קיים"
			frappe.local.response["http_status_code"] = 422
		else:
			proposal_states = ["Proposal Received", "Proposal Processing", "Proposal Ready"]
			filters = {
				"party_name": customer,
				"workflow_state": ["in", proposal_states],
				"docstatus": 0
			}
			all_records = frappe.get_all("Quotation", filters=filters)
			fields = ["name as proposal_id", "transaction_date as date", "grand_total as amount", "status", "workflow_state as proposal_state"]
			proposal_list = frappe.get_all("Quotation", filters=filters,\
				fields=fields, start=page_index, limit=page_size, order_by="creation desc")
			response.update({
				"data": proposal_list,
				"total": len(all_records)
			})
	except Exception as e:
		frappe.local.response['http_status_code'] = getattr(e, "http_status_code", 500)
		# msg ="Unable to fetch Proposal list"
		response["message"] = "המערכת לא מצליחה לאתר את רשימת הצעת המחיר שלך"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: get_proposal_list")
	finally:
		return response

@frappe.whitelist()
def send_proposal(quote_id, data=None):
	"""
		convert quotation to proposal
		data: {
			:customer_name- customer name
			:phone
			:email_id
			:house_no
			:apartment_no
			:street_address
			:city
			:delivery_collection_point
			:delivery_city
		}
	"""
	try:
		response = frappe._dict()
		quote = frappe.get_doc("Quotation", quote_id)
		quote.workflow_state = "Proposal Received"
		if data:
			data = json.loads(data)
			update_customer_profile(data, quote.party_name)
			quote.delivery_collection_point = data.get("delivery_collection_point")
			quote.delivery_city = data.get("delivery_city")
		quote.flags.ignore_mandatory = True
		quote.save()
		frappe.db.commit()
		# msg ="Proposal Sent Successfully"
		response["message"] = "הבקשה להצעת המחיר נשלחה בהצלחה!"
	except Exception as e:
		frappe.local.response['http_status_code'] = getattr(e, "http_status_code", 500)
		response["message"] = "Proposal Creation Failed"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: send_proposal")
	finally:
		return response

@frappe.whitelist()
def delete_proposal(proposal_id):
	try:
		response = frappe._dict()
		proposal_state = frappe.db.get_value("Quotation", proposal_id, "workflow_state")
		if proposal_state == "Proposal Processing":
			frappe.local.response["http_status_code"] = 422
			# msg = "Can not delete Processing Stage Proposal"
			response["message"] = "לא ניתן להסיר את הרשימה כרגע"
		else:
			frappe.delete_doc("Quotation", proposal_id)
			frappe.db.commit()
			# msg = "Proposal Deleted Successfully."
			response["message"] = "הבקשה שלך להצעת מחיר הוסרה בהצלחה!"
	except Exception as e:
		frappe.local.response['http_status_code'] = getattr(e, "http_status_code", 500)
		# msg ="Proposal Deletion Failed"
		response["message"] = "לא ניתן להסיר כרגע את הבקשה להצעת מחיר"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: delete_proposal")
	finally:
		return response
