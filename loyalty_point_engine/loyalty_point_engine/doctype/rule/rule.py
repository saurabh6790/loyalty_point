# Copyright (c) 2013, Saurabh and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Rule(Document):
	pass

@frappe.whitelist()
def get_vsibility_setting(rule_type, only_visble_fields=0):
	field_dict = frappe.db.sql(""" select from_date, to_date, start_time, end_time  
		from `tabRule Type` 
		where name = '%s'"""%rule_type, as_dict=1)
	hide_field_list, unhide_field_list = [], []

	if len(field_dict) > 0:
		for field in field_dict[0]:
			if field_dict[0].get(field) == 0 or field_dict[0].get(field) == None:
				hide_field_list.append(field)
			if field_dict[0].get(field) == 1:
				unhide_field_list.append(field)

	if only_visble_fields == 1:
		return unhide_field_list
	else: 		
		return hide_field_list, unhide_field_list 