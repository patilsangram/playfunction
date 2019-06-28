from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Master"),
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
			"label": _("CRM"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Lead",
					"description": _("Lead")
				},
				{
					"type": "doctype",
					"name": "Customer",
					"description": _("Customer")
				},
				{
					"type": "doctype",
					"name": "Contact",
					"description": _("Contact")
				},
				{
					"type": "doctype",
					"name": "Address",
					"description": _("Address")
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
					"name": "Supplier",
					"description": _("Supplier."),
				},
				{
					"type": "doctype",
					"name": "Request for Quotation",
					"description": _("Request for Quotation."),
				},
				{
					"type": "doctype",
					"name": "Purchase Order",
					"description": _("Purchase Orders given to Suppliers."),
				},
				{
					"type": "doctype",
					"name": "Purchase Receipt",
					"description": _("Purchase Receipt."),
				},
				{
					"type": "doctype",
					"name": "Purchase Invoice",
					"description": _("Purchase Invoice."),
				},
				{
					"type": "doctype",
					"name": "Payment Entry",
					"description": _("Payment Entry."),
				},
				{
					"type": "page",
					"name": "stock-control",
					"label": _("Stock Control"),
					"description": _("Stock Control")
				},
			]
		},
		{
			"label": _("Account"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "report",
					"name": "Accounts Receivable",
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounts Payable",
					"doctype": "Purchase Invoice",
					"is_query_report": True
				},
				{
					"type": "doctype",
					"name": "Sales Invoice",
					"description": _("Sales Invoice."),
				},
				{
					"type": "doctype",
					"name": "Purchase Invoice",
					"description": _("Purchase Invoice."),
				}
			]
		},
		{
			"label": _("Stock"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "report",
					"name": "Stock Ledger",
					"is_query_report": True,
					"description": _("Stock Transactions")
				},
				{
					"type": "report",
					"name": "Stock Details",
					"doctype": "Catalog",
					"is_query_report": True
				}
			]
		}
	]
