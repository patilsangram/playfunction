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

		localStorage.removeItem("items");
		localStorage.removeItem("filters");
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
			localStorage.setItem('item_group', JSON.stringify(item_group));
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
				me.$main.append(frappe.render_template("pepperi_item_list", {
					"data": r.message, "item_group": filters["item_group"], "total": 0}))
				$('.pepperi-content').html(frappe.render_template('scope_items', {"data": r.message}))
				me.search_item();
				me.show_item_details();
				me.image_view();
				me.unit_qty_change();
			}
		})
	},

	search_item: function() {
		var me = this;
		$('.search-btn').click(function() {
			var search_txt = $('.search_ip').val();
			if(search_txt) {
				frappe.msgprint(search_txt)
			}
		})

		$('.search-clr').click(function() {
			var search_txt = $('.search_ip').val();
			if(search_txt) {
				$('.search_ip').val("");
			}
		})
	},

	show_item_details: function() {
		var me = this;
		$('.ObjectMenu').click(function() {
			let item_code = $(this).attr("data-item")
			frappe.msgprint(item_code)
		})
	},

	image_view: function() {
		var me = this;
		$('.img-view').click(function() {
			let image =  $(this).attr("data-img")
			frappe.msgprint(image)
		})
	},

	unit_qty_change: function() {
		var me = this;
		// decrease-qty
		$('.qty-minus').click(function() {
			var qty = $(this).closest("div.gQs").find("input[name='UnitsQty']").val();
			if (qty && parseInt(qty) > 0) {
				var item_code = $(this).closest("div.gQs").attr("data-item");
				qty = parseInt(qty) - 1
				$(this).closest("div.gQs").find("input[name='UnitsQty']").val(qty);
				me.update_cart(item_code, qty);
			}
		})
		// increase-qty
		$('.qty-plus').click(function() {
			var qty = $(this).closest("div.gQs").find("input[name='UnitsQty']").val();
			qty = parseInt(qty) + 1
			var item_code = $(this).closest("div.gQs").attr("data-item");
			$(this).closest("div.gQs").find("input[name='UnitsQty']").val(qty);

			me.update_cart(item_code, qty);
		})
		// qty-change
		$('.unitqty').change(function() {
			var qty = parseInt($(this).val()) || 0;
			var item_code = $(this).closest("div.gQs").attr("data-item");
			$(this).closest("div.gQs").find("input[name='UnitsQty']").val(qty);
			me.update_cart(item_code, qty)
		})
	},

	update_cart: function(item_code, qty) {
		var items = JSON.parse(localStorage.getItem('items')) || {};
		if (qty == 0) {
			delete items[item_code]
		}
		else {
			items[item_code] = qty
		}
		localStorage.setItem('items', JSON.stringify(items));
		console.log(JSON.parse(localStorage.getItem('items')))
		//frappe.msgprint(repl("%(item)s - %(qty)s", {"item": item_code, "qty": qty}))
	}
})