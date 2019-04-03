# -*- coding: utf-8 -*-
# Copyright (c) 2019, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ItemSubcategory(Document):
	def validate(self):
		data=frappe.db.count('Item Subcategory', filters={'category': self.category, 'subcategory': self.subcategory})
		if data>0:
			frappe.throw("This pair is already exists")

