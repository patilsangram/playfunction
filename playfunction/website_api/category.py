import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_categories(search=None):
	# TODO: Remove this method after confirmation of get_category_tree
	"""
	returns group level 1 and 2 Item Groups/categories
	:param search: search text
	"""
	try:
		response = frappe._dict()
		cond = " 1=1"
		if search:
			cond += " and name like '{0}' or parent_item_group like '{0}'".format("%{}%".format(search))

		query = """
			select name as category, parent_item_group as parent_category,
			image from `tabItem Group`
			where name not in ('All Item Groups', 'Products', 'Raw Material', 
			'Services', 'Sub Assemblies', 'Consumable') and {}
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

@frappe.whitelist(allow_guest=True)
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
	data = frappe.get_list("Item Group", fields=fields, filters=filters_, ignore_permissions=True)
	categories = _get_child(category, data, [])
	return categories

@frappe.whitelist(allow_guest=True)
def get_category_tree():
	"""
		return item group tree hierarchy of custom item groups(category)
		in parent-child structure.
	"""
	fields = ["name as title", "group_level", "parent_item_group", "is_group as has_child"]
	erp_item_group = ['All Item Groups', 'Products', 'Raw Material', 'Services', 'Sub Assemblies', 'Consumable']
	filters = {
		"group_level": [">", 0],
		"name": ["not in", erp_item_group]
	}
	item_groups = frappe.get_all("Item Group", filters, fields, ignore_permissions=True)
	group_tree = []
	for idx, group in enumerate(item_groups):
		if group.get("group_level") == 1:
			childs, item_groups = get_children(group.get("title"), group.get("group_level"), item_groups)
			if len(childs):
				child_level = "level_" + str(group.get("group_level")+1)
				group[child_level] = childs
			else:
				group["has_child"] = 0
			group.pop("parent_item_group")
			group_tree.append(group)

	# sequential arrangement
	sequence_req = ["Therapist", "Parents", "School", "Baby (0-12months)",\
		"Toys", "Outdoor Toys", "Furniture", "Offers and Sale"]
	result = [
		g for seq in sequence_req for g in group_tree if g.get("title") == seq
	]
	return result

def get_children(category, group_level, data):
	children = []
	for idx, group in enumerate(data):
		if group.get("parent_item_group") == category:
			if group.get("has_child"):
				childs, data = get_children(group.get("title"), group.get("group_level"), data)
				if len(childs):
					child_level = "level_" + str(group.get("group_level")+1)
					group[child_level] = childs
				else:
					group["has_child"] = 0
			group.pop("parent_item_group")
			children.append(group)
			#data.remove(group)
	return children, data

@frappe.whitelist(allow_guest=True)
def age_list():
	def sorting(val):
		if "M" in val:
			return int(val.split("M")[0])
		elif "+" in val:
			return len(val.split("+")[0])

	response = frappe._dict()
	age_records = frappe.get_all("Age", ignore_permissions=True)
	age_list = [a.get("name") for a in age_records]
	age_list.sort(key=sorting)
	response["age_list"] = age_list
	return response

@frappe.whitelist(allow_guest=True)
def manufacturer_list():
	response = frappe._dict()
	manufacturers = frappe.get_all("Brand", ignore_permissions=True)
	response["manufacturer_list"] = [m.get("name") for m in manufacturers]
	return response
