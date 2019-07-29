import frappe
import json
from category import get_child_categories


@frappe.whitelist()
def get_category_items(category, subcategory=None, search=None):
	try:
		response = frappe._dict()
		cond = " where 1=1"
		category = category if not subcategory else subcategory
		if category:
			child_cat = get_child_categories(category)
			child_cat.append(category)
			chid_category = "(" + ",".join("'{}'".format(c) for c in child_cat) + ")"
			cond += " and (c.catalog_level_1 in {0} or c.catalog_level_2 in {0}\
				or c.catalog_level_3 in {0} or c.catalog_level_4 in {0})".format(chid_category)

		if search:
			cond += " and (i.name like '{0}' or i.item_name like '{0}'\
				or i.age like '{0}')".format("%{}%".format(search))

		query = """
			select
				distinct i.name, i.image, i.item_name, i.age as age_range, i.cost_price,
				i.discount_percentage, i.cost_price - i.cost_price*i.discount_percentage/100
				as after_discount_price, ifnull(sum(b.actual_qty), 0) as stock_qty,
				group_concat(f.file_url) as item_videoes
			from
				`tabItem` i left join `tabBin` b on b.item_code = i.name
			left join
				`tabCatalog` c on c.parent = i.name
			left join
				`tabFile` f on f.attached_to_name = i.name and f.attached_to_doctype = 'Item'
				and substring_index(f.file_url,'.',-1) in ("m4v","avi","mpg","mp4")
			{}  group by i.name
		""".format(cond)
		items = frappe.db.sql(query, as_dict=True)
		for i in items:
			item_videoes = i.pop("item_videoes") or ""
			i["item_videoes"] = item_videoes.split(",") if item_videoes else []
		response["items"] = items
		response["total"] = len(items)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch category items: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: get_category_items")
	finally:
		return response

@frappe.whitelist()
def get_item_discount(item_code, discount_percentage=0):
	"""
		send item details with given discount percentage
	"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Item", item_code):
			response["message"] = "Item not found"
			frappe.local.response['http_status_code'] = 404
		else:
			discount_query = "i.cost_price - i.cost_price*{}/100 as after_discount_price".format(discount_percentage)
			query = """
				select distinct i.name, i.image, i.item_name, i.age as age_range,
				i.cost_price, {0} as discount_percentage, {1},
				ifnull(sum(b.actual_qty), 0) as stock_qty from `tabItem` i left join `tabBin` b
				on b.item_code = i.name left join `tabCatalog` c on c.parent = i.name
				where i.name = '{2}' group by i.name
			""".format(discount_percentage, discount_query, item_code)
			response["data"] = frappe.db.sql(query, as_dict=True)[0]
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to get discount details"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: get_item_discount")
	finally:
		return response