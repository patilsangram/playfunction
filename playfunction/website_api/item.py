import frappe
from frappe import _
import json
from category import get_child_categories


filter_flags = ["sales_item", "community_center", "best_seller",
	"gift_ideas", "award_wining", "our_range", "new_item"]

@frappe.whitelist(allow_guest=True)
def get_category_items(data):
	"""returns items with category
		data:{
			'category':
			'subcategory':
			'search':
			'sales_item':
			'community_center':
			'best_seller':
			'gift_ideas':
		}
	"""
	try:
		response = frappe._dict()
		data = json.loads(data)
		cond = " where 1=1"
		if data.get("category"):
			child_cat = get_child_categories(data.get("category"))
			child_cat.append(data.get("category"))
			chid_category = "(" + ",".join("'{}'".format(c) for c in child_cat) + ")"
			cond += " and (c.catalog_level_1 in {0} or c.catalog_level_2 in {0}\
				or c.catalog_level_3 in {0} or c.catalog_level_4 in {0})".format(chid_category)

		if data.get("search"):
			cond += " and (i.name like '{0}' or i.item_name like '{0}'\
				or i.age like '{0}' or i.sp_without_vat like '{0}')".format("%{}%".format(search))

		for f in filter_flags:
			if data.get(f):
				cond += " and i.{} = 'Yes'".format(f)

		query = """
			select
				i.name as item_code, i.item_name, i.image, i.age as age_range,
				i.sp_without_vat as selling_price,
				if (i.discount_percentage > 0,
				i.sp_without_vat - (i.sp_without_vat*i.discount_percentage/100.00),
				i.sp_without_vat) as after_discount,
			from
				`tabItem` i left join `tabBin` b on b.item_code = i.name
			left join
				`tabCatalog` c on c.parent = i.name
			{} 	group by i.name
		""".format(cond)
		items = frappe.db.sql(query,as_dict=True)
		response["items"] = items
		
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch category items: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title="Website API: get_category_items")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def search(search=None):
	"""
		returns the details on the basis of search
		search:search text/brands/items
	"""
	try:
		# Need to find category
		category = None
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
				or i.age like '{0}' or i.brand like  '{0}')".format("%{}%".format(search))

		query = """
			select distinct
				i.name as item_code, i.item_name, i.brand, i.image,i.age as age_range,
				i.sp_without_vat as selling_price,
			from
				`tabItem` i left join `tabBin` b on b.item_code = i.name
			left join
				`tabCatalog` c on c.parent = i.name
			{} 	group by i.name
		""".format(cond)
		items = frappe.db.sql(query,as_dict=True)
		response["items"] = items
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title="Website API: search")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def get_categorised_item(catalog_level_1, catalog_level_2, age=None, manufacturer=None, catalog_level_3=None, catalog_level_4=None, price_from=None,price_to=None):
	try:
		response = frappe._dict()
		cond = " where 1=1"

		# catalog_level conditions
		levels = [catalog_level_1, catalog_level_2, catalog_level_3, catalog_level_4]

		for idx, level in enumerate(levels):
			if level:
				cond += " and c.{} = '{}'".format('catalog_level_' + str(idx+1), level)

		if manufacturer:
			cond += " and i.brand like '{0}'".format("%{}%".format(manufacturer))

		if age:
			cond += " and i.age like '{0}'".format("%{}%".format(age))

		if price_from and price_to:
			cond += " and i.sp_without_vat between '{}' and '{}'".format(price_from, price_to)

		query = """
			select
				i.name as item_code, i.item_name, i.brand, i.age as age_range,
				i.sp_without_vat as selling_price, i.image
			from
				`tabItem` i left join `tabCatalog` c on c.parent = i.name
			{} group by i.name
		""".format(cond)

		items = frappe.db.sql(query, as_dict=True)
		response["items"] = items
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch toys: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title="Website API: get_categorised_item")
	finally:
		return response


@frappe.whitelist(allow_guest=True)
def get_item_details(item_code):
	"""
		Returns item details
	"""
	try:
		
		response = frappe._dict()
		if not frappe.db.exists("Item", item_code):
			response["data"] = "Item not found"
			frappe.local.response["http_status_code"] = 404
		else:
			items = frappe.db.sql("""
				select
					i.name as item_code, i.image, i.item_name, i.description,
					i.age as age_range, i.sp_without_vat as selling_price,
					if (i.discount_percentage > 0,
					i.sp_without_vat - (i.sp_without_vat*i.discount_percentage/100.00),
					i.sp_without_vat) as after_discount,
					group_concat(concat(v.video_file, "#", v.image)) as item_media
				from
					`tabItem` i left join `tabItem Media` v on v.parent = i.name
					and v.type = 'Video'
				where i.item_code = {}
			""".format(item_code), as_dict=True)

			for i in items:
				if i.get("item_media"):
					item_media = i.pop("item_media")
					media = [{"video": m.split("#")[0], "thumbnail": m.split("#")[1]} for m in item_media.split(",") ]
					i["item_videoes"] = media
				else:
					i["item_videoes"] = []
			response["items"] = items
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch item_details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title="Website API: get_item_details")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def recommended_items(item_code):
	"""
		Returns recommended item details
	"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Item", item_code):
			response["data"] = "Item not found"
			frappe.local.response["http_status_code"] = 404
		else:
			items = frappe.db.sql("""select i.name as item_code, i.item_name, i.image, i.sp_without_vat as selling_price, i.age as age_range,r.item_name,r.item_code,r.image  
					from `tabItem` i left join `tabRecommend Item` r on r.parent = i.name where i.name = {0} and r.item_code is not null """.format(item_code),as_dict=True)
			response["items"] = items
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch item_details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title="Website API: recommended_items")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def related_items(data):
	"""
		Returns related item details
		data:{
			'item_code':
			'sales_item':
			'best_seller':
			'award_wining':
			'new_item':
		}
	"""
	try:
		response = frappe._dict()
		data = json.loads(data)
		cond = " where 1=1"
		if data.get("item_code"):
			cond += " and (i.item_code = {0})".format(data.get("item_code"))

		for f in filter_flags:
			if data.get(f):
				cond += " and i.{} = 'Yes'".format(f)

		query = """
			select
				i.name as item_code, i.item_name, i.image, i.sp_without_vat as selling_price,
				i.age as age_range,r.item_name,r.item_code,r.image
			from
				`tabItem` i left join `tabRelated Item` r
				on r.parent = i.name
			{0} group by i.item_code
		""".format(cond)
		items = frappe.db.sql(query, as_dict=True)
		response["items"] = items
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch item_details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title="Website API: related_items")
	finally:
		return response