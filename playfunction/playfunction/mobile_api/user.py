import frappe
import requests
import json
from frappe.utils import validate_email_add
from frappe import _


@frappe.whitelist(allow_guest=True)
def ping():
	return "Pong"



@frappe.whitelist(allow_guest=True)
def login(data):
	""":param data: {
			"usr": "yugandhara.b@indictranstech.com",
			"pwd": "admin@123"
		}
	"""
	user_data = json.loads(data)
	try:
		if user_data.get("usr") and user_data.get("pwd"):
			if user:
				frappe.clear_cache(user = user)
				frappe.local.login_manager.authenticate(user,user_data["pwd"])
				frappe.local.login_manager.post_login()
				frappe.response["sid"] = frappe.session.sid
				frappe.response["message"] = "Logged In"
				mobile_no = frappe.db.get_value('User',{"name":user_data.get("usr")},'mobile_no')
				if mobile_no:
					frappe.response["mobile_no"] = mobile_no
				frappe.response["status_code"] = 200

			else:
				frappe.response["message"] = "Invalid Email Id or Mobile no."
				frappe.response["status_code"] = 404
		else:
			raise frappe.throw(_("Invalid Input"))
	except frappe.AuthenticationError,e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.response["status_code"] = http_status_code

	




	