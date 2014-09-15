# Copyright (c) 2013, Saurabh and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from loyalty_point_engine.loyalty_point_engine.doctype.rule.rule import get_vsibility_setting
from frappe.utils.data import today, nowtime, cint
import time
import itertools
from loyalty_point_engine.loyalty_point_engine.accounts_handler import create_jv, get_payable_acc

def initiate_point_engine(sales_invoice_details):
	valid_rules = get_applicable_rule()
	rule_details = get_ruel_details(valid_rules)
	if rule_details:
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
	referral_points = 0
	for rule in rule_details:
		points_earned += calc_basic_points(rule_details[rule], sales_invoice_details.net_total_export)
		referral_points += calc_referral_points(rule_details[rule])
		if rule_details[rule].get('is_lp_mumtiplier') == 1:
			points_earned = multiplier_points(rule_details[rule], points_earned)

	debit_to, credit_to = get_accouts(sales_invoice_details.customer, sales_invoice_details.company)
	make_point_entry(points_earned, rule_details, sales_invoice_details, debit_to, credit_to)
	make_referred_points_entry(sales_invoice_details, referral_points)

def calc_basic_points(rule_details, inv_amount):
	return rule_details.get('points_earned')*cint(inv_amount/rule_details.get('amount'))

def multiplier_points(rule_details, points_earned):
	return points_earned * cint(rule_details.get('multiplier'))

def calc_referral_points(rule_details):
	return cint(rule_details.get('referred_points'))

def make_point_entry(points_earned, rule_details, sales_invoice_details, debit_to, credit_to):
	create_earned_points_entry(points_earned, rule_details, sales_invoice_details, debit_to, credit_to)
	create_reddem_points_entry(rule_details, sales_invoice_details, debit_to, credit_to)

def create_earned_points_entry(points_earned, rule_details, sales_invoice_details, debit_to, credit_to):
	create_point_transaction('Customer', sales_invoice_details.customer, sales_invoice_details.name,  'Earned', points_earned, rule_details)
	create_jv(sales_invoice_details, points_earned, debit_to, credit_to)

def create_reddem_points_entry(rule_details, sales_invoice_details, debit_to, credit_to):
	debit_to, credit_to = credit_to, debit_to
	create_point_transaction('Customer', sales_invoice_details.customer, sales_invoice_details.name, 'Redeem', sales_invoice_details.redeem_points)
	create_jv(sales_invoice_details, sales_invoice_details.redeem_points, debit_to, credit_to)

def create_point_transaction(ref_link, ref_name, inv, type, points, rule_details=None):
	frappe.errprint(ref_name)
	tran = frappe.new_doc("Point Transaction")
	tran.ref_link = ref_link
	tran.ref_name = ref_name	
	tran.date = today()
	tran.type = type
	tran.points = points * 1 if type == 'Earned' else -1 * points
	tran.valied_upto = '2015-09-01'
	tran.invoice_number = inv
	tran.docstatus = 1
	tran.insert()

def make_referred_points_entry(sales_invoice_details, referral_points):
	create_point_transaction(sales_invoice_details.referral, sales_invoice_details.referral_name, sales_invoice_details.name, 'Earned', referral_points)
	debit_to, credit_to = get_accouts(sales_invoice_details.referral_name, sales_invoice_details.company)
	create_jv(sales_invoice_details, referral_points, debit_to, credit_to)

def get_accouts(party, company):
	return get_payable_acc(party), frappe.db.get_value('Company', company, 'default_cash_account')