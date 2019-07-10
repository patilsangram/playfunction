import json
import frappe
from frappe import _


@frappe.whitelist()
def create_customer(data):
	"""
	:param data: {
		customer_name:
		email_id:
		address_title:
		address_line1:
		address_line2:
		country:
		city:
		pincode:
	}
	"""
	try:
		response = frappe._dict()
		data = json.loads(data)
		mandatory = ["customer_name", "address_title", "address_line1", "city", "country"]
		if not all([ f in data.keys() for f in mandatory ]):
			response["status_code"] = 422
			response["message"] = _("Invalid Data")
			frappe.local.response['http_status_code'] = 422
		else:
			if frappe.db.exists("Customer", data.get("customer_name")):
				response["status_code"] = 500
				response["message"] = "Customer already exists."
				frappe.local.response['http_status_code'] = 500
			else:
				customer = frappe.new_doc("Customer")
				customer.update(data)
				customer.save()
				frappe.db.commit()
				response = get_customer_details(customer.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Customer creation failed: {}".format(str(e))
	finally:
		return response


@frappe.whitelist()
def get_customer_list(search=None):
	# return customer details list along with address details
	try:
		response = frappe._dict()
		if frappe.has_permission("Customer", "read"):
			cond = " where 1=1"
			if search:
				cond += " and c.customer_name like '{0}' \
					or c.email_id like '{0}'".format("%{}%".format(search))

			data = frappe.db.sql("""
				select distinct c.name, c.customer_name, c.email_id, c.customer_type,
				ad.address_line1, ad.address_line2, ad.city, ad.pincode,
				ad.country, ad.address_title from `tabCustomer` c
				left join `tabDynamic Link` dl on dl.link_name = c.name
				and dl.link_doctype = 'Customer' left join `tabAddress` ad
				on dl.parent = ad.name  {} group by c.name
			""".format(cond), as_dict=True)
			response.update({"status_code": 200, "data": data})
		else:
			frappe.local.response['http_status_code'] = 403
			response.update({"status_code": 403, "message": "Insufficient Permission"})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch customer: {}".format(str(e))
	finally:
		return response

@frappe.whitelist()
def update_customer(customer, data):
	"""
	:param customer: customer name/id
	:param data: {
		customer_name:
		email_id:
		address_title:
		address_line1:
		address_line2:
		country:
		city:
		pincode:
	}
	"""
	try:
		response = frappe._dict()
		data = json.loads(data)
		if not frappe.db.exists("Customer", customer):
			response["status_code"] = 404
			frappe.local.response["http_status_code"] = 404
			response["message"] = "Customer {} not found".format(customer)
		else:
			customer = frappe.get_doc("Customer", customer)
			customer_fields = {
				k:v for k,v in data.items()
				if k in ["email_id", "customer_name"]
			}
			if customer_fields.keys():
				customer.update(customer_fields)
				customer.save()
				frappe.db.commit()

			# update/create address
			address = get_customer_address(customer)
			if address and len(data.keys()):
				address_doc = frappe.get_doc("Address", address.get("name"))
				address_doc.update(data)
				address_doc.save(ignore_permissions=True)
				frappe.db.commit()
			elif len(data) and \
				all([ f in data.keys() for f in  ['address_title', 'address_line1', 'city', 'country']]):
				address = frappe.new_doc("Address")
				address.update(data)
				address.append("links", {
					"link_doctype": "Customer",
					"link_name": customer.name
				})
				address.flags.ignore_permissions = True
				address.flags.ignore_mandatory = True
				address.save()
			frappe.db.commit()
			response.update({"status_code": 200, "message": "Customer updated Successfully"})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Customer update failed: {}".format(str(e))
	finally:
		return response

@frappe.whitelist()
def delete_customer(customer=None):
	try:
		response = frappe._dict()
		if frappe.has_permission("Customer", "delete"):
			if frappe.db.exists("Customer", customer):
				frappe.delete_doc("Customer", customer)
				frappe.db.commit()
				response.update({"status_code": 200, "message": "Delete Successfully"})
			else:
				frappe.local.response['http_status_code'] = 404
				response.update({"status_code": 404, "message": "Customer not found"})
		else:
			frappe.local.response['http_status_code'] = 403
			response.update({"status_code": 403, "message": "Insufficient Permission"})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Cannot Delete, Linked with transaction records"
	finally:
		return response

@frappe.whitelist()
def get_customer_details(customer):
	"""return customer and address details"""
	try:
		response = frappe._dict()
		if frappe.db.exists("Customer", customer):
			doc = frappe.get_doc("Customer", customer)
			response["customer_name"] = doc.get("customer_name")
			response["email_id"] = doc.get("email_id")
			response["name"] = doc.get("name")
			response["status_code"] = 200
			address = get_customer_address(customer)
			if address:
				address.pop("name")
				address.pop("creation")
				response.update(address)
		else:
			response["status_code"] = 404
			response["message"] = "Customer not found"
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch customer Details: {}".format(str(e))
	finally:
		return response

@frappe.whitelist()
def get_customer_address(customer):
	"""get first created address against customer"""
	if customer:
		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", customer],
			["Dynamic Link", "parenttype", "=", "Address"],
		]

		fields = ["name", "address_title", "address_line1",
			"address_line2", "city", "country", "pincode", "creation"]

		address_list = frappe.get_all("Address", filters=filters, fields=fields, order_by="creation")
		if len(address_list):
			return address_list[0]
		else:
			return {}
	else:
		return {}