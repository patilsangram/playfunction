frappe.pages['stock-control'].on_page_load = function(wrapper) {
	new frappe.StockControl({
		$wrapper: $(wrapper)
	});
	frappe.breadcrumbs.add("PlayFunction");
}

frappe.StockControl = Class.extend({
	init: function(opts) {
		this.$wrapper = opts.$wrapper
		this.make();
	},

	make: function() {
		this.$wrapper.empty();
		this.$wrapper.append(frappe.render_template("stock_control_layout"));
	}
})