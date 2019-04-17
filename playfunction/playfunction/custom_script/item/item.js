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
			//validation for discount field
			if(frm.doc.max_discount>0)
			{	
				if(frm.doc.discount>frm.doc.max_discount)
				{
					cur_frm.set_value("discount","")
					refresh_field("discount")
					frappe.throw("Please enter valid discount, it should not be more than max discount")
				}
			}
	},
		
	
});

cur_frm.fields_dict['category_list'].grid.get_field('subcategory').get_query =function(frm,cdt,cdn){
	var d=locals[cdt][cdn]
	return {
		"filters": {'category': d.category}
	}
}
