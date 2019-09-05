import frappe
import json
from frappe import _
from erpnext.selling.doctype.quotation.quotation import make_sales_order


@frappe.whitelist()
def place_order(quote_id):
	try:
		response = frappe._dict()
		if not frappe.db.exists("Quotation", quote_id):
			response["message"] = "Quotation not found"
			frappe.local.response["http_status_code"] = 404
		else:
			doc = frappe.get_doc("Quotation", quote_id)
			doc.workflow_state = "Approved"
			doc.save()
			doc.submit()

			# sales order
			sales_order = make_sales_order(doc.name)
			if sales_order:
				sales_order.delivery_date = frappe.utils.today()
				sales_order.save()
				response["message"] = "Order Placed Successfully."
				response["order_id"] = sales_order.name
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Error occured while placing order"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: place_order")
	finally:
		return response

@frappe.whitelist()
def order_details(order_id):
	"""Return Sales Order Details"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Sales Order", order_id):
			response["message"] = "Order not found"
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
		response["message"] = "Failed to fetch Order Details"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: order_details")
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
		frappe.log_error(message=frappe.get_traceback() , title="Website API: update_order")
	finally:
		return response

@frappe.whitelist()
def order_history(page_index=0, page_size=10):
	"""Returns Order List"""
	try:
		response = frappe._dict()
		customer = frappe.db.get_value("Customer",{"user": frappe.session.user},"name")
		if not customer:
			response["message"] = "Customer doesn't exists."
			frappe.local.response["http_status_code"] = 422
		else:
			all_records = frappe.get_all("Sales Order", filters={"customer": customer})
			fields = ["name as order_id", "transaction_date as date", "delivery_status", "total"]
			order_list = frappe.get_all("Sales Order", filters={"customer": customer},\
				fields=fields, start=page_index, limit=page_size, order_by="creation")
			response.update({
				"data": order_list,
				"total": len(all_records)
			})
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Unable to fetch order list"
		frappe.log_error(message=frappe.get_traceback(), title="Website API: get_order_list")
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
			response["message"] = "Order not found"
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
		response["message"] = "Unable to Delete Order Item"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: delete_order_item")
	finally:
		return response