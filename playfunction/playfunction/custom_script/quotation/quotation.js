frappe.ui.form.on("Quotation",{
	refresh: function(frm) {
		if (frm.doc.docstatus == 0 && frm.doc.workflow_state != "Rejected") {
			frm.events.init_approval_flow(frm);
		}
		frm.trigger("set_status_intro");
		frm.trigger("update_field_property");
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

	update_field_property: function(frm) {
		if(has_common(frappe.user_roles, ["Playfunction Customer"]) && frappe.session.user != 'Administrator') {
			// set form fields property
			var form_fields = {
				"read_only":["quotation_to", "customer", "transaction_date",
					"valid_till", "order_type", "customer_address", "contact_person",
					"shipping_address_name", "territory", "apply_discount_on",
					"additional_discount_percentage","discount_amount"],
				"hidden": ["currency_and_price_list", "more_info", "print_settings",
					"payment_schedule_section", "payment_schedule_section",
					"terms_section_break","taxes","taxes_and_charges", "shipping_rule"]
			}

			$.each(form_fields, function(prop, fields) {
				$.each(fields, function(i, f){
					frm.set_df_property(f, prop, true)
				})
			})

			// Quotation item table properties
			var items_table = {
				"read_only" : ["item_name", "barcode", "supplier_item_code",
					"uom","margin_type", "margin_rate_or_amount", "discount_percentage", "rate"],
				"hidden": ["cost_price", "selling_rate", "item_weight_details", "item_balance", "reference"]
			}

			$.each(items_table, function(prop, fields){
				$.each(fields, function(idx, field){
					var df = frappe.meta.get_docfield("Quotation Item", field, frm.doc.name);
					df[prop] = true
				})
			})
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