import frappe


def submit(doc, method):
    receipient = frappe.get_doc("Notification","Delivery Note")
    cc = []
    for i in receipient.recipients:
        cc.append(i.cc)
    sales_invoice = doc.items
    frappe.sendmail(
                    recipients = frappe.db.get_value("Customer",{"name":doc.customer},"user"),
                    cc = cc,
                    subject = receipient.subject,
                    message = frappe.render_template(receipient.message,{"doc":doc,"si":sales_invoice[0].against_sales_invoice})
                    # attachments= print_att
                    )
