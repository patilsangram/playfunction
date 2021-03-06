import frappe
from frappe import _
import json
from requests import request


def stock_availability():
	"""
		send mail to admin if sales order qty availble in stock
	"""
	def update_reserved_qty(bin_data, updates):
		for k, v in updates.items():
			if k in bin_data:
				old_reserved = bin_data[k]["reserved"]
				new_reserved = old_reserved + v
				bin_data[k]["reserved"] = new_reserved
		return bin_data

	try:
		stock_for_so = []
		query = """
			select so.name, so.customer, soi.item_code, (soi.qty - soi.delivered_qty) as qty
			from `tabSales Order` so left join `tabSales Order Item` soi
			on so.name = soi.parent
			where so.status not in ('Closed', 'Stopped') and so.docstatus = 1
			group by so.name, soi.item_code order by so.creation
		"""
		so_data = frappe.db.sql(query, as_dict=True)

		# formatting: sales_data => {"sales_order": [{"item_code": "qty"}]}
		sales_data = {}
		for so in so_data:
			if so.get("name") not in sales_data:
				sales_data[so.name] = [{so.item_code: so.qty}]
			else:
				existing = sales_data[so.name]
				existing.append({so.item_code:so.qty})
				sales_data[so.name] = existing

		# available stock
		bin_data = frappe.db.sql("""select item_code, sum(actual_qty) as actual_qty
			from `tabBin` group by item_code""")

		# {"item_code": {"bin_qty", "reserved"}}
		bin_qty = { b[0]:{"qty": b[1], "reserved": 0} for b in bin_data if b[1] > 0}

		# check sales order wise availability
		for so, items in sales_data.items():
			if not frappe.db.get_value("Sales Order", so, "stock_availability_mail"):
				item_qty = {}
				is_stock_available = True
				for item in items:
					item_code, qty = item.keys()[0], item.values()[0]
					if item_code in bin_qty:
						if qty <= bin_qty[item_code]["qty"] - bin_qty[item_code]["reserved"]:
							item_qty[item_code] = qty
						else:
							is_stock_available = False
							break
					else:
						is_stock_available = False
						break
				if is_stock_available:
					# update_bit_qty_reserved
					bin_qty = update_reserved_qty(bin_qty, item_qty)
					stock_for_so.append(so)
		if len(stock_for_so):
			stock_availability_mail(stock_for_so)
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title="Stock availability Scheduler failed")

def stock_availability_mail(sales_orders):
	"""send stock availability mail to playfunction admin"""
	try:
		admin_users = frappe.get_all('Has Role', filters = {
			'parenttype': 'User',
			'role': ('in', ['Playfunction Admin'])
		}, fields=['parent'])
		if not len(admin_users):
			return
		recipients = [ u.get("parent") for u in admin_users if u.get("parent") != "Administrator"]
		message = frappe.render_template("templates/includes/stock_availability_mail.html", {
			"sales_orders": sales_orders		
		})
		frappe.sendmail(recipients=recipients,
			subject=_("Stock availability"),
			message=message
		)
		so_tuple = "(" + ",".join("'{}'".format(so) for so in sales_orders) + ")"
		frappe.db.sql("update `tabSales Order` set stock_availability_mail=1 \
				where name in {}".format(so_tuple))
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title="Stock availability Scheduler failed")


@frappe.whitelist()
def check_payment_status():
	"""Scheduler method to check payment status of order(iCredit)"""
	try:
		orders = []
		error_log = {}
		fields = ["name", "sales_tokens"]
		filters = {
			"payment_status": ("in", ["Pending", "", None]),
			"docstatus": ("!=", 2),
			"mode_of_order": "Web"
		}
		due_orders = frappe.get_list("Sales Order", fields=fields, filters=filters)
		if len(due_orders):
			url = "https://testicredit.rivhit.co.il/API/PaymentPageRequest.svc/SaleDetails"
			headers = {"Content-Type": "application/json", "user-agent": "Playfunction App"}
			method = "POST"

			for order in due_orders:
				tokens = order.get("sales_tokens")
				sales_token = json.loads(tokens)["PrivateSaleToken"]
				data = {"SalePrivateToken": sales_token}
				response = request(method, url, data=json.dumps(data), headers=headers)
				# check payment status
				if response.status_code == 200:
					response = json.loads(response.text)
					if not response.get("status") and response.get("Amount") \
						and response.get("AuthNum"):
						# TODO: partial payment - response.get("Amount") != order amt
						frappe.db.set_value("Sales Order", order.get("name"), "payment_status", "Paid")
						frappe.db.commit()
				else:
					# update error log
					error_log[order.get("name")] = response.text
		if error_log.keys():
			frappe.error_log(message=json.dumps(error_log), title="Scheduler Event Failed")
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback() , title="Scheduler Event: check_payment_status")