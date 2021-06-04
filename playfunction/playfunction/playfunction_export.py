import frappe
import re, csv, os
from frappe import _
from frappe.utils import cstr, formatdate, format_datetime, parse_json, cint, flt
from frappe.utils.csvutils import UnicodeWriter
from frappe.contacts.doctype.address.address import get_address_display

@frappe.whitelist()
def export_data(dt, dn, file_type='Excel'):
	exporter = DataExporter(dt, dn, file_type='Excel')
	exporter.build_response()

class DataExporter:
	def __init__(self, dt, dn, file_type='Excel'):
		self.dt = dt
		self.dn = dn

	def build_response(self):
		self.writer = UnicodeWriter()
		self.writer.writerow([''])

		# get data
		data_rows = self.add_data_row()

		for row in data_rows:
			self.writer.writerow(row)
		
		filename = self.dn
		with open(filename, 'wb') as f:
			f.write(cstr(self.writer.getvalue()).encode('utf-8'))
		f = open(filename)
		reader = csv.reader(f)

		from frappe.utils.xlsxutils import make_xlsx
		xlsx_file = make_xlsx(reader, 'Data Export')

		f.close()
		os.remove(filename)

		# write out response as a xlsx type
		frappe.response['filename'] = self.dn + '.xlsx'
		frappe.response['filecontent'] = xlsx_file.getvalue()
		frappe.response['type'] = 'binary'

	def add_data_row(self):
		data_rows = []
		data_rows.extend(self.get_linked_records())
		data_rows.extend(self.items_and_totals())
		return data_rows

	def get_linked_records(self):
		# quote -> order -> invoice -> DN
		def get_next_doc(dt, dn):
			item_tbl = {
				"Quotation": {"item_tbl": "Sales Order Item", "ref_col": "prevdoc_docname"},
				"Sales Order": {"item_tbl": "Sales Invoice Item", "ref_col": "sales_order"},
				"Sales Invoice": {"item_tbl": "Delivery Note Item", "ref_col": "against_sales_invoice"}
			}

			next_doc = frappe.db.sql("select parent from `tab{}` \
				where {} = '{}'".format(
					item_tbl.get(dt).get('item_tbl'),
					item_tbl.get(dt).get('ref_col'), dn), as_dict=True)
			if len(next_doc):
				return next_doc[0].get("parent")
			return ''

		linked_records = []
		customer_po = invoice_no = delivery_note = ''
		
		if self.dt == "Quotation":
			sales_order = get_next_doc("Quotation", self.dn)
		else:
			sales_order = self.dn

		if sales_order:
			invoice_no = get_next_doc("Sales Order", sales_order)
			if invoice_no:
				po_data = frappe.db.sql("select po_no from `tabSales Invoice`\
					where name = '{}'".format(invoice_no), as_dict=True)
				if len(po_data):
					customer_po = po_data[0].get("po_no")

		if invoice_no:
			delivery_note = get_next_doc("Sales Invoice", invoice_no)

		linked_records.append([customer_po, 'מספר הזמנה לקוח'])
		linked_records.append([invoice_no, 'מספר חשבונית'])
		linked_records.append([delivery_note, 'מספר תעודת משלוח'])
		linked_records.append([''])
		return linked_records
	
	def items_and_totals(self):
		data_rows = []
		doc = frappe.get_doc(self.dt, self.dn)

		customer = doc.get("party_name") if self.dt == "Quotation" else doc.get("customer")
		customer_addr = doc.get("address_display") or ''
		shipping_address = doc.get("shipping_address") or ''
		transaction_date = formatdate(doc.get("transaction_date"))

		if not customer_addr:
			addresses = frappe.db.sql("select parent from `tabDynamic Link` where \
				link_doctype = 'Customer' and link_name = '{}' order by modified desc limit 1\
			".format(customer), as_dict=True)
			if len(addresses):
				customer_addr = get_address_display(addresses[0]["parent"])

		customer_addr = customer_addr.replace("<br>", " ")
		shipping_address = shipping_address.replace("<br>", " ")

		headers = ['מ·ק', 'מספר מסמך', 'תאריך', 'שם לקוח', 'סך הכל  (ללא מע"מ)', 'מע"מ', 'כתובת' , 'קוד מוצר', 'תאור פריט', 'כמות', 'נטו ליחידה', 'סה"כ נטו']
		data_rows.append(headers)

		#items
		for item in doc.get("items", []):
			data_rows.append([
				item.get("idx"),
				self.dn,
				transaction_date,
				customer_addr,
				flt(doc.get("total", 0)),
				flt(doc.get("total_taxes_and_charges", 0)),
				shipping_address,
				item.get("item_code"),
				item.get("item_name"),
				cint(item.get("qty")),
				flt(item.get("rate")),
				flt(item.get("amount"))
			])

		data_rows.append([''])
		data_rows.append(['']*11 + [flt(doc.get("total")), 'סך הכל ללא מעמ'])
		data_rows.append(['']*11 + [flt(doc.get("total_taxes_and_charges")), 'מעמ'])
		data_rows.append(['']*11 + [flt(doc.get("grand_total")), 'סך הכל לתשלום'])

		return data_rows