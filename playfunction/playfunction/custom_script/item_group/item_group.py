import frappe
from frappe import _

@frappe.whitelist()
def update_group_level(doc, method=None):
	if doc.parent_item_group:
		parent_level = frappe.db.get_value("Item Group", doc.parent_item_group, "group_level") or 1
		if parent_level <= 4:
			doc.group_level = parent_level + 1
		else:
			frappe.throw(_("Only 5 level tree structure are allowed"))