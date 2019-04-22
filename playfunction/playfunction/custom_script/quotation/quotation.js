frappe.ui.form.on("Quotation", {
	refresh: function(frm) {

	}
})

frappe.ui.form.on("Quotation Item",{
	item_code: function(frm, cdt, cdn) {
		var item = frappe.get_doc(cdt, cdn);
		/*frappe.call({
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
		})*/
	}
})