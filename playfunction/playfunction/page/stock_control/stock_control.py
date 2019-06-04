import frappe
import json
from frappe import _

@frappe.whitelist()
def get_dashboard_data(filters):
	try:
		filters = json.loads(filters)
		print("---------------------------", filters)
		return "Success"
	except Exception as e:
		frappe.msgprint(_("Something went wrong while fetching data."))