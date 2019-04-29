import frappe, json
from frappe.utils import today, flt

@frappe.whitelist()
def checkout_order(data,doctype):
	try:
		data = json.loads(data)
		cart_items = data.get("items")
		customer = frappe.get_value("Customer", {"user": frappe.session.user}, "name")
		if cart_items:
			doc = frappe.new_doc(doctype)
			doc.selling_price_list = "Standard Selling"
			doc.customer = customer
			doc.company = frappe.get_value("Company",{},"name")
			if doctype == "Sales Order":
				doc.delivery_date = today()
			for k, v in cart_items.items():
				discount = frappe.get_value("Item",{'item_code':k},"discount_percentage")
				row = {"item_code": k, "qty": v[0], "price_list_rate": v[1], "discount_percentage": v[2]}
				# discount_percentage
				if v[2] and v[1] > 0:
					row.update({"discount_amount": flt(v[1]) * flt(v[2]) / 100})
				doc.append("items",row)
			doc.set_missing_values()
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)
			return doc.name
		else:
			frappe.msgprint("Please add items to cart first")
			return
	except Exception as e:
		frappe.msgprint("Something went wrong ..")
		return


@frappe.whitelist()
def validate_quotation(doc,meathod):
	for k in doc.items:
 		get_data = frappe.get_value("Item", {"item_code": k.item_code}, ["last_purchase_rate","discount_percentage"])
	 	if not k.cost_price:
		 	k.cost_price = get_data[0]	
		if k.cost_price and k.selling_rate:
			k.selling_price = k.cost_price * k.selling_rate
		if not k.discount_percentage:
			k.discount_percentage=get_data[1]
