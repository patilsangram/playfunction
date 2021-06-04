frappe.provide("playfunction.export");

playfunction.export.export_excel = function(doc) {

	var doctype = cur_frm.doc.doctype
	if(has_common(["Quotation", "Sales Order"], [doctype]) && cur_frm.has_perm("submit"), cur_frm.doc.docstatus == 1) {
		cur_frm.add_custom_button(__("Export"), function() {
			let get_template_url = '/api/method/playfunction.playfunction.playfunction_export.export_data';
			open_url_post(get_template_url, {dt: cur_frm.doc.doctype, dn: cur_frm.doc.name});
		}).addClass("btn-primary");
	}
}
