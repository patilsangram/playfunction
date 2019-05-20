
frappe.provide("playfunction.selling");

playfunction.selling.SellingController = Class.extend({
	refresh: function() {
		var doctype = cur_frm.doc.doctype
		if(has_common(frappe.user_roles, ["Playfunction Customer"]) && frappe.session.user != 'Administrator') {
			// set form fields property
			var common_form_fields = {
				"read_only":["customer_name", "transaction_date", "company",
					"valid_till", "order_type", "customer_address", "contact_person",
					"shipping_address_name", "territory", "apply_discount_on"],
				"hidden": [
					"terms_section_break", "shipping_rule","taxes_section","taxes","currency_and_price_list","subscription_section"]
			}

			// doctype wise parent form, child form fields mapping along with property
			/*e.g. {"DocType": {
					"parent": {read_only fields, hidden fields},
					"item": {read_only fields, hidden fields}
				}}*/

			var doctype_fields = {
				"Quotation": {
					"parent": {"read_only": ["quotation_to"], "hidden": ["more_info","section_break_44"]},
					"item": {"read_only": ["description"], "hidden": ["gst_hsn_code","conversion_factor"]}
				},
				"Sales Order": {
					"parent": {"read_only": ["delivery_date","po_no","status"], "hidden": ["set_warehouse","sales_partner","sales_team","more_info","sales_team_section_break","section_break_48","section_break1"]},
					"item": {"read_only": ["item_code","description","weight_per_unit","weight_uom"], "hidden": ["gst_hsn_code","uom","delivered_by_supplier","supplier","warehouse","blanket_order"]}
				},
				"Sales Invoice": {
					"parent": {"read_only": ["due_date","project","po_no","po_date"], "hidden": ["print_settings","sales_partner","commision_rate","total_commision","sales_team","invoice_copy","select_print_heading","reverse_charge","invoice_type","ecommerce_gstin","more_information","section_break_49","section_break2"]},
					"item": {"read_only": ["item_code","description","weight_per_unit","total_weight"], "hidden": ["gst_hsn_code","uom","conversion_factor","delivered_by_supplier","income_account","cost_center","expence_account","enable_deferred_revenue","warehouse","batch_no","allow_zero_valuation_rate","serial_no","asset"]}
				}
			}

			$.each(common_form_fields, function(prop, fields) {
				
				var fields_ = fields.concat(doctype_fields[doctype]['parent'][prop])
				$.each(fields_, function(i, f){
					cur_frm.set_df_property(f, prop, true)
					console.log(f, "------>", prop)
					console.log(cur_frm.set_df_property(f, prop, true))
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