$.extend(cur_frm.cscript, new playfunction.selling.SellingController({frm: cur_frm}));

frappe.ui.form.on("Sales Order",{
	refresh: function(frm) {

	}
})