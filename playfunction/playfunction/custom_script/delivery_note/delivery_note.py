import frappe


def submit(doc, method):
    receipient = frappe.get_doc("Notification","Delivery Note")
    cc = []
    for i in receipient.recipients:
        cc.append(i.cc)
    sales_invoice = doc.items
    si_name = sales_invoice[0].against_sales_invoice
    order_date = frappe.db.get_value("Sales Invoice",{"name":si_name},"posting_date")
    frappe.sendmail(
                    recipients = frappe.db.get_value("Customer",{"name":doc.customer},"user"),
                    cc = cc,
                    subject = receipient.subject,
                    message = frappe.render_template(receipient.message,{"doc":doc,"si":si_name,"date":order_date})
                    # attachments= print_att
                    )
