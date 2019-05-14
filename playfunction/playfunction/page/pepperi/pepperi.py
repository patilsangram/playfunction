import frappe, json, erpnext


erp_item_groups = ['All Item Groups','Products','Raw Material','Services','Sub Assemblies','Consumable']

@frappe.whitelist()
def get_item_groups():
	fields = ["name", "image"]
	filters = {"name": ("not in", erp_item_groups), "is_group": 1, "group_level": 1}
	item_groups = frappe.db.get_all("Item Group", filters, fields, ignore_permissions=True)
	return item_groups

@frappe.whitelist()
def get_items_and_group_tree(filters):
	# return item groups hierarchy and item list
	company = erpnext.get_default_company() or frappe.db.get_all("Company")[0].get("name")
	filters = json.loads(filters)
	price_list = "Standard Selling"
	customer_discount = frappe.db.get_value("Customer", {"user": frappe.session.user}, "discount_percentage") or 0
	cond = " "

	item_group = filters.get("item_group")
	filters_ = {"group_level": (">", 1)}
	fields = ['name','parent_item_group as parent','is_group as expandable']
	data = frappe.get_list("Item Group", fields=fields, filters=filters_)

	item_groups, group_list = get_children(item_group, data, [item_group])


	# item group condition
	if filters.get("child_item_group"):
		group_list = [filters.get("child_item_group")]

	cond += " and i.item_group in {}".format("(" + ",".join("'{}'".format(i) for i in group_list) + ")")

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

	data = {"item_groups": item_groups, "items": item_details}
	return data

def get_children(parent, data, groups=[]):
	children = {}
	for i,v in enumerate(data):
		if v.get('parent') == parent:
			groups.append(v.get('name'))
			if v.get('expandable'):
				children[v.get('name')] = get_children(v.get('name'), data, groups)[0]
			else:
				children[v.get('name')] = {}
	return children, groups

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

