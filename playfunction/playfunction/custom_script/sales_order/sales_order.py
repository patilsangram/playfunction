import frappe


def submit(doc, method):
    receipient = frappe.get_doc("Notification","Sales Order")
    cc = []
    for i in receipient.recipients:
        cc.append(i.cc)
    frappe.sendmail(
                    recipients = frappe.db.get_value("Customer",{"name":doc.customer},"user"),
                    cc = cc,
                    subject = receipient.subject,
                    message = receipient.message
                    # attachments= print_att
                    )
