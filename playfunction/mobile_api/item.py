import frappe
import json
from category import get_child_categories


@frappe.whitelist()
def get_category_items(category, search=None):
	try:
		response = frappe._dict()
		cond = " where 1=1"
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
			select distinct i.name, i.image, i.item_name, i.age as age_range, i.cost_price,
			i.cost_price - i.cost_price*i.discount_percentage/100 as after_discount_price,
			ifnull(sum(b.actual_qty), 0) as stock_qty from `tabItem` i left join `tabBin` b
			on b.item_code = i.name left join `tabCatalog` c on c.parent = i.name 
			{} group by i.name
		""".format(cond)
		items = frappe.db.sql(query, as_dict=True)
		response["status_code"] = 200
		response["items"] = items
		response["total"] = len(items)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch category items: {}".format(str(e))
	finally:
		return response