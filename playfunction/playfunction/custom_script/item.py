

from __future__ import unicode_literals
import frappe
from frappe import _


@frappe.whitelist()
def item_info(doctype, txt, searchfield, start, page_len, filters):
	data=frappe.db.sql("select subcategory from `tabItem Subcategory` where category='{0}'".format(filters.get('category')))
	return data