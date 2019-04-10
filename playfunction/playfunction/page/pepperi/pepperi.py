import frappe, json, erpnext


@frappe.whitelist()
def get_item_groups():
	fields = ["name", "parent_item_group", "is_group", "image"]
	item_groups = frappe.db.get_all("Item Group", fields)
	return item_groups

@frappe.whitelist()
def get_items_and_categories(filters):
	# return item categories/Sub categories along with item list
	# 2. accept filters dictionary create dynamic conditions
	company = erpnext.get_default_company() or frappe.db.get_all("Company")[0].get("name")
	filters = json.loads(filters)
	item_group = frappe.get_all("Item Group")
	cat_subcat = frappe.db.sql("select group_concat(name) as subcategory, category \
		from `tabItem Subcategory` group by category", as_dict=True)
	categories = {}
	for c in cat_subcat:
		categories[c.get("category")] = c.get("subcategory").split(",")

	# item details
	cond = "where 1=1 "
	if filters.get("item_group"):
		cond += " and i.item_group = '{}'".format(filters.get("item_group"))
	if filters.get("category"):
		# {category: [subcat1, subcat2]}
		subcat_list = [sb for cat, subcat in filters.get("category").items() for sb in subcat]
		if len(subcat_list):
			subcat_tpl = "(" + ",".join("'{}'".format(i) for i in subcat_list) + ")"
			cond += " and c.subcategory in {}".format(subcat_tpl)
	if filters.get("search_txt"):
		fil = "'%{0}%'".format(filters.get("search_txt"))
		cond += """ and (i.item_code like %s or i.item_name like %s)"""%(fil, fil)

	item_details = frappe.db.sql("""
		select
			i.item_code, i.item_name, i.image, group_concat(concat(c.category,',',c.subcategory))
			as category, ifnull(b.actual_qty, 0) as qty, d.default_warehouse
		from
			tabItem i left join `tabCategory List` c  on c.parent = i.name
		left join
			`tabItem Default` d on d.parent = i.name and d.company = '{}'
		left join
			`tabBin` b on b.item_code = i.item_code and d.default_warehouse = b.warehouse
		{}
		group by i.name
	""".format(company, cond), as_dict=True)

	data = {"item_group": item_group, "category": categories, "items": item_details}
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
	print "__________________________________________", item_details
	return item_details