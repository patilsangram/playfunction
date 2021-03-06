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
				frappe.response["message"] = "מחובר/ת"
				frappe.response["status_code"] = 200
				quote_id, proposal_id = get_last_quote()
				frappe.response["quote_id"] = quote_id
				frappe.response["proposal_id"] = proposal_id
				frappe.local.response["http_status_code"] = 200
			else:
				# msg = "Invalid Username or Password"
				frappe.response["message"] = _("משתמש או דוא\"ל לא תקין")
				frappe.response["status_code"] = 404
				frappe.local.response['http_status_code'] = 404
		else:
			frappe.response["status_code"] = 422
			# msg = "Invalid credential"
			frappe.response["message"] = _("שם משתמש או סיסמא לא תקינים")
			frappe.local.response['http_status_code'] = 422
	except frappe.AuthenticationError as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.response["status_code"] = http_status_code
		frappe.local.response["http_status_code"] = http_status_code
		# ms = "Unable to login"
		response["message"] = "בעיה בהתחברות לחשבון"
		frappe.log_error(message=frappe.get_traceback() , title="Website API: login")

def get_last_quote():
	# return customer's last quotation (cart) & proposal ID
	quote_id = proposal_id = ""
	if frappe.session.user:
		customer = frappe.db.get_value("Customer",{'user': frappe.session.user},"name")
		if customer:
			quotations = frappe.get_all("Quotation", filters={
					"party_name": customer,
					"workflow_state": ["not in", ["Proposal"]],
					"docstatus": 0
				}, order_by="creation desc", limit=1)
			if len(quotations):
				quote_id = quotations[0].get("name")

			proposal_id = frappe.db.get_value("Quotation", {
				"party_name": customer,
				"workflow_state": "Proposal",
				"docstatus": 0
			}, "name", order_by="creation desc")
	return quote_id, proposal_id


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
				# msg ="You have been successfully logged out"
				frappe.response["message"] = _("התנתקת מהחשבון בהצלחה")
				frappe.response["status_code"] = 200
				frappe.local.response["http_status_code"] = 200
			else:
				# msg ="User does not exist."
				frappe.response["message"] = ("שם משתמש אינו קיים")
				frappe.response["status_code"] = 404
				frappe.local.response["http_status_code"] =  404
		else:
			frappe.response["message"] = ("Invalid logout user")
			frappe.response["status_code"] = 422
			frappe.local.response["http_status_code"] =  422
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.response["status_code"] = http_status_code
		# msg = "Unable to Logout"
		response["message"] = "אין אפשרות להתנתק מהחשבון"
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
			# msg = "Invalid User"
			response.message = _(" שם משתמש אינו קיים")
			response.status_code = 404
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		# msg = "Forgot Password failed"
		response["message"] = "שכחת את הסיסמא אינו תקף"
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
			'key': 'AR2xs49BkdNPUmBnfjHCou6QAOxx7wFj',Forgot Password failed
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
					# msg ="Password reset key is expired"
					response.message = _("פג תוקף סיסמא זמנית")
					response.status_code = 417
					frappe.local.response['http_status_code'] = 417
					return response
			elif args.get("old_password"):
				frappe.local.login_manager.check_password(user, args.get("old_password"))

			_update_password(user, args.get("new_password"))
			frappe.db.set_value("User", user, "reset_password_key", "")
			# msg = "Password reset sucessfully"
			response.message = _("הסיסמא שונתה בהצלחה!")
			response.status_code = 200
			frappe.local.response['http_status_code'] = 200
		else:
			# msg = "Invalid User"
			response.message = _(" שם משתמש לא קיים ")
			response.status_code = 404
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		response.status_code = http_status_code
		# msg = "Update Password Failed"
		response["message"] = "עדכון הסיסמא נכשל"
		frappe.local.response["http_status_code"] = http_status_code
		frappe.log_error(message=frappe.get_traceback() , title="Website API: update_password")
	finally:
		return response

@frappe.whitelist(allow_guest=True)
def registration(data):
	"""
		data:{
			'email': 'test@gmail.com',
			'first_name':'test',
			'last_name':'test',
			'password':test@123',
			'mobile_no':'99XXXXXXXX'
		}
	"""
	try:
		response = frappe._dict({})
		args = json.loads(data)
		user = frappe.db.exists("User", args.get("email"))
		if user:
			# msg = "User Already Registered"
			response["message"] = "המשתמש כבר רשום"
			frappe.local.response['http_status_code'] = 200
		else:
			# Mobile no validation
			existing_mobile_no = ""
			if args.get("mobile_no") and frappe.db.get_value("User",
				{"mobile_no": args.get("mobile_no")}, "name"):
				# msg = "Given Mobile No is linked with existing user."
				response["message"] = _("נתוני הטלפון הנייד לא מקושרים למשתמש הקיים")
				frappe.local.response['http_status_code'] = 417
			else:
				user_doc = frappe.new_doc("User")
				user_doc.email = args.get("email")
				user_doc.first_name = args.get("first_name")
				user_doc.last_name = args.get("last_name")
				user_doc.mobile_no = args.get("mobile_no")
				user_doc.enabled = 1
				user_doc.new_password = args.get("password")
				user_doc.send_welcome_email = 0
				user_doc.flags.ignore_permissions = True
				user_doc.save()
				if user_doc:
					#key = random_string(32)
					#user_doc.db_set("reset_password_key", key)
					#send_mail(user_doc.name,key)
					# msg = "User created with Email Id {} Please check Email for Verification"

					# add roles
					if frappe.db.exists("Role", "Playfunction Customer"):
						user_doc.add_roles("Playfunction Customer")
						user_doc.save()

						# make customer
						customer = frappe.new_doc("Customer")
						customer.customer_name = user_doc.full_name
						customer.user = user_doc.email
						customer.flags.ignore_permissions = True
						customer.flags.ignore_mandatory = True
						customer.save()

						#add user permission for customer
						user_permission = frappe.new_doc("User Permission")
						user_permission.user = user_doc.name
						user_permission.allow = "Customer"
						user_permission.for_value = customer.name
						user_permission.apply_to_all_documents = True
						user_permission.ignore_permissions = True
						user_permission.save()

					response.message = _("משתמש נוצר עם מזהה דוא\"ל {} אנא בדוק אם יש אימות בדוא\"ל שלך".format(user_doc.name))
					frappe.local.response['http_status_code'] = 200
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		# msg = "Registration failed"
		response["message"] = "ההרשמה נכשלה"
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
			# msg = "Access Key"
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

@frappe.whitelist()
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
				user_doc.flags.ignore_permissions = True
				user_doc.save()
				# msg = "Email Verified"
				response.message = ("דוא\"ל אומת בהצלחה !")
				response["status_code"] = 200
				frappe.local.response['http_status_code'] = 200
			else:

				response.message = _("Invalid Access Key")
				response.status_code = 417
				frappe.local.response['http_status_code'] = 417
		else:
			# msg ="Invalid User"
			response.message = ("שם משתמש לא קיים")
			response["status_code"] = 404
			frappe.local.response['http_status_code'] = 404
	except Exception as e:
		frappe.log_error(message = frappe.get_traceback() , title = "Website API: Verify Mail")
		http_status_code = getattr(e, "http_status_code", 500)
		response["status_code"] = http_status_code
		frappe.local.response['http_status_code'] = http_status_code
		# msg = "Mail Verification failed"
		response["message"] = "בעיה באימות דוא\"ל"
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
			# msg = "Customer already exists."
			response["message"] = "שם משתמש כבר קיים"
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
			customer.flags.ignore_permissions = True
			customer.save()
			frappe.db.commit()
			# msg = "Customer successfully created"
			response["message"] = ".הלקוח נוצר בהצלחה"
			frappe.local.response['http_status_code'] = 200
	except Exception as e:
		http_status_code = getattr(e, "http_status_code", 500)
		frappe.local.response['http_status_code'] = http_status_code
		# msg = "Customer creation failed"
		response["message"] = "שגיאה ביצירת פרטי לקוח"
	finally:
		return response