import frappe
import json
from frappe import _

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

@frappe.whitelist(allow_guest=True)
def forgot_password(data):
	""":param data: {
			"usr": "test@gmail.com"
		}
	"""
	try:
		from frappe.utils import random_string, get_url
		args = json.loads(data)
		response = frappe._dict({})
		user = frappe.db.exists("User", args.get("usr"))
		if user :
			user = frappe.get_doc("User", user)
			key = random_string(32)
			user.db_set("reset_password_key", key)
			link = get_url("/update-password?key=" + key)
			user.password_reset_mail(link)
			response.key = key
			response.message = _("Password reset instructions have been sent to your email")
			response.status_code = 200
			frappe.local.response['http_status_code'] = 200
		else:
			response.message = _("Invalid User")
			response.status_code = 404
			frappe.local.response['http_status_code'] = 404
	except Exception, e:
		response["message"] = "Forgot Password failed"
		http_status_code = getattr(e, "http_status_code", 500)
		response.status_code = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		frappe.log_error(message=frappe.get_traceback() , title="Website API: forgot_password")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def update_password(data):
	""":param data: {
			"usr": "test@gmail.com",
			"key": "AR2xs49BkdNPUmBnfjHCou6QAOxx7wFj",
			"new_password": "test@1234",
			"old_password": "test@12"
		}
	"""
	from frappe.utils.password import update_password as _update_password
	try:
		args = json.loads(data)
		response = frappe._dict({})
		user = frappe.db.exists("User", args.get("usr"))
		if user:
			if args.get("key"):
				user = frappe.db.get_value("User", {"reset_password_key":args.get("key")})
				if not user:
					response.message = _("Password reset key is expired")
					response.status_code = 417
					frappe.local.response['http_status_code'] = 417
					return response
			elif args.get("old_password"):
				frappe.local.login_manager.check_password(user, args.get("old_password"))
			
			_update_password(user, args.get("new_password"))
			frappe.db.set_value("User", user, "reset_password_key", "")
			response.message = _("Password reset sucessfully")
			response.status_code = 200
			frappe.local.response['http_status_code'] = 200
		else:
			response.message = _("Invalid User")
			response.status_code = 404
			frappe.local.response['http_status_code'] = 404
	except Exception, e:
		http_status_code = getattr(e, "http_status_code", 500)
		response.status_code = http_status_code
		response["message"] = "Update Password failed"
		frappe.local.response["http_status_code"] = http_status_code
		frappe.log_error(message=frappe.get_traceback() , title="Website API: update_password")
	finally:
		return response