import frappe
import json
from requests import request

"""
This is common payment APIs file for mobile, website and ERP payment flow
1. For website:
	1.1 Get payment url
	1.2 Store Private/Public Sales Token
	1.3 Check Payment Status
2. For Mobile/ERPNext:
	2.1 Create Rihvit Invoice
	2.2 Manual Payment
"""


@frappe.whitelist()
def get_rihvit_api_token(rihvit_settings):
	"""
	Check API Token in Rihvit Settings, if not generate and save
	:param rihvit_settings: Rihvit Settings dictionary
	:return: API Token
	"""
	try:
		url = "https://api.rivhit.co.il/online/RivhitOnlineAPI.svc/ApiToken.Get"
		method = "POST"
		data = {
			"username": rihvit_settings.get("username"),
			"password": rihvit_settings.get("password"),
			"company_id": rihvit_settings.get("company_id")
		}
		api_token = ""
		headers = {"Content-Type": "application/json"}
		response = request("POST", url, data=json.dumps(data), headers=headers)
		if response.status_code == 200:
			response = json.loads(response.text)
			api_token = response.get("data")["api_token"]
			frappe.db.set_value("Rihvit Settings", "Rihvit Settings", "api_token", api_token)
			frappe.db.commit()
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback() , title="API: get_rihvit_api_token")
	finally:
		return api_token


@frappe.whitelist()
def create_rihvit_invoice(invoice_id):
	"""
	Create Rihvit Invoice using order details and iCredit Settings
	:param order_id: Sales Order
	:return: Invoice Creation Status (String)
	"""
	try:
		#TODO: Use Invoice Data instead of Sales Order
		invoice = frappe.get_doc("Sales Invoice", invoice_id)
		rihvit_settings = frappe.get_doc("Rihvit Settings", "Rihvit Settings")
		customer = frappe.get_doc("Customer", invoice.get("customer"))
		# Rihvit API token - check in settings if not generate new one
		if not rihvit_settings.get("api_token"):
			get_rihvit_api_token(rihvit_settings)
		# sales order item
		items = []
		for i in invoice.get("items"):
			items.append({
				#"item_id": i.get("item_code"),
				"quantity": i.get("qty"),
				"description": i.get("item_code") + ":" + i.get("item_name"),
				"bruto_price_nis": i.get("price_list_rate"), #before discount
				"price_nis": i.get("rate"), #after discount
				"currency_id": 1,
				"exempt_vat": False
			})

		# Rihvit Sales Invoice API
		url = "https://api.rivhit.co.il/online/RivhitOnlineAPI.svc/Document.New"
		headers = {"Content-Type": "application/json"}
		data = {
			"api_token": rihvit_settings.get("api_token"),
			"document_type": 1,
			"customer_id": 0,
			"last_name": customer.get("customer_name"),
			"first_name": customer.get("customer_name"),
			"price_include_vat": False,
			"currency_id":1,
			"items": items,
			"comments": invoice.name
		}
		response = request("POST", url, data=json.dumps(data), headers=headers)
		if response.status_code == 200:
			invoice.rihvit_invoice = response.text
			invoice.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.log_error(message= "Rihvit Invoice Success", title="API: Rihvit API Success")
			return "Success"
		else:
			error_log = json.dumps({invoice_id: response.text})
			frappe.log_error(message= error_log, title="API: create_rihvit_invoice")
			return "Failure"
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: create_rihvit_invoice")
		return "Failure"

@frappe.whitelist()
def get_payment_url(quote_id):
	"""This method will pass quote data (customer details, item data)
	to the GetUrl API (iCredit) and get payment url

	:param quote_id: Quotation No.
	:return: payment url(iCredit) (String)"""
	try:
		quote = frappe.get_doc("Quotation", quote_id)
		icredit_settings = frappe.get_doc("iCredit Settings", "iCredit Settings")
		customer = frappe.get_doc("Customer", quote.get("party_name"))
		address_doc = frappe.db.get_value("Dynamic Link", {
			"link_doctype": "Customer",
			"link_name": quote.get("party_name")
		}, "parent")

		full_address = ""
		address = {}
		if address_doc:
			address = frappe.get_doc("Address", address_doc)
			full_address = address.get("address_line1") +" "+ address.get("address_line2")

		# quote item
		items = []
		for i in quote.get("items"):
			items.append({
				"CatalogNumber": i.get("item_code"),
				"Quantity": i.get("qty"),
				#UnitPrice with 17% VAT
				"UnitPrice": i.get("rate") + i.get("rate") * 0.17,
				"Description": i.get("item_code") + ":" + i.get("item_name")
			})

		# GetUrl API

		# Added user-agent to headers to avoid max redires exceed error
		# Ref - https://stackoverflow.com/questions/43421026/how-to-deal-with-toomanyredirects-exceeded-30-redirects-exception-using-requ
		headers = {"Content-Type": "application/json", "user-agent": "Playfunction App"}
		url = icredit_settings.get("geturl_api")
		data = {
			"GroupPrivateToken": icredit_settings.get("group_private_token"),
			"RedirectURL" : icredit_settings.get("redirect_url") + "&quote_id={}".format(quote_id),
			"FailRedirectURL": icredit_settings.get("fail_redirect_url"),
			"IPNURL": icredit_settings.get("ipnurl"),
			"CustomerLastName": customer.get("customer_name"),
			"CustomerFirstName": customer.get("customer_name"),
			"Address": full_address,
			"City": address.get("city"),
			"EmailAddress": address.get("email_id"),
			"NumberOfPayments": 1,
			"Currency": 1,
			"SaleType": 1,
			"HideItemList": True,
			"Items": items,
			"Custom1" : quote_id,
			# "Custom2" : "456",
		}

		response = request("POST", url, data=json.dumps(data), headers=headers)
		if response.status_code == 200:
			doc = frappe.get_doc("Quotation", quote_id)
			doc.sales_tokens = response.text
			doc.save()
			frappe.db.commit()
			res = json.loads(response.text)
			return res["URL"]
		else:
			frappe.log_error(message=response.text , title="Payment API: get_payment_url")
			return ""
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback() , title="Payment API: get_payment_url")
		return ""
