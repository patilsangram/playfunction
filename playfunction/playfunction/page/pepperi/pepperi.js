frappe.pages['pepperi'].on_page_load = function(wrapper) {
	new frappe.pepperi({
		$wrapper: $(wrapper)
	});
}

frappe.pepperi = Class.extend({
	init: function(opts) {
		this.$wrapper = opts.$wrapper
		this.make();
	},

	make: function() {
		this.$wrapper.empty();
		this.$wrapper.append(frappe.render_template("pepperi_layout"));
		this.$header = this.$wrapper.find(".pepperi-header");
		this.$main = this.$wrapper.find(".pepperi-main");
		this.home();
		this.bind_events();
	},

	home: function() {
		this.$header.empty()
		this.$main.empty()
		this.$header.append(frappe.render_template("pep_header"))
		this.$main.append(frappe.render_template("pepperi_home"))
		this.bind_events();
	},

	bind_events: function() {
		var me = this;

		//redirect to home
		$('#btnMenuHome').click(function() {
			me.home();
		})

		// profile
		$('#cust-profile').click(function() {
			frappe.set_route("Form", "User", frappe.session.user);
		})

		//sign out
		$('#cust-signout').click(function() {
			return frappe.app.logout();
		})

		//order
		$('#make-order').click(function() {
			me.render_item_catalog();
		})

		//order history
		$('#order-history').click(function() {
			frappe.set_route("List", "Sales Order")
		})

		//order list
		$('#order-list').click(function() {
			frappe.set_route("List", "Sales Order")
		})

		//quotation history
		$('#quote-history').click(function() {
			frappe.set_route("List", "Quotation")
		})

		//quotation list
		$('#quote-list').click(function() {
			frappe.set_route("List", "Quotation")
		})
	},

	render_item_catalog: function() {
		var me = this;
		// fetch & render item group
		frappe.call({
			method: "playfunction.playfunction.page.pepperi.pepperi.get_item_groups",
			async: false,
			freeze: true,
			freeze_message: __("Please wait ..."),
			callback: function(r) {
				me.$main.empty()
				me.$main.append(frappe.render_template("item_catalog", {"data":r.message}))
				me.item_catalog_trigger();
			}
		})
	},

	item_catalog_trigger: function() {
		//item group/catalog trigger
		var me = this;
		$('.item_catlog').click(function() {
			var item_group = $(this).attr("data-item-cat")
			me.render_item_grid({'item_group': item_group})
		})
	},

	render_item_grid: function(filters) {
		var me = this;
		frappe.call({
			method: "playfunction.playfunction.page.pepperi.pepperi.get_items_and_categories",
			args: filters,
			callback: function(r) {
				me.$main.empty()
				me.$main.append(frappe.render_template("pepperi_item_list", {"data": r.message}))
			}
		})
	}
})
