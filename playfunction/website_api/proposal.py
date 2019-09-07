import frappe
import json
from frappe import _
from customer import update_customer_profile


@frappe.whitelist()
def get_proposal_list(page_index=0, page_size=10):
	try:
		response = frappe._dict()
		customer = frappe.db.get_value("Customer",{"user": frappe.session.user},"name")
		if not customer:
			response["message"] = "Customer doesn't exists."
			frappe.local.response["http_status_code"] = 422
		else:
			filters = {"party_name": customer, "workflow_state": "Proposal", "docstatus": 0}
			all_records = frappe.get_all("Quotation", filters=filters)
			fields = ["name as proposal_id", "transaction_date as date", "grand_total as amount", "status"]
			proposal_list = frappe.get_all("Quotation", filters=filters,\
				fields=fields, start=page_index, limit=page_size, order_by="creation")
			response.update({
				"data": proposal_list,
				"total": len(all_records)
			})
	except Exception as e:
		frappe.local.response['http_status_code'] = getattr(e, "http_status_code", 500)
		response["message"] = "Unable to fetch Proposal list"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: get_proposal_list")
	finally:
		return response

@frappe.whitelist()
def get_proposal_details(proposal_id):
	try:
		response = frappe._dict()
		if not frappe.db.exists("Quotation", proposal_id):
			response["message"] = "Proposal not found"
			frappe.local.response["http_status_code"] = 404
		else:
			pass
	except Exception as e:
		frappe.local.response['http_status_code'] = getattr(e, "http_status_code", 500)
		response["message"] = "Unable to fetch Proposal Details"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: get_proposal_details")
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
		quote.workflow_state = "Proposal"
		if data:
			data = json.loads(data)
			update_customer_profile(data, quote.party_name)
			quote.delivery_collection_point = data.get("delivery_collection_point")
			quote.delivery_city = data.get("delivery_city")
		quote.flags.ignore_mandatory = True
		quote.save()
		frappe.db.commit()
		response["message"] = "Proposal Sent Successfully"
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
		frappe.delete_doc("Quotation", proposal_id)
		frappe.db.commit()
		response["message"] = "Proposal Deleted Successfully."
	except Exception as e:
		frappe.local.response['http_status_code'] = getattr(e, "http_status_code", 500)
		response["message"] = "Proposal Deletion Failed"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: delete_proposal")
	finally:
		return response