import frappe
import json
from frappe import _
from frappe.utils import random_string, get_url
from frappe.utils.password import update_password as _update_password

@frappe.whitelist(allow_guest=True)
def login(data):
	"""
		data: {
			'usr': 'test@gmail.com',
			'pwd': 'admin@123'
		}
	"""
	user_data = json.loads(data)
	try:
		response = frappe._dict({}) 
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
	"""data: {
		'usr': 'test@gmail.com'
	}"""
	try:
		args = json.loads(data)
		response = frappe._dict({})
		user = frappe.db.exists("User", args.get("usr"))
		if user :
			user = frappe.get_doc("User", user)
			key = random_string(32)
			user.db_set("reset_password_key", key)
			link = get_url("/update-password?key=" + key)
			# user.password_reset_mail(link)
			response.key = key
			# response.message = _("Password reset instructions have been sent to your email")
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
	"""
		data: {
			'usr': 'test@gmail.com',
			'key': 'AR2xs49BkdNPUmBnfjHCou6QAOxx7wFj',
			'new_password': 'test@1234',
			'old_password': 'test@12'
		}
	"""
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

@frappe.whitelist(allow_guest=True)
def registration(data):
	"""
		data:{
			'email': 'test@gmail.com',
			'first_name': 'tripti',
			'last_name':'sharma',
			'password':' 'admin@123',
			'mobile_no':'9999999999'
		}
	"""
	try:
		response = frappe._dict({})
		args = json.loads(data)	
		user = frappe.db.exists("User", args.get("email"))
		if user:
			response["status_code"] = 200
			response["message"] = "User Already Registered"
			frappe.local.response['http_status_code'] = 200
		else:
			user_doc = frappe.new_doc("User")
			user_doc.email = args.get("email")
			user_doc.first_name = args.get("first_name")
			user_doc.last_name = args.get("last_name")
			user_doc.mobile_no = args.get("mobile_no")
			user_doc.enabled = 0
			user_doc.new_password = args.get("password")
			user_doc.send_welcome_email = 0
			user_doc.save(ignore_permissions = True)
			if user_doc:
				key = random_string(32)
				user_doc.db_set("reset_password_key", key)
				send_mail(user_doc.name,key)
				response.message = _("User created with Email Id {} Please check Email for Verification".format(user_doc.name))
				response["status_code"] = 200
				frappe.local.response['http_status_code'] = 200
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response.status_code = http_status_code
		response["message"] = "Registration failed"
		frappe.local.response["http_status_code"] = http_status_code
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: registration")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def send_mail(email,key=None):
	"""
		used to send access key
	"""
	try:
		user = frappe.db.exists("User", email)
		if user:
			subject = "Access Key"
			content = """ This is your access key {} """.format(key)
			frappe.sendmail(
				recipients = email, 
				sender = frappe.session.user, 
				subject = subject,
				message = content,
				delayed = 1)
	except Exception as e:
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: registration -send_mail")

@frappe.whitelist(allow_guest=True)
def verify_mail(data):
	"""
		data:{
			'email': 'test@gmail.com',
			'key':'KB7Y2OBU0iuhgulTbNCf8xmqxsGOAUC5'
		}
		enables user through key
	"""
	try:
		response = frappe._dict({})
		args = json.loads(data)	
		if frappe.db.exists("User", args.get("email")) and args.get("key"):
			user = frappe.db.get_value("User", {"reset_password_key":args.get("key")})
			if user == args.get("email"):
				user_doc = frappe.get_doc("User",args.get("email"))
				user_doc.enabled = 1
				user_doc.save(ignore_permissions = True)
				response.message = ("Email Verified")
				response["status_code"] = 200
				frappe.local.response['http_status_code'] = 200
			else:
				response.message = _("Invalid Access Key")
				response.status_code = 417
				frappe.local.response['http_status_code'] = 417
		else:
			response.message = ("Invalid User")
			response["status_code"] = 404
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: Verify Mail")
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Mail Verification failed"
	finally:
		return response

@frappe.whitelist()
def make_customer(data):
	"""
	data: {
		address_line1:
		address_line2:
		country:
		city:
		pincode:
	}
	"""
	try:
		response = frappe._dict()
		args = json.loads(data)
		user= frappe.get_doc("User",frappe.session.user)
		#check customer exists or not for the current user
		customer = frappe.db.get_value("Customer",{'user':user.name},"name")
		if customer:
			response["status_code"] = 200
			response["message"] = "Customer already exists."
			frappe.local.response['http_status_code'] = 200
		else:
			customer = frappe.new_doc("Customer")
			customer.customer_name= user.full_name
			customer.email_id= user.email
			customer.mobile_no = user.mobile_no
			customer.customer_type = "Individual"
			customer.address_line1 = args.get("address_line1")
			customer.address_line2 = args.get("address_line2")
			customer.country = args.get("country")
			customer.city = args.get("city")
			customer.pincode = args.get("pincode")
			customer.user = user.email 
			customer.save(ignore_permissions= True)
			frappe.db.commit()
			response["status_code"] = 200
			response["message"] = "Customer successfully created."
			frappe.local.response['http_status_code'] = 200
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		response["message"] = "Customer creation failed"
	finally:
		return response