import frappe
import json
from frappe import _

@frappe.whitelist()
def get_dashboard_data(filters):
	try:
		filters = json.loads(filters)
		filter_query = " where 1=1"

		if filters.get("item"):
			filter_query += " and stock_data.item_code = '{}'".format(filters.get("item"))

		if filters.get("customer"):
			filter_query += " and stock_data.customer = '{}'".format(filters.get("customer"))

		if filters.get("supplier"):
			filter_query += " and stock_data.supplier = '{}'".format(filters.get("supplier"))

		if filters.get("stock") and filters.get("stock_qty"):
			# stock filter e.g. between 100 and 200, not in (100, 200)
			cond_mapper = {"Equals": "=","Not Equals": "!=", "In": "in", "Not In": "not in",
				"Between": "between","Greater Than": ">", "Greater Than or Equal To": ">=",
				"Less Than": "<", "Less Than or Equal To": "<="}
			condition = cond_mapper.get(filters.get("stock"))
			cond_query = ""
			val_list = [ int(v.strip()) for v in filters.get("stock_qty").split(",") if v.strip().isdigit()]
			if len(val_list):
				if filters.get("stock") in ["In", "Not In"]:
					cond_query = "(" + ",".join("'{}'".format(i) for i in val_list) + ")"
				elif filters.get("stock") == "Between" and len(val_list) > 1:
					cond_query = "{} and {}".format(val_list[0], val_list[1])
				else:
					cond_query = val_list[0]
				filter_query += " and stock_data.stock {} {}".format(condition, cond_query)

		# sub query to handle stock filter/alias
		query = """
			select * from (select
				i.item_code, i.item_name, i.cost_price, i.supplier,
				i.supplier_item_name, q.party_name as customer, ifnull(sum(qi.qty), 0) as quote_qty,
				ifnull((soi.qty - soi.delivered_qty), 0) as pending_qty, ifnull(sum(bin.actual_qty), 0) as stock
			from
				tabItem i
			left join
				`tabQuotation Item` qi on qi.item_code = i.item_code
			left join
				`tabQuotation` q on qi.parent = q.name
			left join
				`tabSales Order Item` soi on soi.item_code = i.item_code
			left join
				`tabBin` bin on bin.item_code = i.item_code
			group by
				i.item_code, q.party_name) as stock_data
			{}
		""".format(filter_query)
		data = frappe.db.sql(query, as_dict=True)
		return data
	except Exception as e:
		frappe.msgprint(_("Something went wrong while fetching data."))
		return []

@frappe.whitelist()
def make_transaction_record(dt, data):
	try:
		data = json.loads(data)
		record_data = {}
		# supplier wise filter
		# format - {"supplier": {"item_code": "qty"}}
		for d in data:
			if d.get("supplier") in record_data:
				if d.get("item_code") in record_data[d.get("supplier")]:
					old_qty = record_data[d.get("supplier")].get(d.get("item_code"))
					record_data[d.get("supplier")][d.get("item_code")] =  old_qty + int(d.get("qty"))
				else:
					record_data[d.get("supplier")][d.get("item_code")] = int(d.get("qty"))
			else:
				record_data[d.get("supplier")] = {d.get("item_code"): int(d.get("qty"))}

		# record_creation
		if dt == "Purchase Order":
			return _make_purchase_order(record_data)
		else:
			return _make_request_for_quote(record_data)

	except Exception as e:
		frappe.msgprint(_("Something went wrong while creating {} - {}".format(dt, str(e))))
		return False

@frappe.whitelist()
def _make_purchase_order(data):
	try:
		po_nos = []
		for sup, itm in data.items():
			po = frappe.new_doc("Purchase Order")
			po.supplier = sup
			po.schedule_date = frappe.utils.today()
			for item, qty in itm.items():
				po.append("items", {
					"item_code": item,
					"qty": 	qty,
					"warehouse": frappe.db.get_value("Item Default", {"parent":item}, "default_warehouse")
				})
			po.set_missing_values()
			po.flags.ignore_mandatory = True
			po.save()
			po_nos.append(po.name)
		return po_nos
	except Exception as e:
		return False

@frappe.whitelist()
def _make_request_for_quote(data):
	try:
		req_for_quotes = []
		for sup, itm in data.items():
			doc = frappe.new_doc("Request for Quotation")
			doc.transaction_date = frappe.utils.today()
			doc.status = "Draft"
			doc.append("suppliers", {
				"supplier": sup,
				"supplier_name":sup
			})
			for item, qty in itm.items():
				doc.append("items", {
					"item_code": item,
					"qty": 	qty,
					"warehouse": frappe.db.get_value("Item Default", {"parent":item}, "default_warehouse")
				})
			doc.set_missing_values()
			doc.flags.ignore_mandatory = True
			doc.save()
			req_for_quotes.append(doc.name)
		return req_for_quotes
	except Exception as e:
		return False