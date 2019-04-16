import frappe, json
from frappe.utils import today

@frappe.whitelist()
def checkout_order(data,doc_type):
	frappe.msgprint(today())
	try:
		data = json.loads(data)
		cart_items = data.get("items")
		if cart_items:
			items = []
			doc = frappe.new_doc(doc_type)
			doc.selling_price_list = "Standard Selling"
			doc.customer = frappe.get_value("Customer", {}, "name")
			doc.company = frappe.get_value("Company",{},"name")
			if doc_type == "Sales Order":
				doc.delivery_date = today()
			for k, v in cart_items.items():
				row = {"item_code": k, "qty": v[0]}
				doc.append("items",row)
			doc.flags.ignore_permissions = True
			doc.set_missing_values()
			doc.insert()
			doc.save()
			return doc.name
		else:
			frappe.msgprint("Please add items to cart first")
			return
	except Exception as e:
		frappe.msgprint("Something went wrong ..")
		return