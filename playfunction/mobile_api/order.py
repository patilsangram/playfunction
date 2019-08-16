import frappe
import json
from frappe import _


@frappe.whitelist()
def get_order_list():
	"""Returns Order List"""
	try:
		response = frappe._dict()
		fields = ["name", "customer", "transaction_date", "total", \
			"billing_status", "status","delivery_status", "docstatus"]
		order_list = frappe.get_all('Sales Order',fields = fields)
		response.update({"data":order_list})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch order list"
		frappe.log_error(message = frappe.get_traceback() , title = "Mobile API: get_order_list")
	finally:
		return response

@frappe.whitelist()
def reorder(order_id):
	"""Create copy of order"""
	try:
		response = frappe._dict()
		if frappe.db.exists("Sales Order", order_id):
			order_doc = frappe.get_doc("Sales Order",order_id)
			reorder_doc = frappe.copy_doc(order_doc)
			reorder_doc.save()
			response = order_details(reorder_doc.name)
		else:
			response["message"] = "Sales Order Not Found"
			frappe.local.response["http_status_code"] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Re-Order Failed.Contact System Manager"
		frappe.log_error(message = frappe.get_traceback() , title = "Mobile API: reorder")
	finally:
		return response

@frappe.whitelist()
def order_details(order_id):
	"""Return Sales Order Details"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Sales Order", order_id):
			response["message"] = "Sales Order not found"
			frappe.local.response["http_status_code"] = 404
		else:
			doc = frappe.get_doc("Sales Order", order_id)
			response["customer"] = doc.customer
			response["order_id"] = doc.name

			# item details
			items = []
			fields = ["item_code", "description", "qty", "rate",
				"discount_percentage", "discount_amount", "amount"]
			for item in doc.get("items"):
				row_data = {}
				for f in fields:
					row_data[f] = item.get(f)
				items.append(row_data)
			response["items"] = items

			# tax, delivery & totals
			response["total"] = doc.get("total")
			response["additional_discount_percentage"] = doc.get("additional_discount_percentage")
			response["after_discount"] = doc.get("net_total")
			response["grand_total"] = doc.get("grand_total")
			response["delivery_charges"] = 0
			response["vat"] = 0

			delivery_account = frappe.db.get_value("Account", {
				"account_name": "Delivery Charge"
			}, "name")

			vat_account = frappe.db.get_value("Account", {
				"account_name": "VAT 17%"
			}, "name")

			for t in doc.get("taxes"):
				if t.account_head == delivery_account:
					response["delivery_charges"] = t.get("tax_amount")
				elif t.account_head == vat_account:
					response["vat"] = t.get("tax_amount")
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Failed to fetch Sales Order Details"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: order_details")
	finally:
		return response

@frappe.whitelist()
def delete_order_item(order_id, item_code):
	"""
		Delete given item_codes from Sales order
		if all deleted then delete Sales order
	"""
	try:
		response = frappe._dict()
		item_code = item_code.encode('utf-8')
		item_list= [ i.strip() for i in item_code.split(",")]

		if not isinstance(item_code, list):
			item_code = [item_code]
		if not frappe.db.exists("Sales Order", order_id):
			response["message"] = "Sales Order not found"
			frappe.local.response['http_status_code'] = 404
		else:
			order = frappe.get_doc("Sales Order", order_id)
			new_items = []
			for idx, row in enumerate(order.get("items")):
				if not row.item_code in item_list:
					new_items.append(row)
			order.items = new_items
			order.flags.ignore_mandatory = True
			order.save()
			if not len(order.get("items", [])):
				frappe.delete_doc("Sales Order", order_id)
				response["message"] = "Deleted all items"
				frappe.local.response["http_status_code"] = 200
			else:
				response = order_details(order_id)
			frappe.db.commit()
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to Delete Sales Order Item"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: delete_order_item")
	finally:
		return response

@frappe.whitelist()
def update_order(order_id, items):
	"""
	:params
		order_id: sales_order
		items: {
		item_code:
		qty:
		discount_percentage:
		description:
	}
	"""
	try:
		fields = ["item_code", "description", "qty", "rate", "discount_percentage"]
		response = frappe._dict()
		items = json.loads(items)
		if not frappe.db.exists("Sales Order", order_id):
			response["message"] = "Sales Order not found"
			frappe.local.response['http_status_code'] = 404
		else:
			if not all([ f in fields for f in items.keys()]) or not items.get("item_code"):
				response["message"] = "Invalid Data"
				frappe.local.response["http_status_code"] = 422
			else:
				order = frappe.get_doc("Sales Order", order_id)
				existing_item = False
				for row in order.get("items"):
					# update item row
					if row.get("item_code") == items.get("item_code"):
						existing_item = True
						row.update(items)
				# add new item
				if not existing_item:
					order.append("items", items)
				order.save()
				frappe.db.commit()
				response = order_details(order.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Sales Order update failed"
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: update_order")
	finally:
		return response

@frappe.whitelist()
def store_sales_token(order_id, data):
	"""Store Private/Public Token received from GetUrl API"""
	try:
		tokens = json.loads(data)
		if not frappe.db.exists("Sales Order", order_id):
			frappe.local.response['http_status_code'] = 404
			return "Order not found"
		elif not tokens or not tokens.get("PrivateSaleToken"):
			frappe.local.response['http_status_code'] = 422
			return "Tokens not found"
		else:
			doc = frappe.get_doc("Sales Order", order_id)
			doc.sales_tokens = json.dumps(tokens)
			doc.save()
			frappe.db.commit()
			return "Tokens Saved Successfully."
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: store_sales_token")
		return "Tokens Update Failed"

@frappe.whitelist()
def get_sales_token(order_id):
	"""Get Sales Token from Sales Order"""
	try:
		if not order_id or not frappe.db.exists("Sales Order", order_id):
			frappe.local.response['http_status_code'] = 404
			return "Order not found"
		else:
			doc = frappe.get_doc("Sales Order", order_id)
			if not doc.get("sales_tokens"):
				frappe.local.response['http_status_code'] = 404
				return "Tokens not found"
			else:
				return json.loads(doc.get("sales_tokens"))
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		frappe.log_error(message=frappe.get_traceback() , title="Mobile API: get_sales_token")
		return "Tokens fetch Failed"