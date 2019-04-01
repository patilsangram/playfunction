import frappe, json


@frappe.whitelist()
def get_item_groups():
	fields = ["name", "parent_item_group", "is_group", "image"]
	item_groups = frappe.db.get_all("Item Group", fields)
	return item_groups

@frappe.whitelist()
def get_items_and_categories(item_group):
	# return item categories/Sub categories along with item list
	item_group = frappe.get_all("Item Group")
	item_category = frappe.get_all("Item Category")
	fields = ["name", "item_name", "image", "stock_balance", "price"]
	items = frappe.db.sql("select name, item_name, image from `tabItem`", as_dict=True)
	return {"item_group": item_group, "category": item_category, "items": items}

