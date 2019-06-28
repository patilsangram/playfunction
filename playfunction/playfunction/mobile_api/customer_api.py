from __future__ import unicode_literals
import frappe, os, json
from frappe.permissions import reset_perms
from frappe import _



@frappe.whitelist()
def create_customer(data):
	""":param data = {
		:customer_name
		:customer_type
		:email_id
	}"""
	try:
		api_data= json.loads(data)
		if not frappe.db.exists('Customer',api_data.get('customer_name')):

			customer_doc = frappe.new_doc("Customer")
			if customer_doc:
				customer_doc.customer_name = api_data.get('customer_name')
				customer_doc.customer_type = api_data.get('customer_type')
				customer_doc.customer_group = api_data.get('customer_group')
				customer_doc.email_id = api_data.get('email_id')
				customer_doc.territory = api_data.get('territory')
				customer_doc.save(ignore_permissions=1)
				if api_data.get('address'):
					address_dict = api_data.get('address')
					address = frappe.get_doc({
						'doctype': 'Address',
						'address_title': address_dict.get('address_title'),
						'address_type': address_dict.get('address_type'),
						'address_line1': address_dict.get('address_line1'),
						'address_line2': address_dict.get('address_line2'),
						'city': address_dict.get('city'),
						'pincode': address_dict.get('pincode'),
						'state': address_dict.get('state'),
						'country': address_dict.get('country'),
						'links': [{
							'link_doctype': "Customer",
							'link_name': customer_doc.name
						}]
					}).insert(ignore_permissions=True)
			return "Customer is created".format(customer_doc.name)
		else:
			return "Customer is already exist"		
	except Exception as e:
		make_error_log(title="Failed api of create customer",method="create_customer",
					status="Error",
					data = "No data",
					message=e,
					traceback=frappe.get_traceback(),exception=True)
		raise e

@frappe.whitelist()
def update_customer(data):
	try:
		api_data= json.loads(data)
		if frappe.db.exists('Customer',api_data.get('customer_name')):
			customer_doc = frappe.get_doc("Customer" , api_data.get('customer_name'))
			customer_doc.customer_name = api_data.get('customer_name')
			customer_doc.customer_type = api_data.get('customer_type')
			customer_doc.customer_group = api_data.get('customer_group')
			customer_doc.territory = api_data.get('territory')
			customer_doc.flags.ignore_permissions = True			
			customer_doc.save()
			return "Customer is updated"
		else:
			return "Customer does not exist"

	except Exception as e:
		raise e
	


@frappe.whitelist()
def get_customer(data):
	try:

		cust_list= frappe.db.sql("""select name, customer_group, territory from `tabCustomer` where docstatus < 2 """,as_dict=1)
		return cust_list
	except Exception as e:		
		make_error_log(title="Failed api of get customer list",method="get_customer",
					status="Error",
					data = "No data",
					message=e,
					traceback=frappe.get_traceback(),exception=True)
		raise e





@frappe.whitelist()
def get_customer_searchlist(customer=None):	
	try:
		if customer:
			cust=frappe.db.sql("""select customer_name from `tabCustomer` where name like "%ad%"; """,as_dict=1)
			return cust
		
		else:
			return 	get_customer()
	except Exception as e:
		
		raise e





@frappe.whitelist()
def delete_customer(customer_name):
	try:
		if not frappe.db.exists("Customer", customer_name):
			return frappe.msgprint("Customer does not exists")
		else:
			customer_doc = frappe.delete_doc("Customer", customer_name)
			frappe.db.commit()
			return "Customer is deleted"
	except Exception as e:
		make_error_log(title="Failed api of delete customer",method="delete_customer",
					status="Error",
					data = "No data",
					message=e,
					traceback=frappe.get_traceback(),exception=True)
		raise e