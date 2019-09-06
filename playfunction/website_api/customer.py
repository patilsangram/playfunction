import frappe
import json


@frappe.whitelist()
def get_customer_profile(customer=None):
	# return customer billing address as profile
	try:
		response = frappe._dict()
		if not customer:
			customer = frappe.db.get_value("Customer", {"user": frappe.session.user}, "name")
		if customer:
			customer_address = frappe.db.sql("""select
				ad.name, ad.address_line1, ad.address_line2,
				ad.phone, ad.email_id, ad.city
			from
				`tabAddress` ad, `tabDynamic Link` dl
			where
				dl.parent = ad.name and
				dl.parenttype = 'Address' and
				dl.link_doctype = 'Customer' and
				dl.link_name = '{}' and
				ad.address_type = 'Billing' and
				ifnull(ad.disabled, 0) = 0
			""".format(customer), as_dict=True)

			if not customer_address or not len(customer_address):
				response["message"] = "Profile Not found"
				frappe.local.response["http_status_code"] = 404
			else:
				customer_address = customer_address[0]
				customer_address.update({
					"house_no": "",
					"apartment_no":"",
					"street_address": ""
				})
				address_line1 = customer_address.pop("address_line1").split(",")
				customer_address["house_no"] = address_line1[0].strip()
				if customer_address.get("address_line2"):
					street_address = customer_address.pop("address_line2")
					customer_address["street_address"] = street_address.strip()
				if len(address_line1) > 1:
					customer_address["apartment_no"] = address_line1[1].strip()
				customer_address["customer_name"] = frappe.db.get_value("Customer", customer, "customer_name")
				response["data"] = customer_address
		else:
			response["message"] = "Customer doesn't exist"
			frappe.local.response["http_status_code"] = 422
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch Customer Address"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: get_customer_profile")
	finally:
		return response


@frappe.whitelist()
def update_customer_profile(data, customer=None):
	"""
		create customer billing address
		data: {
			:customer_name
			:phone
			:email_id
			:house_no
			:apartment_no
			:street_address
			:city
		}
	"""
	try:
		response = frappe._dict()
		if not customer:
			customer = frappe.db.get_value("Customer",{"user": frappe.session.user},"name")
		if not customer:
			response["message"] = "Customer doesn't exists."
			frappe.local.response["http_status_code"] = 422
		else:
			if not isinstance(data, dict):
				data = json.loads(data)

			add_doc = {}
			add_doc["address_line1"] = data.get("house_no", "").strip() +", "+\
				data.get("apartment_no", "").strip()
			add_doc["address_line2"] = data.get("street_address", "").strip()
			add_doc["phone"] = data.get("phone", "").strip()
			add_doc["city"] = data.get("city", "")
			add_doc["email_id"] = data.get("email_id").strip()


			existing_address = get_customer_profile(customer)
			if not existing_address.get("data"):
				if not data:
					return False

				address = frappe.new_doc("Address")
				address.update(add_doc)
				address.append("links", {
					"link_doctype": "Customer",
					"link_name": customer,
					"link_title": customer
				})
				address.flags.ignore_mandatory = True
				address.save()
			else:
				address_doc = frappe.get_doc("Address", existing_address.get("data").get("name"))
				address_doc.update(add_doc)
				address_doc.flags.ignore_mandatory = True
				address_doc.save()
			if data.get("customer_name"):
				frappe.db.set_value("Customer", customer, "customer_name", data.get("customer_name"))
			frappe.db.commit()
			response["message"] = "Profile Created Successfully."
		response = get_customer_profile(customer)
	except Exception as e:
		frappe.local.response["http_status_code"] = getattr(e, "http_status_code", 500)
		response["message"] = "Address Creation failed"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: update_customer_profile")
	finally:
		return response