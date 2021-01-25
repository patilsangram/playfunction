import frappe


def submit(doc, method):
    notify_doc = frappe.get_doc("Notification", "Delivery Note")
    if notify_doc:
        cc = []
        print_doc = frappe.get_print('Delivery Note', doc.name, doc = None, print_format = notify_doc.print_format,as_pdf=1)
        print_att = [{'fname':doc.name +".pdf",'fcontent':print_doc}]
        for i in notify_doc.recipients:
            cc.append(i.cc)

        sales_invoice = doc.items
        si_name = sales_invoice[0].against_sales_invoice
        order_date = frappe.db.get_value("Sales Invoice",{"name":si_name},"posting_date")
        frappe.sendmail(
            recipients = cc,#frappe.db.get_value("Customer",{"name":doc.customer},"user") or cc,
            #cc = cc,
            subject = notify_doc.subject,
            message = frappe.render_template(notify_doc.message,{"doc":doc,"si":si_name,"date":order_date}),
            attachments= print_att
        )
