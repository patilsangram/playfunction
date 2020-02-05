import frappe
from frappe.model.naming import make_autoname, getseries

@frappe.whitelist()
def item_autoname(doc, method):
	"""

	Creates an autoname from supplier's 1st & 3rd character and auto icremented series:

	e.g.
		1. if supplier is 'Indictrans' then naming will be ID00001
		2. if supplier is 'Test Supplier' then naming will be like TS00002

		* Here, we're maintaing dummy naming series to get auto increment series.
		i.e. ItemAutoname
	"""
	if doc.supplier and len(doc.supplier) >= 3:
		supplier = doc.supplier.replace(" ", "")
		supplier_chars = supplier[0].upper() + supplier[2].upper()
		series = getseries("ItemAutoname", 5)
		doc.item_code = supplier_chars + str(series)