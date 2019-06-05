frappe.ui.form.on("Sales Invoice",{
	refresh: function(frm) {
		// from public - playfunction_selling.js
		playfunction.selling.set_field_permissions();
	}
})