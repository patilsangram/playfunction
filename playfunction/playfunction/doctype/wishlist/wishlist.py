# -*- coding: utf-8 -*-
# Copyright (c) 2019, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class Wishlist(Document):
	def validate(self):
		update_amount(self)

def update_amount(self):
	for i in self.get("items"):
		i.amount = flt(i.qty) * flt(i.rate)