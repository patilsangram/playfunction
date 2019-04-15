import frappe, json


@frappe.whitelist()
def checkout_order(data,doc_type):
	try:
		data = json.loads(data)
		cart_items = data.get("items")
		if cart_items:
			items = []
			doc = frappe.new_doc(doc_type)
			doc.selling_price_list = "Standard Selling"
			doc.customer = frappe.get_value("Customer", {}, "name")
			#doc.company = erpnext.get_default_company() or frappe.db.get_all("Company")[0].get("name")

			for k, v in cart_items.items():
				row = {"item_code": k, "qty": v[0]}
				doc.append("items",row)
			doc.save()
			return doc.name
		else:
			frappe.msgprint("Please add items to cart first")
			return
	except Exception as e:
		frappe.msgprint("Something went wrong ..")
		return
