frappe.pages['pepperi'].on_page_load = function(wrapper) {
	new frappe.pepperi({
		$wrapper: $(wrapper)
	});
	frappe.breadcrumbs.add("PlayFunction");
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
		this.rtl_setup();
		this.home();
		this.bind_events();
	},

	rtl_setup: function() {
		if (frappe.utils.is_rtl()) {
			console.log("RTL Activate....")
			/*var ls = document.createElement('link');
			ls.rel="stylesheet";
			ls.href= "/assets/css/playfunction-web.min.css";
			document.getElementsByTagName('head')[0].appendChild(ls);*/
			//$('head').append('<link rel="stylesheet" href="style2.css" type="text/css" />');
		}
		else {
			console.log("RTL Deactivate ....")
		}
	},

	home: function() {
		this.$header.empty()
		this.$main.empty()
		this.$header.append(frappe.render_template("pep_header"))
		this.$main.append(frappe.render_template("pepperi_home"))
		this.cur_page = "pepperi_home"
		this.bind_events();


	},

	bind_events: function() {
		var me = this;
		//redirect to home
		$('#btnMenuHome').click(function() {
			me.home();
		})

		// redirect to catalog
		$('#CatalogList').click(function(){
			me.render_item_catalog();
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
			frappe.set_route("query-report", "Order History");
		})

		//order list
		$('#order-list').click(function() {
			frappe.set_route("List", "Sales Order")
		})

		//quotation history
		$('#quote-history').click(function() {
			window.location.href = "/desk#List/Quotation/Report"
		})

		//quotation list
		$('#quote-list').click(function() {
			window.location.href = "/desk#List/Quotation/List"
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
			localStorage.removeItem("search_txt");
			// me.render_item_grid(true)
			me.render_item_grid()
		})
	},

	render_item_grid: function(update_grid=false) {
		//filters = {"item_group": "Products", "category": {"Collection": ["Vintage"]}, "search_txt": "ada"}
		var me = this;
		filters = me.get_localstorage_data()
		frappe.call({
			method: "playfunction.playfunction.page.pepperi.pepperi.get_items_and_group_tree",
			args: {"filters": filters},
			callback: function(r) {
				me.localdata = JSON.parse(localStorage.getItem("items")) || {}
				let localdata = JSON.parse(localStorage.getItem("items")) || {}
				if(!update_grid) {
					me.$main.empty()
					me.cur_page = "Grid View"
					me.$main.append(frappe.render_template("pepperi_item_list", {
						"data": r.message, "item_group": filters["item_group"],
						"child_item_group": filters["child_item_group"], "total": 0
					}))
					$('.pepperi-content').html(frappe.render_template('scope_items',
						{"data": r.message, "local": localdata})
					)
					me.search_item();
					me.gotocart();
					me.show_item_details();
					me.image_view();
					me.unit_qty_change();

					me.item_group_trigger();
					//me.child_item_group_trigger();
					me.category_trigger();
					me.back_to_item_grid();
				}
				else {
					$('.pepperi-content').html(frappe.render_template('scope_items',
						{"data": r.message, "local": localdata})
					)
					me.show_item_details();
					me.image_view();
					me.unit_qty_change();
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
			me.localdata = JSON.parse(localStorage.getItem("items")) || {}
			me.cur_page = "Cart"
			let data = me.prepare_cart_data();
			$('.backbtn').removeClass('hide');
			$('.pepCheckout').removeClass('hide');
			$('#goToCartBtn').hide();
			data.total=me.cart_details.total
			data.total_after_discount = me.cart_details.total_after_discount

			$('.pepperi-content').html(frappe.render_template("pepperi_cart", {"data": data,"local":me.localdata}))
			$('.total_details').html(frappe.render_template("total_cart_details", {"total": data.total,"total_after_discount":data.total_after_discount}));
			me.unit_qty_change()
			me.checkout()
		})
	},

	checkout: function() {
		var me = this;
		$(".pepCheckout_opt a").click(function(){
			var data = me.get_localstorage_data();
			var doctype = $(this).data('value');
			frappe.call({
				method:"playfunction.playfunction.custom_script.quotation.quotation.checkout_order",
				args: {
					"data": data,
					"doctype": doctype
				},
				callback: function(r) {
					if(!r.exc && r.message) {
						frappe.msgprint((doctype+" is created Successfully"));
						setInterval(function(){window.location.reload();},3000);
						//clear localStorage
						keys = ["items","filters","search_txt","category","item_group","child_item_group"]
						$.each(keys, function(i, key) {
							localStorage.removeItem(key);
						})
						localStorage.removeItem("search_txt");
						me.render_item_grid(true)
					}else {
						frappe.msgprint(__("Something went wrong while placing order."))
					}
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
				$('.pepperi-content').html(frappe.render_template('item_details', {"data": r.message}))
			}
		})
	},

	back_to_item_grid: function() {
		var me = this;
		$('.backbtn').click(function() {
			$('.backbtn').addClass('hide');
			$('.pepCheckout').addClass('hide');
			$('#goToCartBtn').show();
			me.cur_page = "Grid View"
			me.render_item_grid(true)
		})
	},

	image_view: function() {
		var me = this;
		var scale = 0.8;
		transform_css = "translate(0px, 0px) rotate(0deg) scale(%(scale)s)"
		image_max_min = function(new_scale, dialog) {
			cal_scale = scale + new_scale
			if(cal_scale > 0.2 && cal_scale < 1.4) {
				scale += new_scale
				dialog.$wrapper.find('#zoom-view').css({"transform": repl(transform_css, {"scale": scale})});
			}
		}
		$('.img-view').click(function() {
			scale = 0.8
			let image =  $(this).attr("data-img")
			let dialog = new frappe.ui.Dialog({
				title: __("Image"),
				fields: [
					{"fieldtype": "Button", "label": "+", "fieldname": "plus"},
					{"fieldtype": "Button", "label": "-", "fieldname": "minus"},
					{"fieldtype":"HTML","fieldname": "image_view"}
				]
			});
			var html_field = dialog.fields_dict.image_view.$wrapper;
			html_field.empty();
			html = repl("<div class='img-view' style='text-align:center'>\
				<img id='zoom-view' src=%(img)s \
				style='transform: translate(0px, 0px) rotate(0deg) scale(0.8); height:440px;'>\
				</div>", {"img": image})

			html_field.append(html)
			dialog.fields_dict.plus.input.onclick = function() {
				image_max_min(0.2, dialog);
			}
			dialog.fields_dict.minus.input.onclick = function() {
				image_max_min(-0.2, dialog);
			}
			dialog.$wrapper.find('.modal-dialog').css({"width":"1000px", "overflow":"auto"});
			dialog.$wrapper.find('.modal-content').css({"height": "600px"});
			dialog.show();
		})
	},

	unit_qty_change: function() {
		var me = this;
		update_cart_qty = function(el,update_qty=false) {
			var qty = $(el).closest("div.gQs").find("input[name='UnitsQty']").val();
			var qty = qty > 0 ? parseInt(qty) : 0
			var item_code = $(el).closest("div.gQs").attr("data-item");
			var price = parseFloat($(el).closest("div.gQs").attr("data-price"));
			var discount = parseFloat($(el).closest("div.gQs").attr("data-discount"));
			var img = $(el).closest("div.gQs").attr("data-img");
			var qty = update_qty ? parseInt(qty) + update_qty : qty
			$(el).closest("div.gQs").find("input[name='UnitsQty']").val(qty);
			me.update_cart(item_code, qty, price, discount,img);
		}
		// refresh qty
		update_cart_qty(this, 0)
		// decrease-qty
		$('.qty-minus').click(function() {
			update_cart_qty(this, -1)

		})
		// increase-qty
		$('.qty-plus').click(function() {
			update_cart_qty(this, 1)
		})
		// decrease-qty-cart
		$('.qty-minus-cart').click(function() {
			update_cart_qty(this, -1)
			var qty = $(this).closest("div.gQs").find("input[name='UnitsQty']").val();
			if (qty && parseInt(qty) > 0) {
				let data = me.prepare_cart_data();
				data.total=me.cart_details.total
				data.total_after_discount = me.cart_details.total_after_discount
				// $('.pepperi-content').html(frappe.render_template("pepperi_cart", {"data": data,"local":me.localdata}))
				$('.total_details').html(frappe.render_template("total_cart_details", {"total": data.total,"total_after_discount":data.total_after_discount}));
				// me.unit_qty_change()
			}
			else{
				$('.total_details').html(frappe.render_template("total_cart_details", {"total": 0,"total_after_discount":0}));
			}
		})
		// increase-qty in cart
		$('.qty-plus-cart').click(function() {
			update_cart_qty(this, 1)
			var qty = $(this).closest("div.gQs").find("input[name='UnitsQty']").val();
			if (qty && parseInt(qty) > 0) {
				let data = me.prepare_cart_data();
				data.total=me.cart_details.total
				data.total_after_discount = me.cart_details.total_after_discount
				// $('.pepperi-content').html(frappe.render_template("pepperi_cart", {"data": data,"local":me.localdata}))
				$('.total_details').html(frappe.render_template("total_cart_details", {"total": data.total,"total_after_discount":data.total_after_discount}));
				// me.unit_qty_change()
			}
		})
		// qty-change
		$('.unitqty').change(function() {
			update_cart_qty(this)
		})
		$('.delete_item').click(function() {
			// alert(item_code)
			// localStorage.removeItem(this);
			// update_cart_qty(this)
		})

	},

	item_group_trigger: function() {
		var me = this;
		// trigger item grid with given group fileter
		var _item_grid = function(group, label='') {
			if(me.cur_page == "Grid View") {
				var label = label ? label : group
				localStorage.setItem('child_item_group', group)
				$('.ch-item-grp-nav').text(label)
				me.render_item_grid(true);
			}
		}

		// sidebar item grp hover/click
		$('.tree-li-grp').hover(
			function() {
				$('.child-box').removeClass("sel-hover");
				$('.grand-child').removeClass('ch-sel-hover');
				$(this).find('.child-box').addClass('sel-hover')
			}
		)

		$('.tree-li-grp').click(function() {
			var group = $(this).attr('data-group')
			_item_grid(group)
		})

		// child item group - 1 hover/click
		$('.tree-li-chgrp').hover(function(e) {
			e.stopPropagation();
			$('.grand-child').removeClass('ch-sel-hover');
			$(this).find('.grand-child').addClass('ch-sel-hover')
		})

		$('.tree-li-chgrp').click(function(e) {
			e.stopPropagation();
			var group = $(this).attr('data-group')
			var label = $(this).attr('data-parent') + ' > ' + group
			_item_grid(group, label)
		})

		// grand child item group - 2 hover/click
		$('.grand-ch-grp').click(function(e) {
			e.stopPropagation();
			var grand_child = $(this).attr('data-group')
			$('.grand-child').removeClass('ch-sel-hover');
			$('.child-box').removeClass("sel-hover");

			var label = $(this).attr('data-grand-parent') + ' > ' +
				$(this).attr('data-parent') + ' > ' + grand_child
			_item_grid(grand_child, label)
		})

		$(".grand-child, .child-box").mouseleave(function(e) {
			e.stopPropagation()
			$('.grand-child').removeClass('ch-sel-hover');
			$('.child-box').removeClass("sel-hover");
		})

		// on outside click hide item group boxes
		$(document).click(function() {
			$('.grand-child').removeClass('ch-sel-hover');
			$('.child-box').removeClass("sel-hover");
		})
	},

	child_item_group_trigger: function() {
		var me = this;
		$('.tree-li-grp-ch').click(function(e) {
			if(me.cur_page == "Grid View") {
				e.stopPropagation();
				var child_item_group = $(this).attr("data-group")
				$('.tree-li-grp-ch').removeClass("selected");
				$(this).addClass("selected");

				localStorage.setItem('child_item_group', child_item_group)
				$('.ch-item-grp-nav').text(child_item_group)
				me.render_item_grid(true);
			}
		})
	},

	category_trigger: function() {
		var me = this;
		$('.tree-li-cat').click(function(e) {
			if(me.cur_page == "Grid View") {
				var search_pos = $("#dvSmSearchHeader").position();
				var cat = $(this).text().trim()
				var sub_cat = $(this).attr('data-subcat').split(",")
				var selected_sbcat = me.get_localstorage_data("category")["category"][cat] || []

				//all checkbox
				sub_cat_html = repl("\
				<ul class='sb_checkbox' style='list-style-type:none;'>\
					<li>\
						<input class='sb_check' value='All' type='checkbox' id='all_check' %(checked)s>\
						<label for='all_check' class='check_lb' title='All'>All</label>\
					</li>", {"checked": selected_sbcat.includes("All")? "checked": ""})

				//sub catgory checkbox
				$.each(sub_cat, function(i,sc) {
					sub_cat_html += repl("<li>\
						<input class='sb_check' type='checkbox' value=%(sc)s id=%(sc_id)s %(checked)s>\
						<label class='check_lb' for=%(sc_id)s title=%(sc)s>%(sc)s</label>\
					</li>", {"sc": sc, "sc_id": sc.replace(/ /g,'_'), "checked": selected_sbcat.includes(sc)? "checked": ""})
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
				me.all_sbcat_check();
				me.apply_sbcat_filter();
			}
		})
	},

	all_sbcat_check: function() {
		var me = this;
		$('#all_check').click(function() {
			$(".sb_check").prop('checked', $(this).prop('checked'));
		})
	},

	apply_sbcat_filter: function() {
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

	update_cart: function(item_code, qty, price, discount, img) {
		var me =this;
		var items = JSON.parse(localStorage.getItem('items')) || {};
		total_qty = 0
		if (qty == 0) {
			delete items[item_code]
		}
		else {
			items[item_code] = [qty, price, discount, img]
		}
		$.each(items, function(i, row) {
			total_qty += parseInt(row[0]) || 0
		})
		$('.total-cnt').text("Qty : "+ String(total_qty))
		localStorage.setItem('items', JSON.stringify(items));
	},

	get_localstorage_data: function(key=false) {
		data = {}
		let keys = key ? [key]:["item_group", "child_item_group","search_txt", "items", "category"]
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
		var total_after_discount = 0
		var cart_data = me.get_localstorage_data("items");
		$.each(cart_data.items || [], function(k,v) {
			let row = {"item_code": k, "qty": v[0], "price": v[1], "discount": v[2], "img": v[3]}
			total += parseFloat(v[1] || 0) > 0 ? parseFloat(v[1]) * parseInt(v[0]) : 0.00
			total_after_discount += parseFloat(v[1] || 0) > 0 ? parseFloat(v[1]-(v[1]*v[2]/100)) * parseInt(v[0]) : 0.00
			data.push(row)
		})
		me.cart_details = {"items": data, "total": total,"total_after_discount":total_after_discount}
		return {"items": data, "total": total,"total_after_discount":total_after_discount}
	}
})
