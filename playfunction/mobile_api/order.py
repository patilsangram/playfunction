from __future__ import unicode_literals
import frappe, os, json
from frappe.permissions import reset_perms
from frappe import _


@frappe.whitelist()
def get_order_list():
	"""
	 Returns Submitted Order List 
	"""
	try:
		response = frappe._dict()
		fields=["name", "customer", "transaction_date", "total", "billing_status", "status","delivery_status"]

		order_list = frappe.get_all('Sales Order',filters={"docstatus":1},fields=fields)
		response.update({"data":order_list, "status_code":200})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable to fetch order list : {}".format(str(e))
	finally:
		return response



@frappe.whitelist()
def get_order(sales_order):
	"""
	 Returns order details with Item
	"""
	try:
		response = frappe._dict()
		if sales_order:
			order = frappe.db.sql("""select name,customer,transaction_date, total, billing_status, status,delivery_status from `tabSales Order` where name = '{0}'""".format(sales_order),as_dict=1)
		if order:
			for row in order:
					row.update({"items": frappe.db.sql("select item_code,description,rate,qty,amount,discount_percentage,discount_amount from `tabSales Order Item` where parent = '{0}'".format(row.get('name')),as_dict=1)})
					response.update({"data":order, "status_code":200})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable to fetch order: {}".format(str(e))
	finally:
		return response