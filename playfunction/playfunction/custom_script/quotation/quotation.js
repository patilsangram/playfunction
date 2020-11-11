frappe.ui.form.on("Quotation",{
	setup:function(frm){
		frm.add_fetch('item_code', 'cost_price', 'cost_price');
	},
	refresh: function(frm) {
		// from public - playfunction_selling.js
		//playfunction.selling.set_field_permissions();
		var proposal_states = ["Proposal Received", "Proposal Processing", "Proposal Ready"]
		if (frm.doc.docstatus == 0 &&
				!(has_common([frm.doc.workflow_state],["Rejected"].concat(proposal_states)))) {
			frm.events.approval_flow(frm);
		}

		else if(has_common([frm.doc.workflow_state], proposal_states)) {
			frm.events.proposal_flow(frm);
		}
		frm.trigger("set_status_intro");
	},

	validate: function(frm) {
		if(frm.doc.workflow_state == "Proposal Received") {
			frm.doc.workflow_state = "Proposal Processing"
		}
	},

	set_status_intro: function(frm) {
		var status_mapper = {
			"Draft": "Approve this document to Submit",
			"Approved": "Approved",
			"Rejected": "Rejected Quotation. Create New One",
			"Proposal Received": "Modify and Approve the Proposal",
			"Proposal Processing": "Approve the Proposal",
			"Proposal Ready": "Proposal Ready"
		}
		frm.set_intro();
		var workflow_state = frm.doc.workflow_state
		if(!workflow_state || workflow_state == "") {
			frm.set_intro(status_mapper["Draft"])
		}
		else {
			frm.set_intro(status_mapper[workflow_state])
		}
	},


	approval_flow: function(frm){
		if(frappe.user.has_role("PlayFunction Admin")) {
			frm.add_custom_button("Approve", function() {
				frm.trigger('approve_qutotation');
			}, "Action")

			frm.add_custom_button("Reject", function() {
				frm.trigger('reject_qutotation');
			}, "Action")
			frm.page.set_inner_btn_group_as_primary(__("Action"));
		}
	},

	approve_qutotation:function(frm){
		frm.doc.workflow_state = "Approved";
		frm.savesubmit();
	},

	reject_qutotation:function(frm){
		frm.doc.workflow_state = "Rejected";
		frm.save();
	},

	before_submit:function(frm){
		if(frm.doc.workflow_state != "Approved"){
			frappe.throw(__("Quotation must be approved by Admin"))
		}
	},

	proposal_flow: function(frm) {
		if (frm.doc.workflow_state == "Proposal Processing" && frappe.user.has_role("PlayFunction Admin")) {
			frm.add_custom_button("Approve Proposal", function() {
				frm.doc.workflow_state = "Proposal Ready"
				frm.save()
			})
		}

		// admin can not edit proposal ready
		if(frm.doc.workflow_state == "Proposal Ready") {
			frm.disable_save();
		}
	}
})

frappe.ui.form.on("Quotation Item",{
	selling_rate:function(frm, cdt, cdn){
		var item = locals[cdt][cdn]
		if(item.cost_price && item.cost_price > 0 && item.selling_rate > 0){
			var selling_price = flt(item.cost_price * item.selling_rate, precision("rate", item))
			frappe.model.set_value(cdt, cdn, "rate", selling_price)
		}
		else {
			frappe.model.set_value(cdt, cdn, "selling_rate", 0);
			frappe.model.set_value(cdt, cdn, "rate", item.price_list_rate);
		}
		refresh_field("items");
	},

	rate:function(frm, cdt, cdn){
		var item = locals[cdt][cdn]
		if(item.cost_price && item.rate) {
			var selling_rate = flt(item.rate/item.cost_price, precision("selling_rate", item))
			frappe.model.set_value(cdt, cdn, "selling_rate", selling_rate)
		}
		refresh_field("items");
	}
})
