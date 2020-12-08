# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "PlayFunction",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("PlayFunction")
		},
		{
			"module_name": "System Pepperi",
			"color": "#2ecc71",
			"icon": "octicon octicon-rocket",
			"type": "page",
			"link": "pepperi",
			"label": _("System Pepperi")
		},
		{
			"module_name": "Stock Control",
			"color": "#106096",
			"icon": "octicon octicon-graph",
			"type": "page",
			"link": "stock-control",
			"label": _("Stock Control")
		},
		{
			"module_name": "Pepperi",
			"color": "#106096",
			"icon": "octicon octicon-graph",
			"type": "page",
			"link": "pepperi",
			"label": _("Pepperi Page")
		}
	]
