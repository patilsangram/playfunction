import frappe


def submit(doc, method):
    receipient = frappe.get_doc("Notification","Sales Invoice")
    cc = []
    # subject = receipient.subject.format(doc.name)
    for i in receipient.recipients:
        cc.append(i.cc)
    frappe.sendmail(
                    # recipients = "pratik.m@indictrans.in",
                    recipients = frappe.db.get_value("Customer",{"name":doc.customer},"user"),
                    cc = cc,
                    subject = receipient.subject,
                    message = frappe.render_template(receipient.message,{"doc":doc})
                    # attachments= print_att
                    )
