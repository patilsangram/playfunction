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
		else:
			if frappe.db.exists("Customer", data.get("customer_name")):
				response["status_code"] = 500
				response["message"] = "Customer already exists."
			else:
				customer = frappe.new_doc("Customer")
				customer.update(data)
				customer.save()
				frappe.db.commit()
				response = get_customer_details(customer.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Customer creation failed: {}".format(str(e))
	finally:
		return response


@frappe.whitelist()
def get_customer_list(search=None):
	try:
		response = frappe._dict()

		if frappe.has_permission("Customer", "read"):
			data = frappe.db.sql("""
				select name, customer_name, email_id, customer_type
				from tabCustomer
			""", as_dict=True)
			response.update({"status_code": 200, "data": data})
		else:
			response.update({"status_code": 403, "message": "Insufficient Permission"})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable to fetch customer: {}".format(str(e))
	finally:
		return response

@frappe.whitelist()
def update_customer(customer, data):
	try:
		pass
	except Exception as e:
		raise e
	finally:
		pass

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
				response.update({"status_code": 404, "message": "Customer not found"})
		else:
			response.update({"status_code": 403, "message": "Insufficient Permission"})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable to delete customer: {}".format(str(e))
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
			response["status_code"] = 200
			filters = [
				["Dynamic Link", "link_doctype", "=", "Customer"],
				["Dynamic Link", "link_name", "=", customer],
				["Dynamic Link", "parenttype", "=", "Address"],
			]

			fields = ["address_title", "address_line1", "address_line2", "city", "country", "pincode"]
			address_list = frappe.get_all("Address", filters=filters, fields=fields)
			if len(address_list):
				response.update(address_list[0])
		else:
			response["status_code"] = 404
			response["message"] = "Customer not found"
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable to fetch customer Details"
	finally:
		return response