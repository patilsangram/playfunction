import frappe
from playfunction.playfunction.invoice_payment import *

def submit(doc, method):
    try:
        if frappe.session.user == "Guest":
          frappe.set_user("Administrator")
        receipient = frappe.get_doc("Notification","Sales Invoice")
        cc = []
        # subject = receipient.subject.format(doc.name)
        print_doc = frappe.get_print('Sales Invoice', doc.name, doc = None, print_format = receipient.print_format,as_pdf=1)
        print_att = [{'fname':doc.name +".pdf",'fcontent':print_doc}]
        for i in receipient.recipients:
            cc.append(i.cc)
        frappe.sendmail(
            # recipients = "pratik.m@indictrans.in",
            recipients = frappe.db.get_value("Customer",{"name":doc.customer},"user"),
            cc = cc,
            subject = receipient.subject,
            message = frappe.render_template(receipient.message,{"doc":doc}),
            attachments= print_att
            )
    except Exception as e:
        pass

def trigger_rihvit_invoice(doc, method):
    try:
        create_rihvit_invoice(doc.name)
    except Exception as e:
        pass