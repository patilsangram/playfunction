import frappe, json


@frappe.whitelist()
def get_item_groups():
	fields = ["name", "parent_item_group", "is_group", "image"]
	item_groups = frappe.db.get_all("Item Group", fields)
	return item_groups

@frappe.whitelist()
def get_items():
	return "success"