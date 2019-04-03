frappe.ui.form.on("Item", {
	validate: function(frm) {
			var modules_data = frm.doc.category_list
			var module_data_list = []
			modules_data.forEach(function(e){
				module_data_list.push(e.subcategory)
			})
			var data_set=new Set(module_data_list)
			if(data_set.size < module_data_list.length)
			{
				frappe.throw("In Category List field duplicates are found, please try with another")
			}
			

	}
});

cur_frm.fields_dict['category_list'].grid.get_field('subcategory').get_query =function(frm,cdt,cdn){
				var d=locals[cdt][cdn]
				return {
					"filters": {'category': d.category}
				}
}
