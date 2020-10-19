import frappe, json
from frappe.utils import today, flt

def submit(doc, method):
	receipient = frappe.get_doc("Notification","Quotation")
	cc = []
	print_doc = frappe.get_print('Quotation', doc.name, doc = None, print_format = receipient.print_format,as_pdf=1)
	print_att = [{'fname':doc.name +".pdf",'fcontent':print_doc}]
	for i in receipient.recipients:
		cc.append(i.cc)
	frappe.sendmail(
                    recipients = frappe.db.get_value("Customer",{"name":doc.party_name},"user"),
                    cc = cc,
                    subject = receipient.subject,
                    message = frappe.render_template(receipient.message,{"doc":doc}),
                    attachments= print_att
                    )

@frappe.whitelist()
def checkout_order(data,doctype):
	try:
		data = json.loads(data)
		cart_items = data.get("items")
		customer = frappe.get_value("Customer", {"user": frappe.session.user}, "name")
		if cart_items:
			doc = frappe.new_doc(doctype)
			doc.selling_price_list = "Standard Selling"
			doc.company = frappe.get_value("Company",{},"name")
			if doctype == "Sales Order":
				doc.customer = customer
				doc.delivery_date = today()
			else:
				doc.party_name = customer
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
			return False
	except Exception as e:
		frappe.msgprint("Something went wrong ..")
		return False


@frappe.whitelist()
def update_selling_data(doc,meathod):
	"""
		update cost_price & discount_percentage & calculate selling_price i.e. Rate
		formula: rate = cost_price * selling_rate
	"""
	cust_discount_per = 0
	if doc.party_name:
		cust_discount_per = frappe.db.get_value("Customer", doc.party_name, "discount_percentage")
	for row in doc.items:
		fields = ["last_purchase_rate", "cost_price","discount_percentage"]
		item_data = frappe.get_value("Item", row.item_code, fields, as_dict=True)
		if not row.cost_price and (item_data.get("cost_price") or item_data.get("last_purchase_rate")):
			row.cost_price = item_data.get("cost_price") or item_data.get("last_purchase_rate")
		if not row.discount_percentage and (cust_discount_per or item_data.get("discount_percentage")):
			row.discount_percentage = cust_discount_per or item_data.get("discount_percentage")
			row.rate=row.cost_price-((row.discount_percentage/100)*row.cost_price)
		if row.cost_price and row.selling_rate:
			row.rate = row.cost_price * row.selling_rate

def get_permission_query_conditions_quotation(user):
	return get_permission_query_conditions(user, "Quotation")

def get_permission_query_conditions_sales_order(user):
	return get_permission_query_conditions(user, "Sales Order")

def get_permission_query_conditions_sales_invoice(user):
	return get_permission_query_conditions(user, "Sales Invoice")

@frappe.whitelist()
def get_permission_query_conditions(user, doctype):
	# playfunction customer can access only his own records
	if not user:
		user = frappe.session.user
	customer_field = {"Quotation": "party_name", "Sales Order": "customer", "Sales Invoice": "customer"}
	if user != "Administrator" and "Playfunction Customer" in frappe.get_roles():
		customer = frappe.db.get_value("Customer", {"user": user})
		return """ {} = '{}' """.format(customer_field.get(doctype), customer) if customer else "1=2"
