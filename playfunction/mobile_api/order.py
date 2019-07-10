from __future__ import unicode_literals
import frappe, os, json
from frappe.permissions import reset_perms
from frappe import _


@frappe.whitelist()
def get_order_list():
	"""Returns Submitted Order List"""
	try:
		response = frappe._dict()
		fields=["name", "customer", "transaction_date", "total", \
			"billing_status", "status","delivery_status"]

		order_list = frappe.get_all('Sales Order',filters={"docstatus":1},fields=fields)
		response.update({"data":order_list, "status_code":200})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch order list"
	finally:
		return response