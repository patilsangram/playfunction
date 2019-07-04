import frappe
from frappe import _


@frappe.whitelist()
def get_categories(search=None, only_parent=False, parent=None):
	"""Get category list

	:param search: search text
	:param only_parent: group level 1 categories
	:param parent: parent_item_group
	"""
	# TODO - {"parent_category": [{"child category data"}]}
	try:
		response = frappe._dict()
		cond = ""
		if only_parent:
			cond += " and group_level=1"
		if search:
			cond += " and name like '{}'".format("%{}%".format(search))
		if parent:
			cond += " and parent_item_group = '{}'".format(parent)

		query = """
			select name, parent_item_group as parent_category, 
			is_group,group_level, image from `tabItem Group` 
			where name not in ('All Item Groups', 'Products', 'Raw Material', 
			'Services', 'Sub Assemblies', 'Consumable') {} 
			order by group_level
		""".format(cond)

		categories = frappe.db.sql(query, as_dict=True)
		response.update({"categories":categories, "status_code": 200})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		response["message"] = "Unable to fetch categories: {}".format(str(e))
	finally:
		return response