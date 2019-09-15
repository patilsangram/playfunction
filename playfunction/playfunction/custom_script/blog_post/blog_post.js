frappe.ui.form.on("Blog Post", {
	category: function(frm) {
		// set category as blog category
		if (frm.doc.category) {
			frm.set_value("blog_category", frm.doc.category)
		}
	}
})