frappe.pages['stock-control'].on_page_load = function(wrapper) {
	new frappe.StockControl({
		$wrapper: $(wrapper)
	});
	frappe.breadcrumbs.add("PlayFunction");
}

frappe.StockControl = Class.extend({
	init: function(opts) {
		this.$wrapper = opts.$wrapper
		this.page = opts.$wrapper.page
		this.make();
	},

	make: function() {
		this.$wrapper.empty();
		this.$wrapper.append(frappe.render_template("stock_control_layout"));
		this.init_filter();
		this.fetch_dashboard_data();
	},

	init_filter: function() {
		const me = this;
		this.item = frappe.ui.form.make_control({
			parent: this.$wrapper.find(".item"),
			df: {
				fieldtype: "Link",
				options: "Item",
				fieldname: "item",
				label: __("Item"),
				change: function(){
					me.fetch_dashboard_data();
				}
			},
			render_input: true,
		});

		this.customer = frappe.ui.form.make_control({
			parent: this.$wrapper.find(".customer"),
			df: {
				fieldtype: "Link",
				options: "Customer",
				fieldname: "customer",
				label: __("Customer"),
				change: function(){
					me.fetch_dashboard_data();
				}
			},
			render_input: true,
		});

		this.supplier = frappe.ui.form.make_control({
			parent: this.$wrapper.find(".supplier"),
			df: {
				fieldtype: "Link",
				options: "Supplier",
				fieldname: "supplier",
				label: __("Supplier"),
				change: function(){
					me.fetch_dashboard_data();
				}
			},
			render_input: true,
		});

		this.stock = frappe.ui.form.make_control({
			parent: this.$wrapper.find(".stock-fil"),
			df: {
				fieldtype: "Select",
				options: ['','Equals','Not Equals','In','Not In','Between',
					'Greater Than','Greater Than or Equal To','Less Than','Less Than or Equal To'],
				fieldname: "stock",
				label: __("Stock"),
				change: function(){
					me.fetch_dashboard_data();
				}
			},
			render_input: true,
		});

		this.stock_qty = frappe.ui.form.make_control({
			parent: this.$wrapper.find(".stock-qty"),
			df: {
				fieldtype: "Data",
				fieldname: "stock_qty",
				label: __("Stock Qty"),
				description: __("e.g. Between - 15, 20"),
				change: function(){
					me.fetch_dashboard_data();
				}
			},
			render_input: true,
		});
	},

	fetch_dashboard_data: function() {
		var me = this;
		var filters = {}
		var filters_col = ["item", "customer", "supplier", "stock", "stock_qty"]

		$.each(filters_col, function(idx, fil) {
			var filter_val = me[fil].$input.val();
			if (filter_val) {
				filters[fil] = filter_val
			}
		})

		frappe.call({
			method: "playfunction.playfunction.page.stock_control.stock_control.get_dashboard_data",
			args: {"filters": filters},
			callback: function(r) {
				$('.item-tbl').html(frappe.render_template("item_details", {"data": r.message}))
				me.check_all();
				me.check_item();
				me.validate_order_qty();
				me.open_record();
				me.open_stock_ledger();
				me.place_order();
				me.request_for_quote();
			}
		})
	},

	place_order: function() {
		var me = this;
		$('.place-order').on("click", function() {
			var data = me.get_checked_items()
			if (data) {
				me.make_transaction_record("Purchase Order", data)
			}
		})
	},

	request_for_quote: function() {
		var me = this;
		$('.request-for-quote').on("click", function(){
			var data = me.get_checked_items()
			if (data) {
				me.make_transaction_record("Request for Quotation", data)
			}
		})
	},

	check_all: function() {
		var me = this;
		$('.all-check').on("click", function() {
			$(".check-item").prop('checked', $(this).prop('checked'));
		})
	},

	check_item: function() {
		// uncheck if supplier is not present
		var me = this;
		$('.check-item').on("click", function() {
			if($(this).prop("checked")) {
				var supplier = $(this).closest('tr').find('.supp').attr('data-dn').trim();
				var item = $(this).attr("data-item");
				if (!supplier) {
					$(this).prop("checked", false);
					frappe.msgprint(__("Supplier is missing for "+"<b>"+(item)+"</b>"))
				}
			}
		})
	},

	validate_order_qty: function() {
		var me = this;
		$('.to-be-ordered').on("change", function() {
			var val = $(this).val();
			if(val && val < 0) {
				$(this).val(0);
			}
		})
	},

	open_record: function() {
		var me = this;
		$('.dt-link').on("click", function() {
			var dt = $(this).attr('data-dt').trim();
			var dn = $(this).attr('data-dn').trim();
			if(dt && dn) {
				frappe.set_route("Form", dt, dn);
			}
		})
	},

	open_stock_ledger: function() {
		var me = this;
		$('.stock-report-link').on("click", function() {
			var item_code = $(this).closest('tr').find('.i-code-td').attr('data-dn').trim();
			frappe.route_options = {"item_code": item_code}
			frappe.set_route("query-report", "Stock Ledger");
		})
	},

	get_checked_items: function() {
		// [{ "item_code": "ABC", "qty": 12, "supplier": "Bryan" }]
		var me = this;
		data = []
		$("input:checkbox[class=check-item]:checked").each(function () {
			var item_code = $(this).attr("data-item")
			var supplier = $(this).closest('tr').find('.supp').attr('data-dn').trim();
			var qty = $(this).closest('tr').find('.to-be-ordered').val();
			if (qty && supplier) {
				data.push({"item_code": item_code, "supplier": supplier, "qty": qty})
			}
			else {
				$(this).prop("checked", false);
			}
		})
		if(!data.length) {
			frappe.msgprint(__("Supplier & Qty required."))
			return false
		}
		return data
	},

	make_transaction_record: function(dt, data) {
		var me = this;
		frappe.call({
			method: "playfunction.playfunction.page.stock_control.stock_control.make_transaction_record",
			args: {"dt": dt, "data": data},
			callback: function(r) {
				if (!r.exc && r.message) {
					frappe.msgprint(__(dt+" Record Created Successfully..."))
					me.fetch_dashboard_data();
				}
			}
		})
	}
})