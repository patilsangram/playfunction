import frappe
from frappe import _

@frappe.whitelist()
def amount_owed_log(doc, method):
	if doc.doctype=="Purchase Invoice" and doc.outstanding_amount > 0:
			new_doc=frappe.get_doc("Supplier",doc.supplier)
			new_doc.append("amount_owed", {
				"invoice_no": doc.name,
				"amount_owed": doc.outstanding_amount,
				"date_owed": doc.due_date
			})
			new_doc.save()
			frappe.db.commit()
	if doc.doctype="Payment Entry" and doc.party_type=='Supplier': 
		for row in doc.references:
			if row.reference_doctype =='Purchase Invoice' and row.outstanding_amount > 0::
				if frappe.db.exists("Amount Owed", {"name":row.reference_name}):
					frappe.delete_doc("Amount Owed", row.reference_name)
					frappe.db.commit()
				new_doc=frappe.get_doc("Supplier",doc.party)
				new_doc.append("amount_owed", {
						"invoice_no": row.reference_name,
						"amount_owed": row.outstanding_amount,
						"date_owed": row.due_date
					})
				new_doc.save()
				frappe.db.commit()

