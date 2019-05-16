frappe.provide("playfunction.selling");

playfunction.selling.SellingController = Class.extend({
	refresh: function() {
		var doctype = cur_frm.doc.doctype
		if(has_common(frappe.user_roles, ["Playfunction Customer"])/* && frappe.session.user != 'Administrator'*/) {
			// set form fields property
			var common_form_fields = {
				"read_only":["customer", "transaction_date",
					"valid_till", "order_type", "customer_address", "contact_person",
					"shipping_address_name", "territory", "apply_discount_on",
					"additional_discount_percentage","discount_amount"],
				"hidden": ["currency_and_price_list", "more_info", "print_settings",
					"payment_schedule_section", "payment_schedule_section",
					"terms_section_break","taxes","taxes_and_charges", "shipping_rule"]
			}

			// doctype wise parent form, child form fields mapping along with property
			/*e.g. {"DocType": {
					"parent": {read_only fields, hidden fields},
					"item": {read_only fields, hidden fields}
				}}*/

			var doctype_fields = {
				"Quotation": {
					"parent": {"read_only": ["quotation_to"], "hidden": []},
					"item": {"read_only": [], "hidden": []}
				},
				"Sales Order": {
					"parent": {"read_only": [], "hidden": []},
					"item": {"read_only": [], "hidden": []}
				},
				"Sales Invoice": {
					"parent": {"read_only": [], "hidden": []},
					"item": {"read_only": [], "hidden": []}
				}
			}

			$.each(common_form_fields, function(prop, fields) {
				var fields_ = fields.concat(doctype_fields[doctype]['parent'][prop])
				$.each(fields_, function(i, f){
					cur_frm.set_df_property(f, prop, true)
				})
			})

			// Item table properties
			var items_table = {
				"read_only" : ["item_name", "barcode", "supplier_item_code",
					"uom","margin_type", "margin_rate_or_amount", "discount_percentage", "rate"],
				"hidden": ["cost_price", "selling_rate", "item_weight_details", "item_balance", "reference"]
			}

			$.each(items_table, function(prop, fields){
				var fields_ = fields.concat(doctype_fields[doctype]['item'][prop])
				$.each(fields_, function(idx, field){
					var df = frappe.meta.get_docfield(doctype+" Item", field, cur_frm.doc.name);
					df[prop] = true
				})
			})
		}
	}
})