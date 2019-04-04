frappe.ui.form.on("Item", {
	validate: function(frm) {
			var sub_cat_list = []
			frm.doc.category_list.forEach(function(e){
				sub_cat_list.push(e.subcategory)
			})
			var sub_cat_set=new Set(sub_cat_list)
			if(sub_cat_set.size < sub_cat_list.length)
			{
				frappe.throw("Duplicates found in category list section, please remove it")
			}
			

	}
});

cur_frm.fields_dict['category_list'].grid.get_field('subcategory').get_query =function(frm,cdt,cdn){
	var d=locals[cdt][cdn]
	return {
		"filters": {'category': d.category}
	}
}
