frappe.ui.form.on("Quotation",{
	refresh: function(frm) {
		if (frm.doc.docstatus==0) {
			frm.events.make_options(frm);
		}
	},
	make_options: function(frm){
		if(frappe.user.has_role("PlayFunction Admin"))
		{
			frm.add_custom_button("Approve", function(){
				frm.trigger('approve_qutotation');
			}, "Action")
			frm.add_custom_button("Reject", function(){
				frm.trigger('reject_qutotation');
			}, "Action")
		}
	},
	approve_qutotation:function(frm){
		frm.doc.workflow_state = "Approved"
		frm.save()
	},
	reject_qutotation:function(frm){
		frm.doc.workflow_state = "Reject"
		frm.save()	
	},
	before_submit:function(frm){
		if(frm.doc.workflow_state!='Approved'){
			frappe.throw("Quotation must be approved by Admin")
		}
	},
	on_submit:function(frm){
		frappe.model.open_mapped_doc({
				method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
				frm: cur_frm
		})
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

