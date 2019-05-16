frappe.provide("playfunction.selling");

playfunction.selling.SellingController = Class.extend({
	refresh: function() {
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
	}
})

playfunction.selling.onload_trigger = function(doc) {
	console.log("outside function call")
}