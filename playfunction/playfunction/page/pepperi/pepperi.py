import frappe, json, erpnext


@frappe.whitelist()
def get_item_groups():
	fields = ["name", "image"]
	filters = {"name": ("!=", "All Item Groups"), "is_group": 1}
	item_groups = frappe.db.get_all("Item Group", filters, fields, ignore_permissions=True)
	return item_groups

@frappe.whitelist()
def get_items_and_categories(filters):
	# return item categories/Sub categories along with item list
	company = erpnext.get_default_company() or frappe.db.get_all("Company")[0].get("name")
	filters = json.loads(filters)
	price_list = "Standard Selling"
	customer_discount = frappe.db.get_value("Customer", {"user": frappe.session.user}, "discount_percentage") or 0
	cond = " "

	# parent-child item group
	groups = frappe.db.sql("""select p.name as parent, group_concat(c.name) as child
		from `tabItem Group` p left join `tabItem Group` c on c.parent_item_group = p.name
		where p.is_group = 1 and p.name != 'All Item Groups' group by p.name""", as_dict=True)

	item_groups = {
		g.get("parent"): g.get("child").split(",") \
		if g.get("child") else [] for g in groups
	}

	cat_subcat = frappe.db.sql("select group_concat(name) as subcategory, category \
		from `tabItem Subcategory` group by category", as_dict=True)

	categories = {}
	for c in cat_subcat:
		categories[c.get("category")] = c.get("subcategory").split(",")

	# item group condition
	if filters.get("item_group") and (not filters.get("child_item_group") \
		or filters.get("child_item_group") == "All"):
		parent_group = filters.get("item_group")
		group_list = [parent_group]
		group_list.extend([ i.get("name") for i in frappe.get_list("Item Group", {"parent_item_group": parent_group}, ignore_permissions=True) ])
	elif filters.get("child_item_group"):
		group_list = [filters.get("child_item_group")]

	cond += " and i.item_group in {}".format("(" + ",".join("'{}'".format(i) for i in group_list) + ")")

	if filters.get("category"):
		# {category: [subcat1, subcat2]}
		subcat_list = [sb for cat, subcat in filters.get("category").items() for sb in subcat if sb != "All"]
		if len(subcat_list):
			subcat_tpl = "(" + ",".join("'{}'".format(i) for i in subcat_list) + ")"
			cond += " and c.subcategory in {}".format(subcat_tpl)

	if filters.get("search_txt"):
		fil = "'%{0}%'".format(filters.get("search_txt"))
		cond += """ and (i.item_code like %s or i.item_name like %s)"""%(fil, fil)

	discount_query = " ifnull(i.discount_percentage, 0) as discount " \
		if not customer_discount else "{} as discount ".format(customer_discount)
	item_details = frappe.db.sql("""
		select
			i.item_code, i.item_name, i.image, {},
			group_concat(concat(c.category,',',c.subcategory)) as category, 
			ifnull(b.actual_qty, 0) as qty, d.default_warehouse, p.price_list_rate as price
		from
			tabItem i left join `tabCategory List` c  on c.parent = i.name
		left join
			`tabItem Default` d on d.parent = i.name and d.company = '{}'
		left join
			`tabBin` b on b.item_code = i.item_code and d.default_warehouse = b.warehouse
		left join
			`tabItem Price` p on p.item_code = i.item_code and p.price_list = '{}'
		where i.is_pepperi_item = 1 {}
		group by i.name
	""".format(discount_query, company, price_list,cond), as_dict=True)

	data = {"item_groups": item_groups, "category": categories, "items": item_details}
	return data


@frappe.whitelist()
def get_item_details(item_code):
	# TODO: make common method
	# item selling price as per login customer
	company = erpnext.get_default_company() or frappe.db.get_all("Company")[0].get("name")
	price_list = "Standard Selling"
	item_details = frappe.db.sql("""
		select
			i.item_code, i.item_name, i.image, group_concat(concat(c.category,',',c.subcategory))
			as category, ifnull(b.actual_qty, 0) as qty, d.default_warehouse, p.price_list_rate as price
		from
			tabItem i left join `tabCategory List` c  on c.parent = i.name
		left join
			`tabItem Default` d on d.parent = i.name and d.company = '{}'
		left join
			`tabBin` b on b.item_code = i.item_code and d.default_warehouse = b.warehouse
		left join
			`tabItem Price` p on p.item_code = i.item_code and p.price_list = '{}'
		where i.name = '{}'
		group by i.name
	""".format(company, price_list, item_code), as_dict=True)
	return item_details

