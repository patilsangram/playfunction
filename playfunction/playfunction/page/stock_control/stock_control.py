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
				i.item_code, i.item_name, i.cost_price, i.supplier_list as supplier,
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
		data = frappe.db.sql(query, as_dict=True, debug=1)
		return data
	except Exception as e:
		frappe.msgprint(_("Something went wrong while fetching data."))
		return []