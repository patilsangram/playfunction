import frappe, json, erpnext


@frappe.whitelist()
def get_item_groups():
	fields = ["name", "parent_item_group", "is_group", "image"]
	item_groups = frappe.db.get_all("Item Group", fields)
	return item_groups

@frappe.whitelist()
def get_items_and_categories(item_group):
	# return item categories/Sub categories along with item list
	# TODO: 1. send category -> {"category": ["sub cat 1", "sub cat 2"]}
	# 2. accept filters dictionary create dynamic conditions
	item_group = frappe.get_all("Item Group")
	item_category = frappe.get_all("Item Category")
	fields = ["name", "item_name", "image", "stock_balance", "price"]
	items = frappe.db.sql("select name, item_name, image from `tabItem`", as_dict=True)
	data = {"item_group": item_group, "category": item_category, "items": items}
	return data


@frappe.whitelist()
def get_item_details(item_code):
	# TODO: item selling price as per login customer
	company = erpnext.get_default_company() or frappe.db.get_all("Company")[0].get("name")
	item_details = frappe.db.sql("""
		select
			i.item_code, i.item_name, i.image, group_concat(concat(c.category,'/',c.subcategory))
			as category, ifnull(b.actual_qty, 0) as qty, d.default_warehouse
		from
			tabItem i left join `tabCategory List` c  on c.parent = i.name
		left join
			`tabItem Default` d on d.parent = i.name and d.company = '{}'
		left join
			`tabBin` b on b.item_code = i.item_code and d.default_warehouse = b.warehouse
		where
			i.name = '{}'
		group by i.name
	""".format(company, item_code), as_dict=True)
	return item_details