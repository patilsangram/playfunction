import frappe
import requests
import json
from frappe import _


@frappe.whitelist(allow_guest=True)
def ping():
	return "Pong"


#LOGIN API
@frappe.whitelist(allow_guest=True)
def login(usr,pwd):
	"""
		:param usr: username or email_id
		:param pwd: password
	"""
	
	try:
		response = frappe._dict({})
		if usr and pwd:
		
				frappe.local.login_manager.authenticate(usr,pwd)
				frappe.local.login_manager.post_login()
				frappe.response["sid"] = frappe.session.sid
				frappe.response["message"] = "Logged In"
				frappe.response["status_code"] = 200
		else:
				frappe.response["message"] = "Invalid Email Id"
				frappe.response["status_code"] = 404
		
	except frappe.AuthenticationError,e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.response["status_code"] = http_status_code


#FORGOT_PASSWORD API
@frappe.whitelist(allow_guest=True)
def forgot_password(usr):
	if usr=="Administrator":
		return 'not allowed'

	try:
		usr = frappe.get_doc("User", usr)
		if not usr.enabled:
			return 'disabled'

		usr.validate_reset_password()
		usr.reset_password(send_email=True)

		return frappe.msgprint(_("Password reset instructions have been sent to your email"))

	except frappe.DoesNotExistError:
		frappe.clear_messages()
		return 'not found'



#LOGOUT API
@frappe.whitelist(allow_guest=True)
def logout(usr,pwd):
		frappe.local.login_manager.logout()
		frappe.db.commit()
		frappe.response["message"] = "Logged out"










		
		

