cur_frm.add_fetch('item_code', 'item_name', 'item_name');
cur_frm.add_fetch('item_code', 'image', 'image');

frappe.ui.form.on("Item", {
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
	    if(frm.doc.is_stock_item==1){
			cur_frm.set_df_property("catalogs", "reqd", frm.doc.is_stock_item=="1");
	    }
	    else{
			cur_frm.set_df_property("catalogs", "reqd", false);
	    }
	},
	onload:function(frm){
		cur_frm.set_df_property("item_group", "hidden", true);
		cur_frm.set_df_property("allow_alternative_item", "hidden", true);
	},
	quick_entry:function(frm){
		cur_frm.set_df_property("item_group", "hidden", true);
	},
	sp_without_vat:function(frm){
		if(frm.doc.sp_without_vat>0){
			var sp_with_vat=frm.doc.sp_without_vat*0.17;
			cur_frm.set_value("sp_with_vat",sp_with_vat);
		}
	},

});


cur_frm.fields_dict['related_item'].grid.get_field('item_code').get_query =function(frm,cdt,cdn){
	return {
		"filters": {'group_level': 1}
	}
}

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
