# Copyright (c) 2013, Saurabh and contributors
# For license information, please see license.txt

# from __future__ import unicode_literals
import frappe
from frappe import _
from loyalty_point_engine.loyalty_point_engine.doctype.rule.rule import get_vsibility_setting
from frappe.utils.data import today, nowtime, cint
import time
from erpnext.accounts.utils import get_balance_on

def create_jv(voucher_details, earned_redeemed_points, debit_to, credit_to):
	"""
		Here we create Journal Voucher for two purpose, 
		1. Earned Point Allocation
		2. Redeemed Point Withdrawal

		For Earned Point Allocation: debit_to = customer's account and credit_to = company's account
		For Redeemed Point Withdrawal: debit_to = company's account and debit_to = customer's account
	"""

	jv = frappe.new_doc("Journal Voucher")
	jv.naming_series = 'JV-'
	jv.voucher_type = 'Journal Entry'
	jv.posting_date = today()
	jv.user_remark = "Loyalty Points: %s "%voucher_details.name
	jv.save()

	jvd = frappe.new_doc("Journal Voucher Detail")
	jvd.account = debit_to
	jvd.debit = earned_redeemed_points
	jvd.cost_center = frappe.db.get_value('Company', voucher_details.company, 'cost_center')
	jvd.is_advance = 'No'
	jvd.parentfield = 'entries'
	jvd.parenttype = 'Journal Voucher'
	jvd.parent = jv.name
	jvd.save()

	jvd1 = frappe.new_doc("Journal Voucher Detail")
	jvd1.account = credit_to
	jvd1.credit = earned_redeemed_points
	jvd1.cost_center = frappe.db.get_value('Company', voucher_details.company, 'cost_center')
	jvd1.is_advance = 'No'
	jvd1.parentfield = 'entries'
	jvd1.parenttype = 'Journal Voucher'
	jvd1.parent = jv.name
	jvd1.save()

	ujv = frappe.get_doc("Journal Voucher", jv.name)
	ujv.total_credit  = jv.total_debit = earned_redeemed_points
	ujv.submit()

def get_payable_acc(customer):
	return frappe.db.sql("""select name from tabAccount 
		where parent_account like '%%%s%%'
		and master_name = '%s'"""%('Accounts Payable', customer), as_list=1 , debug=1)[0][0]

def create_account_head(doc):
	party_type = ''
	company_details = frappe.db.get_value("Company", doc.company,
		["abbr", "receivables_group", "payables_group"], as_dict=True)
	if not frappe.db.exists("Account", (doc.name + " - lpt" + " - " + company_details.abbr)):
		parent_account = company_details.receivables_group \
			if party_type=="Customer" else company_details.payables_group
		if not parent_account:
			frappe.throw(_("Please enter Account Receivable/Payable group in company master"))
		# create
		account = frappe.get_doc({
			"doctype": "Account",
			'account_name': doc.name + " - lpt",
			'parent_account': parent_account,
			'group_or_ledger':'Ledger',
			'company': doc.company,
			'master_name': doc.name,
			"freeze_account": "No",
			"report_type": "Balance Sheet"
		}).insert(ignore_permissions=True)

		frappe.msgprint(_("Account Created: {0}").format(account.name))

def manage_accounts(customer):
	debit_to = get_payable_acc(customer.name) 
	credit_to = get_payable_acc(customer.lead_name)
	points = get_balance_on(credit_to)
	details = type('new_dict', (object,), {"name": "Point Adjusment" ,  "company" : customer.company})
	create_jv(details, points, debit_to, credit_to)