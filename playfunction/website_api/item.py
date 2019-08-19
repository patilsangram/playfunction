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
				i.name, i.item_name, i.image, i.age as age_range, i.sp_without_vat as selling_price
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
		items = frappe.db.sql(query,as_dict=True)
		response["items"] = items
		response["status_code"] = 200
		frappe.local.response["http_status_code"] = 200
		
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: search")
	finally:
		return response

@frappe.whitelist()
def add_to_wishlist(data):
	"""
	 	data:{ "item_code":
			   "item_name":
			   "qty":
			   "age":
			   }
	"""
	try:
		response = frappe._dict()
		items = json.loads(data)
		cust = frappe.db.get_value("Customer",{'user':frappe.session.user},"name")
		if cust:
			wishlist_doc = frappe.get_value("Wishlist",{'customer':cust},"name")
			if wishlist_doc:
				wishlist_doc = frappe.get_doc("Wishlist",wishlist_doc)
				existing_item = False
				for row in wishlist_doc.get("items"):
					# update item row
					if row.get("item_code") == items.get("item_code"):
						existing_item = True
						row.update(items)
				# add new item
				if not existing_item:
					wishlist_doc.append("items", items)
				wishlist_doc.save(ignore_permissions= True)
				frappe.db.commit()
				response["message"] = "Wishlist is updated"
				frappe.local.response["http_status_code"] = 200
			else:
				wishlist_doc = frappe.new_doc("Wishlist")
				wishlist_doc.customer = cust
				wishlist_doc.user = frappe.session.user 
				wishlist_doc.append("items", items)
				wishlist_doc.save(ignore_permissions= True)
				frappe.db.commit()
				response["message"] = "Wishlist Created"
				frappe.local.response["http_status_code"] = 200
		else:
			response["status_code"] = 404
			response["message"] = "Customer not found"
			frappe.local.response['http_status_code'] = 404

	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to create Wishlist: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: add_to_wishlist")
	finally:
		return response

@frappe.whitelist()
def delete_wishlist(name,item_code):
	try:
		response = frappe._dict()
		item_code = item_code.encode('utf-8')
		item_list= [ i.strip() for i in item_code.split(",")]
		cust = frappe.db.get_value("Customer",{'user':frappe.session.user},"name")
		wish_doc = frappe.get_value("Wishlist",{'customer':cust},"name")
		if frappe.db.exists("Wishlist",wish_doc):
			wish = frappe.get_doc("Wishlist", wish_doc)
			new_items = []
			for idx, row in enumerate(wish.get("items")):
				if not row.item_code in item_list:
					new_items.append(row)
			wish.items = new_items
			wish.flags.ignore_mandatory = True
			wish.save()
			response["status_code"] = 200
			response["message"] = "Wishlist Item deleted"
			if not len(wish.get("items", [])):
				frappe.delete_doc("Wishlist", wish_doc)
				response["message"] = "Deleted all items"
				frappe.local.response["http_status_code"] = 200
			frappe.db.commit()
		else:
			response["status_code"] = 404
			response["message"] = "Wishlist not found"
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to delete Wishlist"
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: delete_wishlist")
	finally:
		return response


@frappe.whitelist()
def get_wishlist_details():
	try:
		item_fields = ["item_code", "item_name","qty", "image", "description","rate","age"]
		response = frappe._dict()
		cust = frappe.db.get_value("Customer",{'user':frappe.session.user},"name")
		wishlist_doc =frappe.get_value("Wishlist",{'customer':cust},"name")
		if frappe.db.exists("Wishlist",wishlist_doc):
			wishlist = frappe.get_doc("Wishlist", wishlist_doc)
			items = []
			# fetch required item details
			for row in wishlist.get("items"):
				row_data = {}
				for f in item_fields:
					row_data[f] = row.get(f)
				items.append(row_data)
			response["items"] = items
		else:
			response["message"] = "Data not found"
			response["status_code"] = 404
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch wishlist"
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: get_wishlist_details")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def get_categorised_item(catalog_level_1, catalog_level_2, age, manufacturer=None, catalog_level_3=None, catalog_level_4=None, price_from=None,price_to=None):
	try:
		response = frappe._dict()
		cond = " where 1=1"
		if catalog_level_1:
			cond += " and (c.catalog_level_1 = '{}')".format(catalog_level_1)

		if catalog_level_2:
			cond += " and (c.catalog_level_2 = '{}')".format(catalog_level_2)

		if catalog_level_3:
			cond += " and (c.catalog_level_3 = '{}')".format(catalog_level_3)

		if catalog_level_4:
			cond += " and (c.catalog_level_4 = '{}')".format(catalog_level_4)

		if manufacturer:
			cond += " and (i.brand like '{0}')".format("%{}%".format(manufacturer))

		if age:
			cond += " and (i.age like '{0}')".format("%{}%".format(age))

		if price_from and price_to:
			cond += " and (i.sp_without_vat between '{}' and '{}')".format(price_from, price_to)

		query = """ 
				select i.name, i.item_name, i.brand, i.age as age_range, i.sp_without_vat as selling_price
				from
					`tabItem` i left join `tabCatalog` c on c.parent = i.name
				 {} group by i.name """.format(cond)
		items = frappe.db.sql(query,as_dict=True)
		response["items"] = items
		frappe.local.response["http_status_code"] = 200
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch toys: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: get_categorised_item")
	finally:
		return response


@frappe.whitelist()
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
			items = frappe.db.sql("""select i.name, i.image, i.item_name, i.age as age_range, group_concat(concat(v.video_file, "#", v.image)) as item_media
			 					from `tabItem` i left join `tabItem Media` v on v.parent = i.name and v.type = 'Video' 
			 	 				where i.item_code = {} """.format(item_code),as_dict=True)
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
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch item_details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: get_item_details")
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
			items = frappe.db.sql("""select i.name, i.item_name, i.image, i.sp_without_vat as selling_price, i.age as age_range,r.item_name,r.item_code,r.image  
				from `tabItem` i left join `tabRecommend Item` r on r.parent = i.name where i.name = {0} """.format(item_code),as_dict=True)
			response["items"] = items
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch item_details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: recommended_items")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def related_items(data):
	"""
		Returns related item details
		data:{"item_code":
	 		"sales_item":
		 	"best_seller":
		 	"award_wining":
		 	"new_item":
		 } 
	"""
	try:
		response = frappe._dict()
		data = json.loads(data)
		cond = " where 1=1"
		if data.get("item_code"):
			cond += " and (i.item_code = {0})".format(data.get("item_code"))

		if data.get("sales_item"):
			cond += " and (i.sales_item ='Yes')"

		elif data.get("best_seller"):
			cond += " and (i.best_seller ='Yes' )"

		elif data.get("award_wining"):
			cond += " and (i.award_wining ='Yes' )"

		elif data.get("new_item"):
			cond += " and (i.new_item ='Yes')"

		query = ("""select i.name, i.item_name, i.image, i.sp_without_vat as selling_price, i.age as age_range,r.item_name,r.item_code,r.image  
			from `tabItem` i left join `tabRelated Item` r on r.parent = i.name
			{0}  group by i.item_code
			""".format(cond))
		items=frappe.db.sql(query,debug=1,as_dict=True)
		response["items"] = items
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to fetch item_details: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: recommended_items")
	finally:
		return response

