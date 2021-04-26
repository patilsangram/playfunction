import frappe
import json
from frappe import _, scrub
from requests import request
from frappe.utils import today
from .order import order_details
from .quotation import get_quote_details
from erpnext.selling.doctype.quotation.quotation import _make_sales_order
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

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
		# check request data

		# if frappe.session.user == "Guest":
		# 	frappe.set_user("Administrator")
		frappe.log_error(message=frappe.local.form_dict, title="Set Payment")

		error = ""
		if frappe.local.form_dict:
			icredit_settings = frappe.get_doc("iCredit Settings", "iCredit Settings")
			data = frappe.local.form_dict
			quote_id = data.get("Custom1")

			# verify payment
			url =  "https://testicredit.rivhit.co.il/API/PaymentPageRequest.svc/Verify"
			headers = {"Content-Type": "application/json", "user-agent": "Playfunction App"}
			verify_data = {
				"GroupPrivateToken": icredit_settings.get("group_private_token"),
				"SaleId": data.get("SaleId"),
				"TotalAmount": data.get("TransactionAmount")
			}
			response = request("POST", url, data=json.dumps(verify_data), headers=headers)

			# update payment status on quotation
			if response.status_code == 200:
				res_status = json.loads(response.text)
				if res_status.get("Status") == "VERIFIED":

					if frappe.db.exists("Quotation", quote_id):
						frappe.db.set_value("Quotation", quote_id, "payment_status", "Paid")
						quote = frappe.get_doc("Quotation", quote_id)
						quote.flags.ignore_permissions = True
						quote.submit()

						#SO
						sales_order = _make_sales_order(quote_id, ignore_permissions=True)
						if sales_order:
							sales_order.delivery_date = frappe.utils.today()
							sales_order.mode_of_order = "Web"
							sales_order.flags.ignore_permissions = True
							sales_order.save()
							sales_order.submit()

						#SI
						si = make_sales_invoice(so.name, ignore_permissions=True)
						si.flags.ignore_permissions = True
						si.submit()

						#PE
						pe = get_payment_entry_custom("Sales Invoice", si.name)
						pe.reference_no = data.get("SaleId")
						pe.reference_date = today()
						pe.flags.ignore_permissions = True
						pe.save()
						pe.submit()
					else: error = "Quotation {} not exists".format(quote_id)
				else:
					error = "Payment Failed: {}".format(res_status)
					frappe.db.set_value("Quotation", quote_id, "payment_status", "Failed")
			else:
				error = "Verify API Fail: {}".format(response.text)

			# mark error
			if error:
				frappe.log_error(message=error, title="Mobile API: set_payment_status")
			return "Payment Status Updated Success"
	except Exception as e:
		frappe.log_error(message=str(e) , title="Mobile API: set_payment_status")

@frappe.whitelist()
def get_payment_entry_custom(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	try:
		doc = frappe.get_doc(dt, dn)
		party_type = "Customer"
		default_account_name = "default_receivable_account"
		party_account = frappe.get_cached_value('Company',  doc.company,  default_account_name)
		party_account_currency = doc.get("party_account_currency")

		# payment type
		payment_type = "Receive"

		# amounts
		grand_total = outstanding_amount = 0
		if party_account_currency == doc.company_currency:
			grand_total = doc.base_rounded_total or doc.base_grand_total
		else:
			grand_total = doc.rounded_total or doc.grand_total
		outstanding_amount = doc.outstanding_amount

		# bank or cash
		df_account = frappe.get_cached_value('Company',  doc.company,  "default_bank_account")
		if df_account:
			account_details = frappe.db.sql("select account_currency, account_type from tabAccount\
				where name = '{}'".format(df_account), as_dict=True)[0]
			bank = frappe._dict({
				"account": df_account,
				"account_currency": account_details.account_currency,
				"account_type": account_details.account_type
			})

		paid_amount = received_amount = 0
		if party_account_currency == bank.account_currency:
			paid_amount = received_amount = abs(outstanding_amount)
		elif payment_type == "Receive":
			paid_amount = abs(outstanding_amount)
		else:
			received_amount = abs(outstanding_amount)

		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = payment_type
		pe.company = doc.company
		pe.cost_center = doc.get("cost_center")
		pe.posting_date = frappe.utils.nowdate()
		pe.mode_of_payment = doc.get("mode_of_payment")
		pe.party_type = party_type
		pe.party = doc.get(scrub(party_type))
		pe.contact_person = doc.get("contact_person")
		pe.contact_email = doc.get("contact_email")

		pe.paid_from = party_account
		pe.paid_to = bank.account
		pe.paid_from_account_currency = party_account_currency
		pe.paid_to_account_currency = bank.account_currency
		pe.paid_amount = paid_amount
		pe.received_amount = received_amount
		pe.allocate_payment_amount = 1
		# pe.letter_head = doc.get("letter_head")
		pe.flags.ignore_permissions = True

		bank_account = frappe.db.sql("""select name from `tabBank Account` where \
			party_type = '{}' and party = '{}' and is_default = 1
		""".format(pe.party_type, pe.party), as_dict=True)

		bank_account = bank_account[0]["name"] if len(bank_account) else ""
		pe.set("bank_account", bank_account)
		pe.set_bank_account_data()

		pe.append("references", {
			'reference_doctype': dt,
			'reference_name': dn,
			"bill_no": doc.get("bill_no"),
			"due_date": doc.get("due_date"),
			'total_amount': grand_total,
			'outstanding_amount': outstanding_amount,
			'allocated_amount': outstanding_amount
		})
		pe.setup_party_account_field()
		pe.set_missing_values()
		if party_account and bank:
			pe.set_exchange_rate()
			pe.set_amounts()
		frappe.log_error(message=pe, title="Mobile API: payment_entry_data")
		return pe
	except Exception as e:
		frappe.log_error(message=error, title="Mobile API: Payment Entry Creation")