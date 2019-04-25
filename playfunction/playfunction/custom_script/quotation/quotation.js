frappe.ui.form.on("Quotation",{
	refresh: function(frm) {
		if (frm.doc.docstatus == 0 && frm.doc.workflow_state != "Rejected") {
			frm.events.init_approval_flow(frm);
		}
		frm.trigger("set_status_intro");
	},

	set_status_intro: function(frm) {
		var status_mapper = {
			"Draft": "Approve this document to Submit",
			"Approved": "Approved",
			"Rejected": "Rejected Quotation. Create New One"
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

	init_approval_flow: function(frm){
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
	}
})

frappe.ui.form.on("Quotation Item",{
	selling_rate:function(frm,cdt,cdn){
		var item=locals[cdt][cdn]
		if(item.cost_price && item.cost_price > 0){
			var selling_price= item.cost_price * item.selling_rate
			frappe.model.set_value(cdt, cdn, "rate", selling_price)
			refresh_field("rate")
			frappe.model.set_value(cdt, cdn, "selling_price", selling_price)
			refresh_field("selling_price")
		}	
	}
})

// ToDo : Quotation Item calculation
/*frappe.ui.form.on("Quotation Item",{
	item_code: function(frm, cdt, cdn) {
		var item = frappe.get_doc(cdt, cdn);
		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Item',
				'filters': {'name': item.item_code},
				'fieldname': 'discount_percentage'
			},
			async: false,
			callback: function(r) {
				if(r.message) {
					frappe.model.set_value(cdt, cdn, "discount_percentage", r.message.discount_percentage)
				}
			}
		})
	}
})*/