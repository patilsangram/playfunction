import frappe, json


@frappe.whitelist()
def get_item_groups():
	fields = ["name", "parent_item_group", "is_group", "image"]
	item_groups = frappe.db.get_all("Item Group", fields)
	return item_groups

@frappe.whitelist()
def get_items_and_categories(item_group):
	# return item categories/Sub categories along with item list
	# return items of given item group
	fields = ["name", "item_name", "image", "stock_balance", "price"]
	items = []
	# items = frappe.db.sql()
	return items

