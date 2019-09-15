import frappe

@frappe.whitelist()
def set_blog_category(doc, method):
	# set category as blog category in Blog Post
	if doc.category and not doc.blog_categoty:
		doc.blog_categoty = doc.category