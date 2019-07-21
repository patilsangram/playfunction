import frappe
from frappe import _


@frappe.whitelist()
def get_categories(search=None):
	"""
	returns group level 1 and 2 Item Groups/categories
	:param search: search text
	"""
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
		category_tree = [ {"category_name": k, "sub_category": v} for k,v in categories.items() ]
		response.update({"category": category_tree, "status_code": 200})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch categories: {}".format(str(e))
	finally:
		return response

@frappe.whitelist()
def get_child_categories(category):
	# return sub categorie from hierarchy
	def _get_child(category, data, child):
		for d in data:
			if d.get("parent") == category:
				child.append(d.get("name"))
				if d.get("expandable"):
					_get_child(d.get("name"), data, child)
		return child

	filters_ = {"group_level": (">", 1)}
	fields = ['name','parent_item_group as parent','is_group as expandable']
	data = frappe.get_list("Item Group", fields=fields, filters=filters_)
	categories = _get_child(category, data, [])
	return categories