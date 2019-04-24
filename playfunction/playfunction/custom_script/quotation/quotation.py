import frappe, json
from frappe.utils import today, flt

@frappe.whitelist()
def checkout_order(data,doctype):
	try:
		data = json.loads(data)
		cart_items = data.get("items")
		if cart_items:
			doc = frappe.new_doc(doctype)
			doc.selling_price_list = "Standard Selling"
			doc.customer = frappe.get_value("Customer", {}, "name")
			customer_name = frappe.db.get_value("User",frappe.session.user,"full_name")
			if not frappe.db.exists('Customer',customer_name):
				customer_name=add_customer(customer_name)
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
			doc.save(ignore_permissions=True)
			return doc.name
		else:
			frappe.msgprint("Please add items to cart first")
			return
	except Exception as e:
		frappe.msgprint("Something went wrong ..")
		return


def add_customer(customer_name):
	doc = frappe.get_doc({
	"doctype": "Customer",
	"customer_name" : customer_name,
	"email_id" : frappe.session.email,
	"mobile_no" : frappe.session.mobile_no
	})
	doc.insert()
	doc.submit()
	return customer_name