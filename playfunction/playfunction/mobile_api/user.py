import frappe
import requests
import json
from frappe import _


#TEST API
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

#UPDATE_PASSWORD API
@frappe.whitelist(allow_guest=True)
def update_password(new_password, logout_all_sessions=0, key=None, old_password=None):
	from frappe.utils.password import update_password as _update_password
	res = _get_user_for_update_password(key, old_password)
	if res.get('message'):
		return res['message']
	else:
		user = res['user']

	_update_password(user, new_password, logout_all_sessions=int(logout_all_sessions))

	user_doc, redirect_url = reset_user_data(user)

	# get redirect url from cache
	redirect_to = frappe.cache().hget('redirect_after_login', user)
	if redirect_to:
		redirect_url = redirect_to
		frappe.cache().hdel('redirect_after_login', user)

	frappe.local.login_manager.login_as(user)

	if user_doc.user_type == "System User":
		return "/desk"
	else:
		return redirect_url if redirect_url else "/"

# VERIFY OLD PASSWORD
def _get_user_for_update_password(key, old_password):
	
	if key:
		user = frappe.db.get_value("User", {"reset_password_key": key})
		if not user:
			return {
				'message': _("Cannot Update: Incorrect / Expired Link.")
			}

	elif old_password:
		# verify old password
		frappe.local.login_manager.check_password(frappe.session.user, old_password)
		user = frappe.session.user

	else:
		return

	return {
		'user': user
	}


def reset_user_data(user):
	user_doc = frappe.get_doc("User", user)
	redirect_url = user_doc.redirect_url
	user_doc.reset_password_key = ''
	user_doc.redirect_url = ''
	user_doc.save(ignore_permissions=True)

	return user_doc, redirect_url





#LOGOUT API
@frappe.whitelist(allow_guest=True)
def logout(usr,pwd):
		frappe.local.login_manager.logout()
		frappe.db.commit()
		frappe.response["message"] = "Logged out"







		
		

