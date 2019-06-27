from __future__ import unicode_literals
import frappe, os, json
from frappe.permissions import reset_perms


#CREATE CUSTOMER API
@frappe.whitelist(allow_guest=True)
def create_customer(customer_name, customer_type=None,email_id=None,city=None, customer_group=None, territory=None, address_line1=None,address_line2=None,state=None,country=None,pincode=None):
	if frappe.db.exists("Customer", customer_name):
		return frappe.msgprint("Customer already exists")
	else:
		customer_doc = frappe.new_doc("Customer")
		customer_doc.customer_name = customer_name
		customer_doc.customer_type = customer_type
		customer_doc.customer_group = customer_group
		customer_doc.email_id = email_id
		customer_doc.territory = territory
		customer_doc.address_line1 = address_line1
		customer_doc.address_line2 = address_line2
		customer_doc.city = city
		customer_doc.state = state
		customer_doc.country = country
		customer_doc.pincode = pincode
		customer_doc.flags.ignore_permissions = True
		customer_doc.save()
		frappe.db.commit()
		return "customer is created"

#UPDATE CUSTOMER API
@frappe.whitelist(allow_guest=True)
def update_customer(customer_name, customer_type=None,email_id=None,city=None, customer_group=None, territory=None, address_line1=None,address_line2=None,state=None,country=None,pincode=None):
	customer_doc = frappe.get_doc("Customer" , customer_name)
	customer_doc.customer_name = customer_name
	customer_doc.customer_type = customer_type
	customer_doc.customer_group = customer_group
	customer_doc.email_id = email_id
	customer_doc.territory = territory
	customer_doc.address_line1 = address_line1
	customer_doc.address_line2 = address_line2
	customer_doc.city = city
	customer_doc.state = state
	customer_doc.country = country
	customer_doc.pincode = pincode
	customer_doc.flags.ignore_permissions = True			
	customer_doc.save()
	frappe.db.commit()
	return "Customer is updated"


#READ API
@frappe.whitelist(allow_guest=True)
def get_customer():
	cust_list = frappe.db.sql("""select customer_name,customer_type,customer_group,territory,email_id,city,address_line1 from tabCustomer """,as_dict=1)
	return cust_list


#SEACH CUSTOMER and CUSTOMER LIST API
@frappe.whitelist(allow_guest=True)
def get_customer_list(customer=None,):	
	if customer:
		cl=frappe.db.sql("""select * from `tabCustomer` where customer_name="admin" """,as_dict=1)
		return cl
	
	else:
		return 	get_customer()




#DELETE CUSTOMER API
@frappe.whitelist(allow_guest=True)
def delete_customer(customer_name):
	customer_doc = frappe.delete_doc("Customer", customer_name)
	frappe.db.commit()
	return "Customer is deleted"