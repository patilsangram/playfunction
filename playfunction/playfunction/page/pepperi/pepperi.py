#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import frappe, json, erpnext
from six.moves.urllib.parse import urlparse, urlencode
import erpnext

erp_item_groups = ['All Item Groups','Products','Raw Material','Services','Sub Assemblies','Consumable']

@frappe.whitelist()
def get_item_groups():
	fields = ["name", "image"]
	filters = {"name": ("not in", erp_item_groups), "is_group": 1, "group_level": 1}
	item_groups = frappe.db.get_all("Item Group", filters, fields, ignore_permissions=True)
	return item_groups

@frappe.whitelist()
def get_items_and_group_tree(filters):
	company = erpnext.get_default_company() or frappe.db.get_all("Company")[0].get("name")
	filters = json.loads(filters)
	customer_discount = frappe.db.get_value("Customer", {"user": frappe.session.user}, "discount_percentage") or 0
	item_group = filters.get("item_group")
	filters_ = {"group_level": (">", 1)}
	fields = ['name','parent_item_group as parent','is_group as expandable']
	data = frappe.get_list("Item Group", fields=fields, filters=filters_)
	item_groups, group_list = get_children(item_group, data, [item_group])
	price_list = frappe.db.get_value("Customer", {"user": frappe.session.user}, "default_price_list") or "Standard Selling"
	print(group_list)
	discount_query = """ CASE WHEN pr.item_group IS NOT NULL
	THEN pr.discount_percentage  ELSE {}
		END as discount """.format(customer_discount)

	# price_list = "Standard Selling"
	if len(group_list)>1:
		parsed_groups = [ urlparse(g).path for g in item_groups ]
		groups_join = ",".join(["'{}'".format(g) for g in parsed_groups])
	else:
		groups_join = '(' + ','.join('"{}"'.format(i) for i in group_list) + ')'
	cond = """ and (c.catalog_level_1 in ({groups}) or c.catalog_level_2 in ({groups})
or c.catalog_level_3 in ({groups}) or c.catalog_level_4 in ({groups}) )""".format(groups=groups_join)
	query = """SELECT
		i.item_code, i.item_name, i.image,{},
		group_concat(c.catalog_level_1) as catalogs,
		ifnull(b.actual_qty, 0) as qty, d.default_warehouse, i.sp_with_vat as price
		from
				tabItem i left join `tabCatalog` c  on c.parent = i.name
		left join
				`tabItem Default` d on d.parent = i.name and d.company = "{}"
		left join
				`tabBin` b on b.item_code = i.item_code and d.default_warehouse = b.warehouse
		left join
				`tabItem Price` p on p.item_code = i.item_code and p.price_list = "{}"
		left join `tabPricing Rule` pr on pr.item_group = i.item_group
				where i.is_pepperi_item = 1 {}	group by i.name
		""".format(discount_query,company, price_list, cond)
	item_details = frappe.db.sql(query, as_dict=True,debug=True)
	data = {"item_groups": item_groups, "items": item_details}
	return data




@frappe.whitelist()
def get_items_and_group_tree1(filters):
	# return item groups hierarchy and item list
	company = erpnext.get_default_company() or frappe.db.get_all("Company")[0].get("name")
	filters = json.loads(filters)
	customer_discount = frappe.db.get_value("Customer", {"user": frappe.session.user}, "discount_percentage") or 0
	# customer_dic =
	price_list = frappe.db.get_value("Customer", {"user": frappe.session.user}, "default_price_list") or "Standard Selling"
	# price_list = "Standard Selling"
	cond = " "
	item_group = filters.get("item_group")
	filters_ = {"group_level": (">", 1)}
	fields = ['name','parent_item_group as parent','is_group as expandable']
	data = frappe.get_list("Item Group", fields=fields, filters=filters_)
	item_groups, group_list = get_children(item_group, data, [item_group])
	# item group/catalog condition
	if filters.get("child_item_group") and filters.get("child_item_group") != 'All':
		group_list = [filters.get("child_item_group")]
	group_tuple = []
	if len(group_list)>1:
		for i in group_list:
			if i.find('"')>1:
				splited_list = i.split('"')
				i = '"\\'.join(splited_list)
			group_tuple.append(i)
		group_tuple = str(tuple(group_tuple))
	else:
		group_tuple = '(' + ','.join('"{}"'.format(i) for i in group_list) + ')'
	cond += """ and (c.catalog_level_1 in {groups} or c.catalog_level_2 in {groups}
		or c.catalog_level_3 in {groups} or c.catalog_level_4 in {groups} )""".format(groups=group_tuple)
	if filters.get("search_txt"):
		fil = "'%{0}%'".format(filters.get("search_txt"))
		cond += """ and (i.item_code like %s or i.item_name like %s)"""%(fil, fil)

	discount_query = """ CASE
							WHEN pr.item_group IS NOT NULL THEN pr.discount_percentage
						 ELSE {}
						END as discount """.format(customer_discount)
	item_details = frappe.db.sql('''
		select
			i.item_code, i.item_name, i.image, {},
			group_concat(c.catalog_level_1) as catalogs,
			ifnull(b.actual_qty, 0) as qty, d.default_warehouse, i.sp_with_vat as price
		from
			tabItem i left join `tabCatalog` c  on c.parent = i.name
		left join
			`tabItem Default` d on d.parent = i.name and d.company = "{}"
		left join
			`tabBin` b on b.item_code = i.item_code and d.default_warehouse = b.warehouse
		left join
			`tabItem Price` p on p.item_code = i.item_code and p.price_list = "{}"
		left join`tabPricing Rule` pr on pr.item_group = i.item_group
		where i.is_pepperi_item = 1 {}
		group by i.name
	'''.format(discount_query, company, price_list,cond), as_dict=True,debug=True)
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
	item_doc = frappe.get_doc("Item", item_code)
	related_items = item_doc.get("related_item") or []
	# group_concat(concat(c.category,',',c.subcategory)) as category, 2. p.price_list_rate as price
	item_details = frappe.db.sql("""
		select
			i.item_code, i.item_name, i.image, ifnull(b.actual_qty, 0) as qty, d.default_warehouse,i.sp_with_vat as price
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
	""".format(company, price_list, item_code), as_dict=True)[0]
	item_details['related_items'] = related_items
	return item_details
