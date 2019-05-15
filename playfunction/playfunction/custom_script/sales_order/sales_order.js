

frappe.require("/assets/playfunction/playfunction.js")


frappe.ui.form.on("Sales Order",{
	onload:function(frm){
		frm.trigger("update_field_property");
		
	}
});