from __future__ import unicode_literals
import frappe, os, json
from frappe.permissions import reset_perms
from frappe import _

@frappe.whitelist()
def get_order_history(data):
	try:
		response = frappe._dict()
		fields = ["name", "customer", "transaction_date", "total", "billing_status", "status",
			"delivery_status"]
		order_details=frappe.get_all('Sales Order',fields )
		return response.update({"Order history":order_details})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable fetch order history: {}".format(str(e))
	finally:
		return response
		
		


@frappe.whitelist()
def get_order_history_item(sales_order):
	try:
		if sales_order:
			name =str(sales_order)
			if frappe.db.exists("Sales Order",name):
				response = frappe._dict()
				order_item_details = frappe.get_all('Sales Order Item',
					filters={
						'parent': name,
						},
						fields=["item_code", "item_name",'qty','discount_percentage','rate','amount']
					)
				return response.update({"Order Item":order_item_details})
			return response.update({"message":"Sales Order doesnot exists","status_code": 200})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable fetch order item history: {}".format(str(e))
	finally:
		return response
				
		
				
	