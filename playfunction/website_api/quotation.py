import frappe
import json
from frappe import _
from frappe.utils import has_common, flt
from erpnext.stock.get_item_details import get_item_details as get_pricing_details

item_fields = ["item_code", "item_name","qty", "discount_percentage", "description", "rate", "amount", "image"]



@frappe.whitelist(allow_guest=True)
def get_cart_details(quote_id):
	"""
		return quotation details.
		items, taxes and total
	"""
	try:
		response = frappe._dict()
		if not frappe.db.exists("Quotation", quote_id):
			# msg = "Invalid Quotation"
			response["message"] = "שגיאה"
			frappe.local.response["http_status_code"] = 404
		else:
			quote = frappe.get_doc("Quotation", quote_id)
			response["customer"] = quote.party_name
			response["quote_id"] = quote.name
			items = []
			# fetch required item details
			sp_without_vat = discount = 0
			for row in quote.get("items"):
				row_data = {}
				for f in item_fields:
					rate = row.get("rate") + row.get("rate") * 0.17
					amount = rate * row.get("qty")
					if f not in ["rate", "amount"]:
						row_data[f] = row.get(f)
					row_data["rate"] = flt(rate, 2)
					row_data["amount"] = flt(amount, 2)
				# selling/before discount price of Item
				# row_data["selling_price"] = frappe.db.get_value("Item",
				# 	row.get("item_code"), "sp_with_vat") or 0
				# item_details = frappe.db.get_value("Item", row.get("item_code"),["sp_with_vat", "last_purchase_rate", "discount_percentage","sp_without_vat"], as_dict=True)
				# if item_details.get("discount_percentage") > 0:
				# 	sp_without_vat = sp_without_vat + (item_details.get("sp_without_vat") * row.get("qty"))*item_details.get("discount_percentage")/100
				# else:
				# 	sp_without_vat =  sp_without_vat + (item_details.get("sp_without_vat") * row.get("qty") )

				# calculations
				if row.get("discount_percentage") > 0:
					per_item_disc = row.get("price_list_rate") * row.get("discount_percentage")/100
					discount += per_item_disc*row.get("qty")

				sp_without_vat += row.get("rate") * row.get("qty")
				row_data["selling_price"] = row.price_list_rate
				items.append(row_data)
			response["items"] = items
			#delivery_details
			response["delivery_collection_point"] = quote.get("delivery_collection_point")
			response["shipping_type"] = quote.get("shipping_type")
			response["delivery_city"] = quote.get("delivery_city")

			#check delivery charges
			delivery_account = frappe.db.get_value("Account", {
				"account_name": "Delivery Charge"
			}, "name")

			# vat account
			vat_account = frappe.db.get_value("Account", {
				"account_name": "VAT 17%"
			}, "name")

			delivery_charges = sales_tax = 0
			for tax_ in quote.get("taxes", []):
				if tax_.get("account_head") == delivery_account:
					delivery_charges = tax_.get("tax_amount")
				elif tax_.get("account_head") == vat_account:
					sales_tax =  tax_.get("tax_amount")

			# taxes & total section
			response["discount"] = discount
			response["total"] = quote.get("grand_total", 0)
			response["shippingCharge"] = discount
			response["delivery_charges"] = delivery_charges
			#sales_tax = quote.get("total")-sp_without_vat if quote.get("total") != 0 and sp_without_vat !=0 else 0
			#response["sales_tax"] = flt(sales_tax,2)
			response["sales_tax"] = flt(sales_tax,2)
			response["sp_without_vat"] = sp_without_vat
			#response["amount_due"] = flt(sp_without_vat,2)
			response["amount_due"] = flt(quote.total,2)
			response["sub_total"] = quote.get("grand_total")
			# proposal_stages
			proposal_state = ["Proposal Received", "Proposal Processing", "Proposal Ready"]
			if quote.get("workflow_state") in proposal_state:
				response["proposal_state"] = quote.get("workflow_state")
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		# msg = "Unable to fetch Quotation Details"
		response["message"] = "שגיאה בפרטי הבקשה"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: get_cart_details")
	finally:
		return response

@frappe.whitelist()
def add_to_cart(items, is_proposal=False):
	"""
	:param data: {
		items: {
			item_code:
			qty:
		}
	}
	"""
	try:
		response = frappe._dict()
		items = json.loads(items)
		user= frappe.get_doc("User",frappe.session.user)
		#check customer exists or not for the current user
		customer = frappe.db.get_value("Customer",{'user':user.name},"name")

		if not customer:
			# msg = "Customer doesn't exists."
			response["message"] = "לקוח אינו קיים"
			frappe.local.response['http_status_code'] = 200
		else:
			billing_addr = frappe.db.sql("""
				select
					ad.name
				from
					`tabAddress` ad, `tabDynamic Link` dl
				where
					dl.parent = ad.name and
					dl.parenttype = 'Address' and
					dl.link_doctype = 'Customer' and
					dl.link_name = '{}' and
					ad.address_type = 'Billing' and
					ifnull(ad.disabled, 0) = 0
				""".format(customer), as_dict=True
			)
			address = billing_addr[0]["name"] if len(billing_addr) else ""
 
			if not has_common(["item_code", "qty"], items.keys()) or not all([ f in item_fields for f in items.keys()]):
				# msg = "Invalid data"
				response["message"] = "שגיאה בנתונים"
				frappe.local.response["http_status_code"] = 422
			else:
				quote = frappe.new_doc("Quotation")
				quote.party_name = customer
				quote.customer_address = address
				quote.selling_price_list = "Meuhedet"
				# update price_list_rate, margin_type, discount_percentage
				items = get_item_details(quote, items)

				quote.append("items", items)

				# Tax - VAT 17%
				vat_account = frappe.db.get_value("Account", {
					"account_name": "VAT 17%"
				}, ["name", "tax_rate"], as_dict=True)
				quote.taxes_and_charges = vat_account.get("name")
				vat_tax = {
					"account_head": vat_account.get("name"),
					"charge_type": "On Net Total",
					"rate": vat_account.get("tax_rate"),
					"description": "VAT 17% - Website"
				}
				quote.append("taxes", vat_tax)

				quote.run_method("set_missing_values")
				# proposal
				if is_proposal:
					quote.workflow_state = "Proposal Received"
				quote.save(ignore_permissions=True)
				frappe.db.commit()
				response = get_cart_details(quote.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		# msg = "Quotation Creation failed"
		response["message"] = "שגיאה בתהליך הבקשה להצעה".format(str(e))
		frappe.log_error(message=frappe.get_traceback() , title="Website API: add_to_cart")
	finally:
		return response

@frappe.whitelist()
def update_cart(quote_id, items):
	"""
	:params
		quote_id: quotation
		items: {
			item_code:
			qty:
		}
	"""
	try:
		response = frappe._dict()
		items = json.loads(items)

		if not frappe.db.exists("Quotation", quote_id):
			# msg = "Quotation not found"
			response["message"] = "הצעת המחיר לא נמצאה"
			frappe.local.response['http_status_code'] = 404
		else:
			if not all([ f in item_fields for f in items.keys()]):
				# msg = "Invalid Data"
				response["message"] = "שגיאה בנתונים"
				frappe.local.response["http_status_code"] = 422
			else:
				quote = frappe.get_doc("Quotation", quote_id)
				items = get_item_details(quote, items)

				existing_item = False
				for row in quote.get("items"):
					# update item row
					if row.get("item_code") == items.get("item_code"):
						existing_item = True
						updatd_qty = row.get("qty") + items.get("qty")
						# if qty == 0 remove that row
						if updatd_qty == 0:
							frappe.delete_doc_if_exists("Quotation Item", row.name)
						else:
							items["qty"] = int(updatd_qty)
							row.update(items)
				# add new item
				if not existing_item:
					quote.append("items", items)

				quote.run_method("set_missing_values")
				quote.flags.ignore_mandatory = True
				quote.flags.ignore_permissions = True
				quote.save()
				frappe.db.commit()
				response = get_cart_details(quote.name)
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		# msg = "Quotation Update failed"
		response["message"] = "שגיאה בעדכון הבקשה להצעה"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: update_cart")
	finally:
		return response

@frappe.whitelist()
def delete_cart_item(quote_id, item_code):
	"""Delete given item_codes from Quote if all deleted then delete Quote"""
	try:
		response = frappe._dict()
		item_code = item_code.encode('utf-8')
		item_list= [ i.strip() for i in item_code.split(",")]

		if not isinstance(item_code, list):
			item_code = [item_code]
		if not frappe.db.exists("Quotation", quote_id):
			# msg = "Quotation not found"
			response["message"] = "הצעת המחיר לא נמצאה"
			frappe.local.response['http_status_code'] = 404
		else:
			quote = frappe.get_doc("Quotation", quote_id)
			new_items = []
			for idx, row in enumerate(quote.get("items")):
				if not row.item_code in item_list:
					new_items.append(row)
			quote.items = new_items
			quote.flags.ignore_mandatory = True
			quote.save()
			if not len(quote.get("items", [])):
				# frappe.delete_doc("Quotation", quote_id)
				# frappe.db.sql("delete from tabQuotation where name = '{}'".format(quote_id))
				quote.flags.ignore_mandatory = True
				# msg = "Deleted all items"
				response["message"] = "כל המוצרים הוסרו בהצלחה"
				frappe.local.response["http_status_code"] = 200
			else:
				response = get_cart_details(quote_id)
			frappe.db.commit()
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		# msg = "Unable to Delete Quote Item"
		response["message"] = "אין אפשרות להסיר מוצר מהרשימה"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: delete_cart_item")
	finally:
		return response


@frappe.whitelist()
def bulk_add_to_cart(quote_id, items):
	"""
	:params
		quote_id: quotation
		items: [{
			"item_code": "",
			"qty": ,
		}]
	"""
	try:
		response = frappe._dict()
		items = json.loads(items)
		if not frappe.db.exists("Quotation", quote_id):
			# msg = "Quotation not found"
			response["message"] = "הצעת המחיר לא נמצאה"
			frappe.local.response['http_status_code'] = 404
		else:
			quote = frappe.get_doc("Quotation", quote_id)
			quote.mode_of_order = "Website"
			quote.selling_price_list = "Meuhedet"
			for i in items:
				i = get_item_details(quote, i)
				existing_item = False
				for row in quote.get("items"):
					# update item row
					if row.get("item_code") == i.get("item_code"):
						existing_item = True
						updatd_qty = row.get("qty") + i.get("qty")
						i["qty"] = int(updatd_qty)
						row.update(i)
				# add new item
				if not existing_item:
					quote.append("items", i)
			quote.save()
			frappe.db.commit()
			response = get_cart_details(quote.name)
		return "Successful"
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		# msg = "Quotation Update failed"
		response["message"] = "שגיאה בעדכון הבקשה להצעה"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: bulk_add_to_cart")
	finally:
		return response

def get_item_details(quote, items):
	try:
		args = frappe._dict({
			"customer": quote.party_name,
			"customer_group": frappe.db.get_value("Customer", quote.party_name, "customer_group"),
			"currency": quote.currency,
			"company": "PlayFunction",
			"transaction_date": frappe.utils.today(),
			"price_list": quote.selling_price_list,
			"ignore_pricing_rule": 0,
			"conversion_rate": 1,
			"plc_conversion_rate": 1,
			"doctype": "Quotation",
			"name": None,
			"order_type": "Sales",
			"item_code": items.get("item_code")
		})

		item_details = get_pricing_details(args)
		items["price_list_rate"] = item_details.get("price_list_rate")
		items["margin_type"] = item_details.get("margin_type")
		items["discount_percentage"] = item_details.get("discount_percentage")
		items["description"] = item_details.get("description", "WebAPI")
		return items
	except Exception as e:
		return items