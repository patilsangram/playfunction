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
		this.cur_page = ""
		this.home();
		this.bind_events();
	},

	home: function() {
		this.$header.empty()
		this.$main.empty()
		this.$header.append(frappe.render_template("pep_header"))
		this.$main.append(frappe.render_template("pepperi_home"))
		this.cur_page = "pepperi_home"
		this.bind_events();

		localStorage.removeItem("items");
		localStorage.removeItem("filters");
		localStorage.removeItem("search_txt");
		localStorage.removeItem("category");
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
				me.cur_page = "Item Catalog"
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
			localStorage.setItem('item_group', item_group);
			me.render_item_grid()
		})
	},

	render_item_grid: function(update_grid=false) {
		// TODO: store filters in localStorage, pass it as filters e.g. item_group, categories
		//filters = {"item_group": "Products", "category": {"Collection": ["Vintage"]}, "search_txt": "ada"}
		var me = this;
		filters = me.get_localstorage_data()
		frappe.call({
			method: "playfunction.playfunction.page.pepperi.pepperi.get_items_and_categories",
			args: {"filters": filters},
			callback: function(r) {
				let localdata = JSON.parse(localStorage.getItem("items")) || {}
				if(!update_grid) {
					me.$main.empty()
					me.cur_page = "Grid View"
					me.$main.append(frappe.render_template("pepperi_item_list", {
						"data": r.message, "item_group": filters["item_group"], "total": 0}))
					$('.pepperi-content').html(frappe.render_template('scope_items', 
						{"data": r.message, "local": localdata})
					)
					me.search_item();
					me.gotocart();
					me.show_item_details();
					me.image_view();
					me.unit_qty_change();

					me.item_group_trigger();
					me.category_trigger();
					me.all_sbcat_check();
					me.apply_sbcat_filter();
					me.back_to_item_grid();
				}
				else {
					$('.pepperi-content').html(frappe.render_template('scope_items', 
						{"data": r.message, "local": localdata})
					)
					me.show_item_details();
					me.image_view();
					me.unit_qty_change();
					me.category_trigger();
					me.all_sbcat_check();
					me.apply_sbcat_filter();
					me.back_to_item_grid();
				}
			}
		})
	},

	search_item: function() {
		//TODO - update item grid, check current page
		var me = this;
		$('.search-btn').click(function() {
			var search_txt = $('.search_ip').val();
			if(me.cur_page == "Grid View") {
				if(search_txt) {
					localStorage.setItem("search_txt", search_txt)
					me.render_item_grid(true)
				}
			}
		})

		$('.search-clr').click(function() {
			var search_txt = $('.search_ip').val();
			if(me.cur_page == "Grid View") {
				if(search_txt) {
					$('.search_ip').val("");
					localStorage.removeItem("search_txt");
					me.render_item_grid(true)
				}
			}
		})
	},

	gotocart: function() {
		var me = this;
		$('#goToCartBtn').click(function() {
			me.cur_page = "Cart"
			let data = me.prepare_cart_data();
			$('.backbtn').removeClass('hide');
			$('.pepCheckout').removeClass('hide');
			$('.pepperi-content').html(frappe.render_template("pepperi_cart", {"data": data}))
			me.checkout()
		})
	},

	checkout: function() {
		var me = this;
		$("#grp_order li a").click(function(){
			var data = me.get_localstorage_data();
			var dt=$(this).data('value');
			frappe.call({
				 	method: "playfunction.playfunction.custom_script.quotation.quotation.checkout_order",
				 	args: {
				 		"data" : data, 
				 		"doc_type" : dt
				 	},
				 	callback: function(r) {
			 		 	frappe.set_route("Form",dt,r.message);
				 	}
				})
		});
	},


	show_item_details: function() {
		var me = this;
		$('.ObjectMenu').click(function() {
			let item_code = $(this).attr("data-item")
			$('.backbtn').removeClass('hide');
			me.render_item_details(item_code);
		})
	},

	render_item_details: function(item_code) {
		var me = this;
		frappe.call({
			method: "playfunction.playfunction.page.pepperi.pepperi.get_item_details",
			args: {"item_code": item_code},
			callback: function(r) {
				me.cur_page = "Item Details"
				$('.pepperi-content').html(frappe.render_template('item_details', {"data": r.message[0]}))
			}
		})
	},

	back_to_item_grid: function() {
		var me = this;
		$('.backbtn').click(function() {
			$('.backbtn').addClass('hide');
			$('.pepCheckout').addClass('hide');
			me.cur_page = "Grid View"
			me.render_item_grid(true)
		})
	},

	image_view: function() {
		var me = this;
		var count=1;
		$('.img-view').click(function() {
			let image =  $(this).attr("data-img")
			let dialog = new frappe.ui.Dialog({
				title: __("Image"),
				fields: [
				{"fieldtype": "Button", "label": __("+"), "fieldname": "plus"},
				{"fieldtype": "Button", "label": __("-"), "fieldname": "minus"},
				{
					fieldtype:"HTML",
					fieldname: "image_view",
				}

				]
			});
			var html_field = dialog.fields_dict.image_view.$wrapper;
			html_field.empty();
			html = repl("<div class='img-view' style='text-align:center'>\
				<img src=%(img)s >\
				</div>", {"img": image})
	        
			html_field.append(html)
			dialog.fields_dict.plus.input.onclick = function() {
				$('img').css({"zoom":++count});

			}
			dialog.fields_dict.minus.input.onclick = function() {
				$('img').css({"zoom":--count});
			}

   			dialog.$wrapper.find('.modal-dialog').css({"width":"1200px", "height": "600px", "overflow":"auto"});
			dialog.show();
		})
	},

	unit_qty_change: function() {
		var me = this;
		// decrease-qty
		$('.qty-minus').click(function() {
			var qty = $(this).closest("div.gQs").find("input[name='UnitsQty']").val();
			if (qty && parseInt(qty) > 0) {
				var item_code = $(this).closest("div.gQs").attr("data-item");
				var price = parseFloat($(this).closest("div.gQs").attr("data-price"));
				var img = $(this).closest("div.gQs").attr("data-img");
				qty = parseInt(qty) - 1
				$(this).closest("div.gQs").find("input[name='UnitsQty']").val(qty);
				me.update_cart(item_code, qty, price, img);
			}
		})
		// increase-qty
		$('.qty-plus').click(function() {
			var qty = $(this).closest("div.gQs").find("input[name='UnitsQty']").val();
			qty = parseInt(qty) + 1
			var item_code = $(this).closest("div.gQs").attr("data-item");
			var price = parseFloat($(this).closest("div.gQs").attr("data-price"));
			var img = $(this).closest("div.gQs").attr("data-img");
			$(this).closest("div.gQs").find("input[name='UnitsQty']").val(qty);
			me.update_cart(item_code, qty, price, img);
		})
		// qty-change
		$('.unitqty').change(function() {
			var qty = parseInt($(this).val()) || 0;
			var item_code = $(this).closest("div.gQs").attr("data-item");
			var price = parseFloat($(this).closest("div.gQs").attr("data-price"));
			var img = $(this).closest("div.gQs").attr("data-img");
			$(this).closest("div.gQs").find("input[name='UnitsQty']").val(qty);
			me.update_cart(item_code, qty, price, img);
		})
	},

	item_group_trigger: function() {
		var me = this;
		$('.tree-li-grp').click(function() {
			if(me.cur_page == "Grid View") {
				let item_group = $(this).attr("data-group")
				$('.tree-li-grp').removeClass("selected");
				$(this).addClass("selected");
				localStorage.setItem('item_group', item_group)
				$('.item-grp-nav').text(item_group)
				me.render_item_grid(true);
			}
		})
	},

	category_trigger: function() {
		var me = this;
		if(me.cur_page == "Grid View") {
			$('.tree-li-cat').click(function(e) {
				var search_pos = $("#dvSmSearchHeader").position();
				let cat = $(this).text().trim()
				let sub_cat = $(this).attr('data-subcat').split(",")

				//all checkbox
				sub_cat_html = "\
				<ul class='sb_checkbox' style='list-style-type:none;'>\
					<li>\
						<input class='sb_check' value='All' type='checkbox' id='all_check'>\
						<label for='all_check' class='check_lb' title='All'>All</label>\
					</li>"
				//sub catgory checkbox
				$.each(sub_cat, function(i,sc) {
					sub_cat_html += repl("<li>\
						<input class='sb_check' type='checkbox' value=%(sc)s id=%(sc_id)s>\
						<label class='check_lb' for=%(sc_id)s title=%(sc)s>%(sc)s</label>\
					</li>", {"sc": sc, "sc_id": sc.replace(/ /g,'_')})
				})
				sub_cat_html += "</ul>"

				$('.smBody').html(sub_cat_html)
				$('.subcat_menu').removeClass('hide')
				$('.subcat_menu').css({
					"top": search_pos.top+130,
					"left": "190px",
					"display": "block",
					"position": "fixed",
					"height": "auto!important",
					"width": '331px',
					"overflow": "auto",
					"z-index": 1100,
					"max-width": "88%!important",
				});
				$('.cat_label').text(cat)
				$('.sbfil_btn').attr("data-cat", cat)
				$('.subcat_menu').show();
			})
		}
	},

	all_sbcat_check: function() {
		var me = this;
		$('#all_check').click(function() {
			$(".sb_check").prop('checked', $(this).prop('checked'));
		})
	},

	apply_sbcat_filter: function() {
		//TODO: show applied category filter
		// change py side query - sbcat in (sb1, sb2)
		// methods get called multiple times
		var me = this;

		update_sbcat_filter = function(category, sb_cat) {
			var category_data = me.get_localstorage_data("category")["category"] || {}
			if (sb_cat.length) {
				category_data[category] = sb_cat
			}
			else {
				delete category_data[category]
			}
			localStorage.setItem('category', JSON.stringify(category_data));
			me.render_item_grid(true)
		}
		$('.pep-clear').click(function() {
			var category = $(this).attr("data-cat")
			$('.subcat_menu').hide();
			update_sbcat_filter(category, [])
		})
		$('.pep-done').click(function() {
			var sb_cat = [];
			var category = $(this).attr("data-cat")
			$('.sb_check').each(function () {
				var sb_category = this.checked ? $(this).val().trim() : "";
				if(sb_category) { sb_cat.push(sb_category) }
			});
			$('.subcat_menu').hide();
			update_sbcat_filter(category, sb_cat)
		})
	},

	update_cart: function(item_code, qty, price, img) {
		var items = JSON.parse(localStorage.getItem('items')) || {};
		if (qty == 0) {
			delete items[item_code]
		}
		else {
			items[item_code] = [qty, price, img]
		}
		localStorage.setItem('items', JSON.stringify(items));
	},

	get_localstorage_data: function(key=false) {
		data = {}
		let keys = key ? [key]:["item_group", "search_txt", "items", "category"]
		for (let key of keys) {
			if(has_common(["items", "category"],[key])) {
				data[key] = JSON.parse(localStorage.getItem(key)) || {}
			}
			else {
				data[key] = localStorage.getItem(key) || ""
			}
		}
		return data
	},

	prepare_cart_data: function() {
		var me = this;
		var data = []
		var total = 0
		var cart_data = me.get_localstorage_data("items");
		$.each(cart_data.items || [], function(k,v) {
			let row = {"item_code": k, "qty": v[0], "price": v[1], "img": v[2]}
			total += parseFloat(v[1] || 0) > 0 ? parseFloat(v[1]) * parseInt(v[0]) : 0.00
			data.push(row)
		})
		return {"items": data, "total": total}
	}
})