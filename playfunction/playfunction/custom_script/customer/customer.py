import frappe
from frappe import _




@frappe.whitelist()
def validate_customer(doc, method):
	"""validate: same user is linked with multilple customers"""
	if doc.user:
		customer_exist = frappe.db.get_value("Customer", {
			"user": doc.user,
			"name": ("!=", doc.name)
		})
		if customer_exist:
			frappe.throw(_("User <b>{}</b> is already linked with Customer <b>{}</b>".format(doc.user, customer_exist)))