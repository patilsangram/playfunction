cur_frm.add_fetch('item_code', 'item_name', 'item_name');
cur_frm.add_fetch('item_code', 'image', 'image');

frappe.ui.form.on("Item", {
	onload:function(frm){
		frm.trigger("is_stock_item");
		if(!frm.doc.item_group) {
			frm.set_value("item_group", "All Item Groups");
		}
		frm.set_df_property("item_group", "hidden", true);
		frm.set_df_property("allow_alternative_item", "hidden", true);
	},

	validate: function(frm) {
		//validation for discount field
		if(frm.doc.max_discount>0 && frm.doc.discount>frm.doc.max_discount) {
			frm.set_value("discount","")
			refresh_field("discount")
			frappe.throw("Please enter valid discount, it should not be more than max discount")
		}

		// validate duplicate Related Item entry
		var related_items = []
		$.each(frm.doc.related_item, function(i, v){
			related_items.push(v.item_code)
		})
		var related_items_set = new Set(related_items)
		if(related_items.length > related_items_set.size) {
			frappe.throw(__("Duplicate Entry found in Related Items."))
		}
	},

	is_stock_item:function(frm){
		frm.toggle_reqd("catalogs", frm.doc.is_stock_item);
	},

	quick_entry:function(frm){
		frm.set_df_property("item_group", "hidden", true);
	},

	sp_without_vat:function(frm){
		frm.events.calculate_selling_price(frm, "sp_without_vat");
	},

	sp_with_vat:function(frm) {
		frm.events.calculate_selling_price(frm, "sp_with_vat");
	},

	calculate_selling_price: function(frm, field) {
		// calculate sp_with_vat & sp_without_vat on vice versa trigger
		// added if conditions to avoid loop
		if(field == "sp_without_vat" && frm.doc.sp_without_vat > 0) {
			var with_vat = flt(frm.doc.sp_without_vat*0.17 + frm.doc.sp_without_vat, 2)
			if(with_vat != frm.doc.sp_with_vat) {
				frm.set_value("sp_with_vat", with_vat);
			}
		}

		else if(field == "sp_with_vat" && frm.doc.sp_with_vat > 0) {
			var without_vat	= flt(frm.doc.sp_with_vat - frm.doc.sp_with_vat*0.17/1.17, 2)
			if(without_vat != frm.doc.sp_without_vat) {
				frm.set_value("sp_without_vat", without_vat);
			}
		}
	}
});


cur_frm.fields_dict['catalogs'].grid.get_field('catalog_level_1').get_query =function(frm,cdt,cdn){
	return {
		"filters": {'group_level': 1}
	}
}

cur_frm.fields_dict['catalogs'].grid.get_field('catalog_level_2').get_query =function(frm,cdt,cdn){
	var row = locals[cdt][cdn];
	return {
		"filters": {
			'group_level': 2,
			'parent_item_group': row.catalog_level_1
		}
	}
}

cur_frm.fields_dict['catalogs'].grid.get_field('catalog_level_3').get_query =function(frm,cdt,cdn){
	var row = locals[cdt][cdn];
	return {
		"filters": {
			'group_level': 3,
			'parent_item_group': row.catalog_level_2
		}
	}
}

cur_frm.fields_dict['catalogs'].grid.get_field('catalog_level_4').get_query =function(frm,cdt,cdn){
	var row = locals[cdt][cdn];
	return {
		"filters": {
			'group_level': 4,
			'parent_item_group': row.catalog_level_3
		}
	}
}
