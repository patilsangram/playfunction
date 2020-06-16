import frappe
import json
from frappe.utils import has_common, flt
from frappe import _
from customer import update_customer_profile
from playfunction.playfunction.invoice_payment import *
from erpnext.selling.doctype.quotation.quotation import make_sales_order


@frappe.whitelist()
def place_order(quote_id, data=None):
	"""
		data: {
			:customer_name- customer name
			:phone
			:email_id
			:house_no
			:apartment_no
			:street_address
			:city
			:delivery_collection_point
			:delivery_city
			:payment_method
		}
	"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Quotation", quote_id):
			response["message"] = "Quotation not found"
			frappe.local.response["http_status_code"] = 404
		else:
			doc = frappe.get_doc("Quotation", quote_id)
			doc.workflow_state = "Approved"
			if data:
				data = json.loads(data)
				doc.delivery_collection_point = data.get("delivery_collection_point")
				doc.delivery_city = data.get("delivery_city")
				doc.shipping_type = data.get("shipping")
				doc.payment_method = data.get("payment_method")

				# delivery charges
				if data.get("shipping") == "Fast delivery to the house at subsidized price - NIS 29":
					delivery_account = frappe.db.get_value("Account", {
						"account_name": "Delivery Charge"
					}, "name")
					delivery_charge_tax = {
						"account_head": delivery_account,
						"tax_amount": 29,
						"charge_type": "Actual",
						"description": delivery_account
					}
					doc.append("taxes", delivery_charge_tax)
			doc.save()
			doc.submit()

			# sales order
			sales_order = make_sales_order(doc.name)
			if sales_order:
				sales_order.delivery_date = frappe.utils.today()
				sales_order.mode_of_order = "Web"
				if data:
					update_customer_profile(data, sales_order.customer)
					sales_order.delivery_collection_point = data.get("delivery_collection_point")
					sales_order.delivery_city = data.get("delivery_city")
					sales_order.shipping_type = data.get("shipping")
					sales_order.payment_method = data.get("payment_method")
				sales_order.save()

				# send back payment_url if payment by card
				# else create Rihvit Invoice
				payment_url = ""
				if data.get("payment_method") == "Payment through card":
					payment_url = get_payment_url(sales_order.name)
				else:
					create_rihvit_invoice(sales_order.name)

				response["payment_url"] = payment_url
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
			fields = ["item_code", "image", "description", "qty", "rate",
				"discount_percentage", "discount_amount", "amount"]
			sp_without_vat = 0
			for item in doc.get("items"):
				row_data = {}
				for f in fields:
					row_data[f] = item.get(f)
				items.append(row_data)
				sp_without_vat = sp_without_vat + (frappe.db.get_value("Item",item.get("item_code"), "sp_without_vat") * item.get('qty'))
			response["items"] = items

			# tax, delivery & totals
			response["total"] = doc.get("total")
			response["additional_discount_percentage"] = doc.get("additional_discount_percentage")
			response["after_discount"] = doc.get("net_total")
			response["grand_total"] = doc.get("grand_total")
			response["delivery_charges"] = 0
			response["vat"] = 0
			vat = doc.get("grand_total") -sp_without_vat
			response["vat"] = flt(vat,2)
			delivery_account = frappe.db.get_value("Account", {
				"account_name": "Delivery Charge"
			}, "name")


			for t in doc.get("taxes"):
				if t.account_head == delivery_account:
					response["delivery_charges"] = t.get("tax_amount")
				elif t.account_head == vat_account:
					pass

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
			if not items.get("item_code"):
				response["message"] = "Invalid Data"
				frappe.local.response["http_status_code"] = 422
			else:
				order = frappe.get_doc("Sales Order", order_id)
				existing_item = False
				item_details = frappe.db.get_value("Item", items.get("item_code"),\
					["sp_with_vat", "discount_percentage"], as_dict=True)
				if item_details.get("discount_percentage") > 0:
					items["margin_type"] = "Percentage"
					items["discount_percentage"] = item_details.get("discount_percentage")
				items["price_list_rate"] = item_details.get("sp_with_vat")
				for row in order.get("items"):
					# update item row
					if row.get("item_code") == items.get("item_code"):
						existing_item = True
						updatd_qty = row.get("qty") + items.get("qty")
						items["qty"] = int(updatd_qty)
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
			order_query = """
				select
					so.name as order_id, date(so.transaction_date) as date,
					so.delivery_status, so.total, dn.tracking_number, dn.company_phone_no
				from
					`tabSales Order` so
				left join
					`tabDelivery Note Item` dni on dni.against_sales_order = so.name
				left join
					`tabDelivery Note` dn on dni.parent = dn.name
				where so.customer = '{}' order by so.transaction_date desc
			""".format(customer)

			all_records = frappe.db.sql(order_query, as_dict=True)

			limit_cond = " limit {}, {}".format(page_index, page_size)
			order_list = frappe.db.sql(order_query + limit_cond, as_dict=True)
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
