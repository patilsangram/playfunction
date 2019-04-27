from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Item"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Item",
					"description": _("Item")
				},
				{
					"type": "doctype",
					"name": "Item Group",
					"description": _("Item Group")
				},
				{
					"type": "doctype",
					"name": "Item Category",
					"description": _("Item Category")
				},
				{
					"type": "doctype",
					"name": "Item Subcategory",
					"description": _("Item Subcategory")
				},
				{
					"type": "doctype",
					"name": "Price List",
					"description": _("Price List")
				},
				{
					"type": "doctype",
					"name": "Item Price",
					"description": _("Item Price")
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Stock Balance",
					"doctype": "Stock Ledger Entry"
				},
			]
		},
		{
			"label": _("Selling"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Quotation",
					"description": _("Quotation."),
				},
				{
					"type": "doctype",
					"name": "Sales Order",
					"description": _("Sales Order."),
				},
				{
					"type": "doctype",
					"name": "Sales Invoice",
					"description": _("Sales Invoice."),
				},
				{
					"type": "doctype",
					"name": "Customer",
					"description": _("Customer."),
				},
				{
					"type": "page",
					"name": "pepperi",
					"label": _("Pepperi"),
					"description": _("Point of Sale")
				},
			]
		},
		{
			"label": _("Buying"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Purchase Order",
					"description": _("Purchase Orders given to Suppliers."),
				},
			]
		},
	]
