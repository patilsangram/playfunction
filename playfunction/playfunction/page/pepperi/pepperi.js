frappe.pages['pepperi'].on_page_load = function(wrapper) {
	new frappe.pepperi({
		$wrapper: $(wrapper)
	});
}

frappe.pepperi = Class.extend({
	init: function(opts) {
		this.$wrapper = opts.$wrapper
		this.render_layout();
	},

	render_layout: function() {
		this.$wrapper.empty();
		this.$wrapper.append(frappe.render_template("pepperi_home"));
	}
})
