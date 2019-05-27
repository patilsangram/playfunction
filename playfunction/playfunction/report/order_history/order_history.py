# Copyright (c) 2013, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = [
		{
			'fieldname': 'name',
			'label': 'Order No.',
			'fieldtype': 'Link',
			'options': 'Sales Order'
		},
		{
			'fieldname': 'customer',
			'label': 'Customer',
			'fieldtype': 'Link',
			'options': 'Customer'
		},
		{
			'fieldname': 'transaction_date',
			'fieldtype': 'Date',
			'label': 'Order Date'
		},
		{
			'fieldname': 'grand_total',
			'fieldtype': 'Currency',
			'label': 'Order Value'
		},
		{
			'fieldname': 'status',
			'fieldtype': 'Data',
			'label': 'Order Status'
		},
		{
			'fieldname': 'shipping_status',
			'fieldtype': 'Data',
			'label': 'Shipping Status'
		},
		{
			'fieldname': 'payment_status',
			'fieldtype': 'Data',
			'label': 'Payment Status'
		}
	]
	query = """
			select name, customer, transaction_date, grand_total, status, 
			'-' as shipping_status, '-' as payment_status
			from `tabSales Order`
		"""
	cond = " where 1=1"
	if filters.get('from_date') and filters.get('to_date'):
		cond += " and transaction_date >= '{0}' and transaction_date <= '{1}'".format(
			filters.get("from_date"), filters.get("to_date"))
	if filters.get("status"):
		cond += " and status = '{}'".format(filters.get("status"))
	data = frappe.db.sql(query + cond)
	return columns, data