# Copyright (c) 2013, Saurabh and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.accounts.party import create_party_account
from frappe import _
from frappe.utils import cint
from loyalty_point_engine.loyalty_point_engine.engine import initiate_point_engine
from loyalty_point_engine.loyalty_point_engine.accounts_handler import create_account_head, manage_accounts_and_lead, make_gl_entry, cancle_jv
from loyalty_point_engine.loyalty_point_engine.custom_script_handler import create_lead, cancle_point_transactions

def grab_jv_and_invoice_details(doc, method):
	si = get_invoice_details(doc.get('entries'))
	if si:
		initiate_point_engine(doc, si)

def get_invoice_details(entries):
	for entry in entries:
		if entry.against_invoice and entry.mode:
			return frappe.get_doc('Sales Invoice', entry.against_invoice)
			break

def referral_management(doc, method):
	if not doc.get('__islocal') and doc.get('__islocal') != None:
		if doc.referral_name:
			lead = create_lead(doc)
			create_account_head(lead)

	if doc.lead_name:
		manage_accounts_and_lead(doc)

def create_acc_payable_head(doc, method):
	# To create libility account head and which is used to capture the loyality points against the customer
	# if not doc.get('__islocal') and doc.get('__islocal') != None:
	create_account_head(doc)

def grab_invoice_details(doc, method):
	if doc.redeem_points:
		point_validation(doc)
		make_gl_entry(doc)
	initiate_point_engine(doc)

def point_validation(doc):
	limit_exceed(doc.total_earned_points, doc.redeem_points, doc.net_total_export)

def limit_exceed(earned_points, redeem_points, net_total_export):
	if cint(redeem_points) > cint(earned_points):
		frappe.msgprint(" Redeemption limit exceeded ", raise_exception=1)
	if cint(redeem_points) < 0:
		frappe.msgprint(" Negative points redeemption not allowed", raise_exception=1)
	if cint(redeem_points) > cint(net_total_export):
		frappe.msgprint(" Can't redeem more points than net total", raise_exception=1)

@frappe.whitelist()
def get_points(customer):
	points = frappe.db.sql("""select sum(points) from `tabPoint Transaction` where ref_name = '%s'"""%(customer), as_list=1)
	return {
		"points": ((len(points[0]) > 1) and points[0] or points[0][0]) if points else None
	}

@frappe.whitelist()
def get_referral(customer):
	referral_name = frappe.db.sql("""select  COALESCE(concat(nullif(referral,''), '@Customer'), concat(referral_lead, '@Lead'), '')
		from tabCustomer where name = '%s'"""%(customer))
	return {
		"referral": ((len(referral_name[0]) > 1) and referral_name[0] or referral_name[0][0]) if referral_name else None
	}

def cancle_points_and_jv(doc, method):
	si = get_invoice_details(doc.get('entries'))
	if si:
		cancle_jv(si)
		cancle_point_transactions(si)