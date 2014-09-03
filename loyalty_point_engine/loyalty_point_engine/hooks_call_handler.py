# Copyright (c) 2013, Saurabh and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.accounts.party import create_party_account
from frappe import _
from loyalty_point_engine.loyalty_point_engine.engine import initiate_point_engine

def create_acc_payable_head(doc, method):
	if not doc.get('__islocal') and doc.get('__islocal') != None:
		create_account_head(doc)

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

def grab_invoice_details(doc, method):
	initiate_point_engine(doc)

