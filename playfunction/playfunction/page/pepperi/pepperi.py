import frappe, json, erpnext


@frappe.whitelist()
def get_item_groups():
	fields = ["name", "parent_item_group", "is_group", "image"]
	erp_item_group = ['All Item Groups','Sub Assemblies','Services','Raw Material','Products','Consumable']
	item_groups = frappe.db.get_all("Item Group", {"name": ("not in", erp_item_group)}, fields)
	return item_groups

@frappe.whitelist()
def get_items_and_categories(filters):
	# return item categories/Sub categories along with item list
	company = erpnext.get_default_company() or frappe.db.get_all("Company")[0].get("name")
	filters = json.loads(filters)
	price_list = "Standard Selling"

	item_group = get_item_groups()

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
		subcat_list = [sb for cat, subcat in filters.get("category").items() for sb in subcat if sb != "All"]
		if len(subcat_list):
			subcat_tpl = "(" + ",".join("'{}'".format(i) for i in subcat_list) + ")"
			cond += " and c.subcategory in {}".format(subcat_tpl)

	if filters.get("search_txt"):
		fil = "'%{0}%'".format(filters.get("search_txt"))
		cond += """ and (i.item_code like %s or i.item_name like %s)"""%(fil, fil)

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
		{}
		group by i.name
	""".format(company, price_list,cond), as_dict=True)

	data = {"item_group": item_group, "category": categories, "items": item_details}
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

@frappe.whitelist()
def checkout(data):
	try:
		data = json.loads(data)
		cart_items = data.get("items")
		if cart_items:
			items = []
			doc = frappe.new_doc("Quotation")
			doc.selling_price_list = "Standard Selling"
			doc.customer = frappe.get_value("Customer", {}, "name")
			for k, v in cart_items.items():
				row = {"item_code": k, "qty": v[0]}
				doc.append("items",row)
			doc.save()
			return doc.name
		else:
			frappe.msgprint("Please add items to cart first")
			return
	except Exception as e:
		frappe.msgprint("Something went wrong ..")
		return

