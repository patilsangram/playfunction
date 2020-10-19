import frappe


def submit(doc, method):
    receipient = frappe.get_doc("Notification","Sales Order")
    cc = []
    print_doc = frappe.get_print('Sales Order', doc.name, doc = None, print_format = receipient.print_format,as_pdf=1)
    print_att = [{'fname':doc.name +".pdf",'fcontent':print_doc}]

    for i in receipient.recipients:
        cc.append(i.cc)
    frappe.sendmail(
                    recipients = frappe.db.get_value("Customer",{"name":doc.customer},"user"),
                    cc = cc,
                    subject = receipient.subject,
                    message = receipient.message,
                    attachments= print_att
                    )
