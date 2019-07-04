import frappe
from frappe import _


@frappe.whitelist()
def get_categories(search=None):
	"""
	returns group level 1 and 2 Item Groups/categories
	:param search: search text
	"""


	# TODO - {"parent_category": [{"child category data"}]}
	try:
		response = frappe._dict()
		cond = ""
		if search:
			cond += " and name like '{0}' or parent_item_group like '{0}'".format("%{}%".format(search))

		query = """
			select name as category, parent_item_group as parent_category,
			image from `tabItem Group`
			where name not in ('All Item Groups', 'Products', 'Raw Material', 
			'Services', 'Sub Assemblies', 'Consumable') and group_level = 2 {}
		""".format(cond)

		categories_data = frappe.db.sql(query, as_dict=True)

		# grouping in {parent:childs}
		categories = {}
		for cat in categories_data:
			parent = cat.pop("parent_category")
			if cat.get("parent_category") not in categories:
				categories[parent] = [cat]
			else:
				cat_list = categories[parent]
				cat_list.append(cat)
				categories[parent] = cat_list
		response.update({"categories":categories, "status_code": 200})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable to fetch categories: {}".format(str(e))
	finally:
		return response