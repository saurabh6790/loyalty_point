# Copyright (c) 2013, Saurabh and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def get_referral(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select name, customer_name, customer_group, territory from `tabCustomer`
		where docstatus < 2
			and ({key} like %(txt)s
				or customer_name like %(txt)s)
			and name != '{cust_name}'
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			if(locate(%(_txt)s, customer_name), locate(%(_txt)s, customer_name), 99999),
			name, customer_name
		limit %(start)s, %(page_len)s""".format(**{
			"key": searchfield,
			"cust_name": filters.get('cust_name')
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})

def create_lead(doc):
	lead = frappe.new_doc("Lead")
	lead.lead_name =  doc.referral_name
	lead.mobile_no = doc.phone_number
	lead.save()
	post_lead_creation(doc, lead)
	return lead

def post_lead_creation(doc, lead):
	frappe.db.sql(" update tabCustomer set referral_lead = '%s' where name = '%s'"%(lead.name, doc.name))

@frappe.whitelist()
def get_payment_modes():
	return frappe.db.sql("select name from `tabMode of Payment`", as_list=1)


def cancle_point_transactions(si):
	frappe.db.sql("""update `tabPoint Transaction` set docstatus = 2 where invoice_number = '%s'"""%(si.name))
	frappe.db.sql("""commit""")
		
		