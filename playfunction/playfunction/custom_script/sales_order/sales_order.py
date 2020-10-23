import frappe


def submit(doc, method):
    try:
        receipient = frappe.get_doc("Notification","Sales Order")
        cc = []
        party_name = doc.customer if doc.customer != "" else ""
        print_doc = frappe.get_print('Sales Order', doc.name, doc = None, print_format = receipient.print_format,as_pdf=1)
        print_att = [{'fname':doc.name +".pdf",'fcontent':print_doc}]
        for i in receipient.recipients:
            cc.append(i.cc)
        frappe.sendmail(
        # recipients = "pratik.m@indictrans.in",
        recipients = frappe.db.get_value("Customer",{"name":party_name},"user"),
        cc = cc,
        subject = receipient.subject,
        message = frappe.render_template(receipient.message,{"doc":doc}),
        attachments= print_att
        )
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback() , title="Error while sending mail: Sales Order")
        raise
