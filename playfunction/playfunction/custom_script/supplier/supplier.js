frappe.ui.form.on("Supplier","onload", function(frm, cdt, cdn) { 
	//make amount owed readonly
    frappe.meta.get_docfield("Amount Owed","invoice_no", cur_frm.doc.name).read_only=true;
    frappe.meta.get_docfield("Amount Owed","amount_owed", cur_frm.doc.name).read_only=true;
    frappe.meta.get_docfield("Amount Owed","date_owed", cur_frm.doc.name).read_only=true;
	refresh_field("amount_owed");
   	//find total of amount owed
   	var total=0;
    frm.doc.amount_owed.forEach(function(d) {
        total = total+ d.amount_owed;
    });
    frm.set_value("total_amount_owed",total);
    //hide links
    $(".grid-add-row").hide();
    $(".grid-row-check").hide();
    $(".grid-remove-rows").hide();

});