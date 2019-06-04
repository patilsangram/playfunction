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
		var me = this;
		me.from_date = frappe.ui.form.make_control({
			parent: me.$wrapper.find(".from_date"),
			df: {
				fieldtype: "Date",
				fieldname: "from_date",
				change: function(){
					me.fetch_dashboard_data();
				}
			},
			only_input: true,
		});
		me.from_date.refresh();

		me.to_date = frappe.ui.form.make_control({
			parent: me.$wrapper.find(".to_date"),
			df: {
				fieldtype: "Date",
				fieldname: "to_date",
				change: function(){
					me.fetch_dashboard_data();
				}
			},
			only_input: true,
		});
		me.to_date.refresh();

		me.item = frappe.ui.form.make_control({
			parent: me.$wrapper.find(".item"),
			df: {
				fieldtype: "Link",
				options: "Item",
				fieldname: "item",
				change: function(){
					me.fetch_dashboard_data();
				}
			},
			only_input: true,
		});
		me.item.refresh();

		me.customer = frappe.ui.form.make_control({
			parent: me.$wrapper.find(".customer"),
			df: {
				fieldtype: "Link",
				options: "Customer",
				fieldname: "customer",
				change: function(){
					me.fetch_dashboard_data();
				}
			},
			only_input: true,
		});
		me.customer.refresh();
	},

	fetch_dashboard_data: function() {
		var me = this;
		var filters = {"name": "xyz"}

		var d = $('.filter-col')
		$.each(d, function(idx, fil) {
			console.log(idx, ":", fil)
		})

		frappe.call({
			method: "playfunction.playfunction.page.stock_control.stock_control.get_dashboard_data",
			args: {"filters": filters},
			callback: function(r) {
				$('.dashboard-body').html(frappe.render_template("item_details"))
				console.log(r.message)
			}
		})
	}
})