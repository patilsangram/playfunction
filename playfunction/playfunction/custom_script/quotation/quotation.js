frappe.ui.form.on("Quotation",{
	setup:function(frm){
		frm.add_fetch('item_code', 'cost_price', 'cost_price');
	},

	onload: function(frm) {
		if(!frm.doc.taxes_and_charges && frm.is_new()) {
			frm.set_value("taxes_and_charges", "VAT 17% - PF")
		}
	},

	refresh: function(frm) {
		// from public - playfunction_selling.js
		playfunction.selling.set_field_permissions();
		var proposal_states = ["Proposal Received", "Proposal Processing", "Proposal Ready"]
		if (frm.doc.docstatus == 0 &&
				!(has_common([frm.doc.workflow_state],["Approved","Rejected"].concat(proposal_states)))) {
			frm.events.approval_flow(frm);
		}

		else if(has_common([frm.doc.workflow_state], proposal_states)) {
			frm.events.proposal_flow(frm);
		}

		else if(frm.doc.workflow_state == "Rejected") {
			frm.disable_save()
		}
		frm.trigger("set_status_intro");
	},

	validate: function(frm) {
		if(frm.doc.workflow_state == "Proposal Received") {
			frm.doc.workflow_state = "Proposal Processing"
		}

		//blank description issue fix

		$.each(frm.doc.items, function(i, row) {
			if(!row.description || row.description == '<div><br></div>' || 
				row.description == undefined) {
				frappe.model.set_value(row.doctype, row.name,
					"description", row.item_name)
			}
			refresh_field("items");
		})
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
		frm.refresh_field("workflow_state")
		frm.trigger("set_status_intro");
		frm.save()
		//frm.savesubmit();
	},

	reject_qutotation:function(frm){
		frm.doc.workflow_state = "Rejected";
		frm.save();
	},

	before_submit:function(frm){
		if(!in_list(["Approved", "Proposal Ready"], frm.doc.workflow_state)){
			frappe.throw(__("Quotation/Proposal must be approved by Admin"))
		}
	},

	proposal_flow: function(frm) {
		if (frm.doc.workflow_state == "Proposal Processing" && frappe.user.has_role("PlayFunction Admin")) {
			frm.add_custom_button("Approve Proposal", function() {
				if(!frm.doc.client_approval) {
					frappe.msgprint(__("Quotation must be Client Approved. Please check <b>Client Approval</b> checkbox first."))
				}
				else {
					frm.doc.workflow_state = "Proposal Ready"
					//frm.doc.workflow_state = "Approved"
					frm.save()
				}
			}, "Action")

			frm.add_custom_button("Reject Proposal", function() {
				frm.trigger('reject_qutotation');
			}, "Action")
			frm.page.set_inner_btn_group_as_primary(__("Action"));
		}
	}
})

/*//#TODO: temporary commented as proposal hebrew calculations was coming wrong. Discuss & uncomment/modify
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
})*/

