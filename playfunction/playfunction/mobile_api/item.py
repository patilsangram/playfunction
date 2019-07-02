from __future__ import unicode_literals
import frappe, os, json
from frappe.permissions import reset_perms
from frappe import _


@frappe.whitelist()
def get_item_details(data):
	try:
		item_list=frappe.db.sql("""SELECT  i.item_code,i.item_name,i.in_stock,i.image,i.discount_percentage,ip.price_list_rate,
			((ip.price_list_rate*i.discount_percentage)/ 100 ) 
			as amount_after_discount FROM `tabItem` i LEFT JOIN `tabItem Price` ip on i.item_code =ip.item_code""",as_dict=1)

		return item_list
	except Exception as e:
		make_error_log(title="Failed api of Get Item Details",method="get_item_details",
					status=404,
					data = "No data",
					message=e,
					traceback=frappe.get_traceback(),exception=True)
		raise e




@frappe.whitelist()
def get_customer(data):
	try:
	 	cust_list=frappe.db.sql("""SELECT c.email_id, c.customer_name,a.name,a.address_line1,
	 		a.address_line2,a.city,a.pincode FROM `tabDynamic Link` d,`tabAddress` a,`tabCustomer` c
	 		 WHERE  d.link_doctype = "Customer" AND a.name = d.parent AND d.link_name=c.name""",as_dict=1)
	 	return cust_list
	except Exception as e:		
		make_error_log(title="Failed api of get customer list",method="get_customer",
					status=404,
					data = "No data",
					message=e,
					traceback=frappe.get_traceback(),exception=True)
		raise e