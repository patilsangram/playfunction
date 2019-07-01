import frappe
import requests
import json
from frappe import _


@frappe.whitelist()
def ping():
	return "Pong"

@frappe.whitelist()
def login(data):
	""":param data: {
		 "usr": username or email_id
		 "pwd": password
	"""
	try:
		response = frappe._dict({})
		if data:
		
				frappe.local.login_manager.authenticate(data)
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

# @frappe.whitelist()
# def forgot_password(data):
# 	""":param data: {
# 			"usr": "tripti.s@indictrans.in"
# 		}
# 	"""
# 	try:
# 		from frappe.utils import random_string, get_url
# 		args = json.loads(data)
# 		response = frappe._dict({})
# 		user = check_email_id(args.get('usr'))
# 		if user:
# 			user = frappe.get_doc("User", user)
# 			key = random_string(32)
# 			# link = "".format(key, user.name)
# 			user.db_set("reset_password_key", key)
# 			# user.password_reset_mail(link)
# 			response.key = key
# 			# response.link = link
# 			response.message = "Password reset instructions have been sent to your email"
# 			response.status_code = 200
# 		else:
# 			response.message = "Invalid User"
# 			response.status_code = 404
# 	except Exception, e:
# 		response["message"] = "Unable to perform action: {}".format(str(e))
# 		response["status_code"] = getattr(e, "http_status_code", 500)
# 	finally:
# 		return response

# @frappe.whitelist()
# def forgot_password(usr):
# 	if usr == "Administrator":
# 		return 'Not Allowed'

# 	try:
# 		usr = frappe.get_doc("User", usr)
# 		if not usr.enabled:
# 			return 'User Disabled'

# 		usr.validate_reset_password()
# 		usr.reset_password(send_email=True)

# 		return frappe.msgprint(_("Password reset instructions have been sent to your email"))

# 	except frappe.DoesNotExistError:
# 		frappe.clear_messages()
# 		return 'not found'



# @frappe.whitelist()
# def update_password(new_password, logout_all_sessions=0, key=None, old_password=None):
# 	from frappe.utils.password import update_password as _update_password
# 	res = _get_user_for_update_password(key, old_password)
# 	if res.get('message'):
# 		return res['message']
# 	else:
# 		user = res['user']

# 	_update_password(user, new_password, logout_all_sessions=int(logout_all_sessions))

# 	user_doc, redirect_url = reset_user_data(user)

# 	# get redirect url from cache
# 	redirect_to = frappe.cache().hget('redirect_after_login', user)
# 	if redirect_to:
# 		redirect_url = redirect_to
# 		frappe.cache().hdel('redirect_after_login', user)

# 	frappe.local.login_manager.login_as(user)

# 	if user_doc.user_type == "System User":
# 		return "/desk"
# 	else:
# 		return redirect_url if redirect_url else "/"


# def _get_user_for_update_password(key, old_password):
	
# 	if key:
# 		user = frappe.db.get_value("User", {"reset_password_key": key})
# 		if not user:
# 			return {
# 				'message': _("Cannot Update: Incorrect / Expired Link.")
# 			}

# 	elif old_password:
# 		# verify old password
# 		frappe.local.login_manager.check_password(frappe.session.user, old_password)
# 		user = frappe.session.user

# 	else:
# 		return

# 	return {
# 		'user': user
# 	}


# def reset_user_data(user):
# 	user_doc = frappe.get_doc("User", user)
# 	redirect_url = user_doc.redirect_url
# 	user_doc.reset_password_key = ''
# 	user_doc.redirect_url = ''
# 	user_doc.save(ignore_permissions=True)

# 	return user_doc, redirect_url

# 		return 'Not Found'



@frappe.whitelist()
def logout(usr,pwd):
		frappe.local.login_manager.logout()
		frappe.response["message"] = "Logged out"






@frappe.whitelist(allow_guest=True)
def update_password(data):
	""":param data: {
			"usr": "test@gmail.com"/"+91 8888771413",
			"key": "AR2xs49BkdNPUmBnfjHCou6QAOxx7wFj",
			"new_password": "test@1234"
		}
	"""
	from frappe.utils.password import update_password as _update_password

	try:
		args = json.loads(data)
		user = check_email_id(args.get('usr'))
		response = frappe._dict({})
		if user:
			if args.get("key"):
				user = frappe.db.get_value("User", {"reset_password_key":args.get("key")})
				if not user:
					response.message = _("Password reset key is expired")
					response.status_code = 417
					return response
			elif args.get("old_password"):
				frappe.local.login_manager.check_password(user, args.get("old_password"))

			_update_password(user, args.get("new_password"))
			frappe.db.set_value("User", user, "reset_password_key", "")
			response.message = "Password reset sucessfully"
			response.status_code = 200
		else:
			response.message = "Invalid User"
			response.status_code = 404
	except Exception, e:
		response["message"] = "Unable to perform action: {}".format(str(e))
		response["status_code"] = getattr(e, "http_status_code", 500)
	finally:
		return response

		
		


