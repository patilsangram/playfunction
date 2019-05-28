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
		

	// related item duplicate check
		var related_item_list = []
		frm.doc.related_item.forEach(function(e){
			related_item_list.push(e.item_code)
		});
		var related_item_set=new Set(related_item_list)
		if(related_item_set.size < related_item_list.length)
		{
			frappe.throw("Duplicates found in related item section, please remove it")
		}

	},
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
