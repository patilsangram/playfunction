import frappe
from frappe import _
from frappe.utils import formatdate

@frappe.whitelist()
def update_amount_owed(doc, method):
	"""update amount owed on supplier form"""
	supplier = ""
	if doc.doctype == "Purchase Invoice":
		supplier = doc.supplier
	elif doc.doctype == "Payment Entry" and doc.party_type=='Supplier':
		supplier = doc.party

	if supplier:
		supplier_doc = frappe.get_doc("Supplier", supplier)
		invoices = frappe.get_all("Purchase Invoice", {
			"docstatus": 1, "outstanding_amount": [">", 0], "supplier": supplier
			}, ["name", "creation", "outstanding_amount"])

		supplier_doc.amount_owed = []
		for inv in invoices:
			supplier_doc.append("amount_owed", {
				"invoice_no": inv.get("name"),
				"amount_owed": inv.get("outstanding_amount"),
				"date_owed": formatdate(inv.get("creation"))
			})
		supplier_doc.save()
		frappe.db.commit()

