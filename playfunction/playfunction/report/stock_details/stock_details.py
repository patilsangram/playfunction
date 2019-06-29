# Copyright (c) 2013, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = [
		{
			'fieldname': 'item_code',
			'label': 'Item Code',
			'fieldtype': 'Link',
			'options': 'Item'
		},
		{
			'fieldname': 'item_name',
			'label': 'Item Name',
			'fieldtype': 'Data',
		},
		{
			"fieldname": "supplier",
			"label": "Supplier",
			"fieldtype": "Link",
			"options": "Supplier"
		},
		{
			"fieldname": "supplier_item_code",
			"label": "Supplier Item Code",
			"fieldtype": "Data"
		},
		{
			"fieldname": "supplier_item_name",
			"label": "Supplier Item Name",
			"fieldtype": "Data"
		},
		{
			"fieldname": "cost_price",
			"label": "Cost Price",
			"fieldtype": "Currency"
		},
		{
			"fieldname": "stock",
			"label": "Stock",
			"fieldtype": "Int"
		},
		{
			"fieldname": "total_price",
			"label": "Total Price",
			"fieldtype": "Currency"
		}
	]

	condition = "where 1=1 "
	if filters.get("supplier"):
		condition += " and i.supplier = '%s'"%(filters.get("supplier"))

	if filters.get("item"):
		condition += " and i.item_code = '%s'"%(filters.get("item"))

	# stock_qty * cost_price = total_price
	data = frappe.db.sql("""select res.*, res.stock*res.cost_price as total_price from (
			select i.item_code, i.item_name, i.supplier, i.supplier_item_code, i.supplier_item_name,i.cost_price, 
			ifnull(sum(bin.actual_qty), 0) as stock
			from `tabItem` i left join `tabBin` bin on i.item_code = bin.item_code {}
			group by i.item_code) as res
		""".format(condition))
	return columns, data
