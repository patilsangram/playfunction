frappe.ui.form.on("Sales Order",{
	refresh: function(frm) {
		// from public - playfunction_selling.js
		playfunction.selling.set_field_permissions();
		playfunction.export.export_excel();
		if (frm.doc.docstatus == 0 && frm.doc.workflow_state != "Rejected") {
			frm.events.init_approval_flow(frm);
		}
	},

	init_approval_flow: function(frm){
		// TODO - Make commomn workflow for Quotation & SO
		if(frappe.user.has_role("PlayFunction Admin")) {
			frm.add_custom_button("Approve", function() {
				frm.trigger('approve_order');
			}, "Action")

			frm.add_custom_button("Reject", function() {
				frm.trigger('reject_order');
			}, "Action")
			frm.page.set_inner_btn_group_as_primary(__("Action"));
		}
	},

	approve_order:function(frm){
		frm.doc.workflow_state = "Approved";
		frm.savesubmit();
	},

	reject_order:function(frm){
		frm.doc.workflow_state = "Rejected";
		frm.save();
	},

	before_submit:function(frm){
		if(frm.doc.workflow_state != "Approved"){
			frappe.throw(__("Sales Order must be approved by Admin"))
		}
	}
})