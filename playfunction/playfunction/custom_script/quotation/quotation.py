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
def update_selling_data(doc,meathod):
	"""
		update cost_price & discount_percentage & calculate selling_price i.e. Rate
		formula: rate = cost_price * selling_rate
	"""
	cust_discount_per = 0
	if doc.customer:
		cust_discount_per = frappe.db.get_value("Customer", doc.customer, "discount_percentage")
	for row in doc.items:
		fields = ["last_purchase_rate as cost_price","discount_percentage"]
		item_data = frappe.get_value("Item", row.item_code, fields, as_dict=True)
		if not row.cost_price and item_data.get("cost_price"):
			row.cost_price = item_data.get("cost_price")
		if not row.discount_percentage and (cust_discount_per or item_data.get("discount_percentage")):
			row.discount_percentage = cust_discount_per or item_data.get("discount_percentage")
		if row.cost_price and row.selling_rate:
			row.rate = row.cost_price * row.selling_rate

@frappe.whitelist()
def show_list(self):
	if frappe.session.user!='Administrator' and "Playfunction Customer" in frappe.get_roles(frappe.session.user):
		return """ owner = '{user}' """.format(user=frappe.session.user)