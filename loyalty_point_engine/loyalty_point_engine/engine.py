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
		rule_details[rule] = frappe.db.sql("""select amount, points_earned, is_lp_mumtiplier, referred_points 
			from `tabRule` where name = '%s'"""%rule, as_dict=1)[0]

	return rule_details

def calulate_points(rule_details, sales_invoice_details):
	points_earned = 0
	for rule in rule_details:
		frappe.errprint(rule)
		points_earned += calc_basic_points(rule_details[rule], sales_invoice_details.net_total_export)

		if rule_details[rule].get('is_lp_mumtiplier') != 0:
			points_earned += mumtiplier_points(rule_details[rule], sales_invoice_details.net_total_export)
		frappe.errprint(points_earned)
	make_point_entry(points_earned, rule_details, sales_invoice_details)

def calc_basic_points(rule_details, inv_amount):
	return rule_details.get('points_earned')*cint(inv_amount/rule_details.get('amount'))

def mumtiplier_points(rule_details, inv_amount):
	""" Need to create structure for multiplier  """

def make_point_entry(points_earned, rule_details, sales_invoice_details):
	frappe.errprint(points_earned)
	create_transaction_entry()
	create_jv()

def create_transaction_entry():
	pass

def create_jv():
	pass