// Copyright (c) 2016, Indictrans and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Order History"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			'reqd': 1,
			"default": frappe.datetime.add_days(frappe.datetime.nowdate(), -30)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			'reqd': 1,
			"default": frappe.datetime.nowdate()
		},
		{
			"fieldname": "grand_total",
			"label": "Order Value",
			"fieldtype": "Currency"
		},
		{
			"fieldname": "status",
			"label": "Order Status",
			"fieldtype": "Select",
			"options": "\nDraft\nTo Deliver and Bill\nTo Bill\nTo Deliver\nCompleted\nCancelled\nClosed"
		},
		{
			"fieldname": "shipping_status",
			"label": "Shippin Status",
			"fieldtype": "Select",
			"options": "\nFully Shipped\nNot Shipped\nPartially Shipped",
		},
		{
			"fieldname": "payment_status",
			"label": "Payment Status",
			"fieldtype": "Select",
			"options": "\nDue\nInvoice Sent\nPaid"
		},
	]
}
