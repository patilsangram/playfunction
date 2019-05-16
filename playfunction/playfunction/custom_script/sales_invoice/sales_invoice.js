$.extend(cur_frm.cscript, new playfunction.selling.SellingController({frm: cur_frm}));

frappe.ui.form.on("Sales Invoice",{
	refresh: function(frm) {
		console.log("custom sales invoice")
	}
})