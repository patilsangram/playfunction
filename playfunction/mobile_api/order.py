from __future__ import unicode_literals
import frappe, os, json
from frappe.permissions import reset_perms
from frappe import _


@frappe.whitelist()
def get_order_list(sales_order = None,order_status =None,billing_status=None,delivery_status=None):
	"""
	 Returns Order List with search and filter

	"""
	try:
		response = frappe._dict()
		filter_dict = {}
		fields=["name", "customer", "transaction_date", "total", "billing_status", "status","delivery_status"]
		if sales_order:
			temp = {"name": sales_order}
			filter_dict.update(temp)
		elif order_status:
			temp = {"status": order_status}
			filter_dict.update(temp)
		elif billing_status:
			temp = {"billing_status": billing_status}
			filter_dict.update(temp)
		elif delivery_status:
			temp = {"delivery_status": delivery_status}
			filter_dict.update(temp)

		if filter_dict:
			order_list = frappe.get_all('Sales Order',filters= filter_dict,fields=fields)
			response.update({"data":order_list, "status_code":200})
		else:
			order_list = frappe.get_all('Sales Order',fields=fields)
			response.update({"data":order_list, "status_code":200})
	
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable fetch order list : {}".format(str(e))
	finally:
		return response
