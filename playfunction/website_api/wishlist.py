import frappe
import json
from frappe.utils import flt
from playfunction.website_api.user import get_last_quote


@frappe.whitelist()
def add_to_wishlist(data):
	"""
	data:{
		"item_code":
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
			wishlist_doc = frappe.get_value("Wishlist", {
				"customer": cust,
				"status": "Draft"
			},"name")
			if wishlist_doc:
				wishlist_doc = frappe.get_doc("Wishlist", wishlist_doc)
				existing_item = False
				for row in wishlist_doc.get("items"):
					# update item row
					if row.get("item_code") == items.get("item_code"):
						existing_item = True
						row.update(items)
				# add new item
				if not existing_item:
					wishlist_doc.append("items", items)
				wishlist_doc.save(ignore_permissions=True)
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
		else:
			response["message"] = "Customer not found"
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to create Wishlist: {}".format(str(e))
		frappe.log_error(message=frappe.get_traceback(), title = "Website API: add_to_wishlist")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def delete_wishlist(name, item_code):
	try:
		response = frappe._dict()
		item_code = item_code.encode('utf-8')
		item_list= [ i.strip() for i in item_code.split(",")]
		cust = frappe.db.get_value("Customer",{'user':frappe.session.user},"name")
		wish_doc = frappe.get_value("Wishlist",{
			"customer": cust,
			"status": "Draft"
		},"name")
		if frappe.db.exists("Wishlist",wish_doc):
			wish = frappe.get_doc("Wishlist", wish_doc)
			new_items = []
			for idx, row in enumerate(wish.get("items")):
				if not row.item_code in item_list:
					new_items.append(row)
			wish.items = new_items
			wish.flags.ignore_mandatory = True
			wish.save()
			response["message"] = "Wishlist Item deleted"
			if not len(wish.get("items", [])):
				frappe.delete_doc("Wishlist", wish_doc)
				response["message"] = "Deleted all items"
			frappe.db.commit()
		else:
			response["message"] = "Wishlist not found"
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to delete Wishlist"
		frappe.log_error(message=frappe.get_traceback() , title = "Website API: delete_wishlist")
	finally:
		return response


@frappe.whitelist(allow_guest=True)
def get_wishlist_details():
	try:
		item_fields = ["item_code", "item_name","qty", "image", "description","rate","age"]
		response = frappe._dict()
		cust = frappe.db.get_value("Customer",{'user':frappe.session.user},"name")
		wishlist_doc =frappe.get_value("Wishlist",{
			"customer": cust,
			"status": "Draft"
		},"name")
		if frappe.db.exists("Wishlist",wishlist_doc):
			wishlist = frappe.get_doc("Wishlist", wishlist_doc)
			items = []
			# fetch required item details
			for row in wishlist.get("items"):
				row_data = {}
				for f in item_fields:
					row_data[f] = row.get(f)

				# selling/before discount price of Item
				row_data["selling_price"] = frappe.db.get_value("Item",
					row.get("item_code"), "sp_with_vat") or 0
				items.append(row_data)
			response["items"] = items
		else:
			response["message"] = "Data not found"
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch wishlist"
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: get_wishlist_details")
	finally:
		return response

@frappe.whitelist()
def wishlist_checkout():
	"""convert wishlist to order"""
	try:
		response = frappe._dict()
		if frappe.session.user:
			customer = frappe.db.get_value("Customer",{'user':frappe.session.user},"name")
			wishlist = frappe.get_value("Wishlist", {
				"customer": customer,
				"status": "Draft"
			},"name")
			if not wishlist:
				response["message"] = "Wishlist not found"
				frappe.local.response["http_status_code"] = 404
			else:
				wishlist_doc = frappe.get_doc("Wishlist", wishlist)
				wishlist_doc.status = "Converted"
				wishlist_doc.flags.ignore_permissions = True
				wishlist_doc.save()
				quote_id = get_last_quote()[0]
				if quote_id:
					# if cart exist
					quote = frappe.get_doc("Quotation", quote_id)
				else:
					# create new quote
					quote = frappe.new_doc("Quotation")
					quote.party_name = customer
				exising_items = [i.get("item_code") for i in quote.get("items")]
				for i in wishlist_doc.get("items"):
					if i.get("item_code") not in exising_items:
						quote.append("items",{
							"item_code": i.get("item_code"),
							"qty": i.get("qty", 0)
						})
					else:
						# if item already exist just increase the qty
						for idx, qi in enumerate(quote.get("items")):
							if qi.get("item_code") == i.get("item_code"):
								qty = qi.get("qty")
								qi.qty = qty + i.get("qty")
				quote.flags.ignore_mandatory = True
				quote.flags.ignore_permissions = True
				quote.save()
				frappe.db.commit()
				response["message"] = "Added to Cart Successfully ..."
				response["quote_id"] = quote.name
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Order Creation failed"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: wishlist_checkout")
	finally:
		return response
