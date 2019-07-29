import frappe
import json
from frappe import _
from frappe.utils import validate_email_add


@frappe.whitelist(allow_guest=True)
def login(data):
	""":param data: {
		"usr": "tripti.s@indictranstech.com",
		"pwd": "admin@123"
		}
	"""
	user_data = json.loads(data)
	try:
		if user_data.get("usr") and user_data.get("pwd"):
			user = frappe.db.exists("User", user_data.get("usr"))
			if user:
				frappe.clear_cache(user = user)
				frappe.local.login_manager.authenticate(user,user_data["pwd"])
				frappe.local.login_manager.post_login()
				frappe.response["sid"] = frappe.session.sid
				frappe.response["email"] = frappe.session.user
				frappe.response["message"] = "Logged In"
				frappe.response["status_code"] = 200
				frappe.local.response["http_status_code"] = 200
			else:
				frappe.response["message"] = _("Invalid User or Email Id")
				frappe.response["status_code"] = 404
				frappe.local.response['http_status_code'] = 404
		else:
			frappe.response["status_code"] = 422
			frappe.response["message"] = _("Invalid login credentials")
			frappe.local.response['http_status_code'] = 422
	except frappe.AuthenticationError,e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		response["message"] = "Unable to Login."
		frappe.log_error(message=frappe.get_traceback() , title="Website API: login")
	
@frappe.whitelist()
def logout(usr):
	"""
		Logged out from the browser
	"""
	try:
		if usr:
			if frappe.db.exists("User", usr):
				frappe.local.login_manager.logout(usr)
				frappe.db.commit()
				frappe.response["message"] = _("You have been successfully logged out")
				frappe.response["status_code"] = 200
				frappe.local.response["http_status_code"] = 200
			else:
				frappe.response["message"] = ("User Not Found")
				frappe.response["status_code"] = 404
				frappe.local.response["http_status_code"] =  404
		else:
			frappe.response["message"] = ("Invalid logout user")
			frappe.response["status_code"] = 422
			frappe.local.response["http_status_code"] =  422
	except Exception, e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.response["status_code"] = http_status_code
		response["message"] = "Unable to Logout."
		frappe.local.response["http_status_code"] = http_status_code
		frappe.log_error(message=frappe.get_traceback() , title="Website API: logout")