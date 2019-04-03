frappe.ui.form.on("Item", {
	refresh: function(frm) {
		// script
	}


})


cur_frm.fields_dict['category_list'].grid.get_field('subcategory').get_query =function(frm,cdt,cdn){
				var d=locals[cdt][cdn]
				return {
					"query": "playfunction.playfunction.custom_script.item.item_info",
					"filters": {'category': d.category}
				}
}
