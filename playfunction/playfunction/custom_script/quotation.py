import frappe, json, erpnext


@frappe.whitelist()
def checkout(data):
	try:
		data = json.loads(data)
		cart_items = data.get("items")
		if cart_items:
			items = []
			doc = frappe.new_doc("Quotation")
			doc.selling_price_list = "Standard Selling"
			doc.customer = frappe.get_value("Customer", {}, "name")
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
