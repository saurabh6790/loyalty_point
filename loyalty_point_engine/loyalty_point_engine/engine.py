# Copyright (c) 2013, Saurabh and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from loyalty_point_engine.loyalty_point_engine.doctype.rule.rule import get_vsibility_setting
from frappe.utils.data import today, nowtime, cint
import time
import itertools

def initiate_point_engine(sales_invoice_details):
	valid_rules = get_applicable_rule()
	rule_details = get_ruel_details(valid_rules)
	calulate_points(rule_details, sales_invoice_details)

def get_applicable_rule():
	rule_validity_checks_param = {}

	for rule in frappe.db.sql("select name from tabRule where is_active = 1 ",as_list=1):
		get_configurations(rule[0], rule_validity_checks_param)

	return check_validity(rule_validity_checks_param)

def get_configurations(rule_type, rule_validity):
	rule_validity[rule_type] = get_vsibility_setting(rule_type, only_visble_fields=1)

def check_validity(rule_validity_checks_param):
	valid_rules = []
	for rule in rule_validity_checks_param:
		rules = frappe.db.sql("select name from tabRule where %s "%make_cond(rule_validity_checks_param[rule]), as_list=1)
		valid_rules.append(list(itertools.chain(*rules)))
	rules = None
	return list(itertools.chain(*valid_rules))

def make_cond(validity_list):
	cond_list = []
	for param in validity_list:
		if 'from_date' in param:
			cond_list.append(" %s <= '%s' "%(param, today()))
		if 'to_date' in param:
			cond_list.append(" %s >= '%s' "%(param, today()))
		if 'start_time' in param:
			cond_list.append(" %s <= '%s' "%(param, nowtime()))
		if 'end_time' in param:
			cond_list.append(" %s >= '%s' "%(param, nowtime()))

	return ' and '.join(cond_list)

def get_ruel_details(rules):
	rule_details = {}
	for rule in rules:
		rule_details[rule] = frappe.db.sql("""select amount, points_earned, is_lp_mumtiplier, referred_points, multiplier 
			from `tabRule` where name = '%s'"""%rule, as_dict=1)[0]
	return rule_details

def calulate_points(rule_details, sales_invoice_details):
	points_earned = 0
	for rule in rule_details:
		points_earned += calc_basic_points(rule_details[rule], sales_invoice_details.net_total_export)
		if rule_details[rule].get('is_lp_mumtiplier') == 1:
			points_earned = multiplier_points(rule_details[rule], points_earned)
	make_point_entry(points_earned, rule_details, sales_invoice_details)

def calc_basic_points(rule_details, inv_amount):
	return rule_details.get('points_earned')*cint(inv_amount/rule_details.get('amount'))

def multiplier_points(rule_details, points_earned):
	return points_earned * cint(rule_details.get('multiplier'))

def make_point_entry(points_earned, rule_details, sales_invoice_details):
	# pass
	create_earned_points_entry(points_earned, rule_details, sales_invoice_details)
	# create_reddem_points_entry(rule_details, sales_invoice_details)
	create_jv(sales_invoice_details, points_earned)

def create_earned_points_entry(points_earned, rule_details, sales_invoice_details):
	create_point_transaction(sales_invoice_details, 'Earned', points_earned, rule_details)

def create_reddem_points_entry(rule_details, sales_invoice_details):
	create_point_transaction(sales_invoice_details)

def create_point_transaction(sales_invoice_details, type, points=None, rule_details=None):
	tran = frappe.new_doc("Point Transaction")
	tran.customer = sales_invoice_details.customer
	tran.date = today()
	tran.type = type
	tran.points = points
	tran.valied_upto = '2015-09-1'
	tran.invoice_number = sales_invoice_details.name
	tran.docstatus = 1
	tran.insert()

def create_jv(sales_invoice_details, points_earned):
	
	jv = frappe.new_doc("Journal Voucher")
	jv.naming_series = 'JV-'
	jv.voucher_type = 'Journal Entry'
	jv.posting_date = today()
	jv.user_remark = "Loyalty Point against sales %s "%sales_invoice_details.name
	jv.save()

	jvd = frappe.new_doc("Journal Voucher Detail")
	jvd.account = get_payable_acc(sales_invoice_details.customer)
	jvd.debit = points_earned
	jvd.cost_center = frappe.db.get_value('Company', sales_invoice_details.company, 'cost_center')
	jvd.is_advance = 'No'
	jvd.parentfield = 'entries'
	jvd.parenttype = 'Journal Voucher'
	jvd.parent = jv.name
	jvd.save()

	jvd1 = frappe.new_doc("Journal Voucher Detail")
	jvd1.account = frappe.db.get_value('Company', sales_invoice_details.company, 'default_cash_account')
	jvd1.credit = points_earned
	jvd1.cost_center = frappe.db.get_value('Company', sales_invoice_details.company, 'cost_center')
	jvd1.is_advance = 'No'
	jvd1.parentfield = 'entries'
	jvd1.parenttype = 'Journal Voucher'
	jvd1.parent = jv.name
	jvd1.save()

	ujv = frappe.get_doc("Journal Voucher", jv.name)
	ujv.total_credit  = jv.total_debit = points_earned
	ujv.submit()

def get_payable_acc(customer):
	return frappe.db.sql("""select name from tabAccount 
		where parent_account like '%%%s%%'
		and master_name = '%s'"""%('Accounts Payable', customer), as_list=1 , debug=1)[0][0]