import frappe
from frappe import _
import json
from playfunction.mobile_api.category import get_child_categories

@frappe.whitelist(allow_guest=True)
def get_category_items(data):
	"""
	 	returns items with category,
	 	data:{"category":
	 		"subcategory":
	 		"search":
	 		"sales_item":
		 	"community_center":
		 	"best_seller":
		 	"gift_ideas":
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

		if data.get("sales_item"):
			cond += " and (i.sales_item ='Yes')"

		elif data.get("community_center"):
			cond += " and (i.community_center ='Yes' )"	

		elif data.get("best_seller"):
			cond += " and (i.best_seller ='Yes' )"

		elif data.get("gift_ideas"):
			cond += " and (i.gift_ideas ='Yes' )"

		elif data.get("award_wining"):
			cond += " and (i.award_wining ='Yes' )"

		elif data.get("our_range"):
			cond += " and (i.our_range ='Yes')"

		elif data.get("new_item"):
			cond += " and (i.new_item ='Yes')"

		query = """
			select 
				i.name, i.item_name, i.age as age_range, i.sp_without_vat as selling_price
			from
				`tabItem` i left join `tabBin` b on b.item_code = i.name
			left join
				`tabCatalog` c on c.parent = i.name
			{} 	group by i.name
		""".format(cond)
		items = frappe.db.sql(query,as_dict=True)
		response["items"] = items
		response["status_code"] = 200
		frappe.local.response["http_status_code"] = 200
		
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch category items: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title="Website API: get_category_items")
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
				i.name, i.item_name, i.brand, i.image,i.age as age_range, i.sp_without_vat as selling_price
			from
				`tabItem` i left join `tabBin` b on b.item_code = i.name
			left join
				`tabCatalog` c on c.parent = i.name
			{} 	group by i.name
		""".format(cond)
		items = frappe.db.sql(query,debug=1,as_dict=True)
		response["items"] = items
		response["status_code"] = 200
		frappe.local.response["http_status_code"] = 200
		
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title="Website API: search")
	finally:
		return response

