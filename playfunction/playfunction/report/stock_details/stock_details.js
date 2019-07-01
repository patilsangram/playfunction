// Copyright (c) 2016, Indictrans and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Details"] = {
	"filters": [
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier"
		},
		{
			"fieldname": "item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
	]
}
