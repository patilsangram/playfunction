import frappe


@frappe.whitelist()
def get_customer_address(customer=None):
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
				response["message"] = "Address Not found"
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
				response["data"] = customer_address
		else:
			response["message"] = "Customer doesn't exist"
			frappe.local.response["http_status_code"] = 422
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch Customer Address"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: get_customer_address")
	finally:
		return response


@frappe.whitelist()
def make_customer_address(customer, data):
	try:
		response = frappe._dict()
		existing_address = get_customer_address(customer)
		if not existing_address.get("data"):
			add_doc = {}
			if not data:
				return False
			if not isinstance(data, dict):
				data = json.loads()
			add_doc["address_line1"] = data.get("house_no", "").strip() +", "+\
				data.get("apartment_no", "").strip()
			add_doc["address_line2"] = data.get("street_address", "").strip()
			add_doc["phone"] = data.get("phone", "").strip()
			add_doc["city"] = data.get("city", "")
			add_doc["email_id"] = data.get("email_id").strip()
			address = frappe.new_doc("Address")
			address.update(add_doc)
			address.append("links", {
				"link_doctype": "Customer",
				"link_name": customer,
				"link_title": customer
			})
			address.flags.ignore_mandatory = True
			address.save()
			response["message"] = "Address Created Successfully."
		response["address"] = get_customer_address(customer)
	except Exception as e:
		frappe.local.response["http_status_code"] = getattr(e, "http_status_code", 500)
		response["message"] = "Address Creation failed"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: make_customer_address")
	finally:
		return response