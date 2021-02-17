import frappe

@frappe.whitelist()
def copy_item_price(doc, method):
	# automatically copy/update item price from Standard Selling
	# to Meuhedet Price List
	try:
		if doc.price_list == "Standard Selling":
			is_exist = frappe.db.get_value("Item Price", {
					"item_code": doc.item_code,
					"price_list": "Meuhedet",
					"selling": 1
				})
			if is_exist:
				item_price = frappe.get_doc("Item Price", is_exist)
				item_price.update({
					"price_list_rate": doc.price_list_rate,
					"note": "Copy/Updated from Standard Selling"
				})
			else:
				item_price = frappe.new_doc("Item Price")
				item_price.update({
					"price_list": "Meuhedet",
					"price_list_rate": doc.price_list_rate,
					"item_code": doc.item_code,
					"item_name": doc.item_name,
					"note": "Copy/Updated from Standard Selling"
				})
			item_price.flags.ignore_permissions = True	
			item_price.save()
	except Exception as e:
		pass