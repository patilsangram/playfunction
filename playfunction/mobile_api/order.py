from __future__ import unicode_literals
import frappe, os, json
from frappe.permissions import reset_perms
from frappe import _


@frappe.whitelist()
def get_order_list():
	"""
	Returns Order List 
	"""
	try:
		response = frappe._dict()
		fields = ["name", "customer", "transaction_date", "total", \
			"billing_status", "status","delivery_status"]
		order_list = frappe.get_all('Sales Order',fields = fields)
		response.update({"data":order_list, "status_code":200})
		frappe.local.response["http_status_code"] = 200
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch order list : {}".format(str(e))
		frappe.log_error(message = frappe.get_traceback() , title = "Mobile API: get_order_list")
	finally:
		return response 

@frappe.whitelist()
def get_order(order):
	"""
	Returns Sales order details with Item
	"""
	try:
		response = frappe._dict()
		if order:
			order_details = frappe.db.sql("""SELECT so.name,so.customer,so.transaction_date,so.total,so.status,
									so.billing_status,so.delivery_status,si.item_code,si.description,
									si.rate,si.qty,si.amount,si.discount_percentage,si.discount_amount FROM `tabSales Order` so
									LEFT JOIN `tabSales Order Item` si ON so.name = si.parent 
									WHERE  so.name = '{0}' AND si.parent='{0}' """.format(order),as_dict=1)
			if order_details:
				response.update({"data":order_details, "status_code":200})
				frappe.local.response["http_status_code"] = 200
			else:
				response["message"] = "Sales Order Not Found"
				frappe.local.response["http_status_code"] = 404

	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable to fetch order: {}".format(str(e))
		frappe.local.response['http_status_code'] = http_status_code
		frappe.log_error(message = frappe.get_traceback() , title = "Mobile API: get_order")
	finally:
		return response

@frappe.whitelist()
def reorder(order):
	"""
		Create copy of order 
	"""
	try:
		response = frappe._dict()
		if frappe.db.exists("Sales Order", order):
			order_doc = frappe.get_doc("Sales Order",order)
			reorder_doc = frappe.copy_doc(order_doc)
			reorder_doc.save()
			response["message"] = "Sales Order Created: {0}".format(reorder_doc.name)
			frappe.local.response["http_status_code"] = 200
		else:
			response["message"] = "Sales Order Not Found"
			frappe.local.response["http_status_code"] = 404	
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to Create Order"
		frappe.log_error(message = frappe.get_traceback() , title = "Mobile API: reorder")
	finally:
		return response