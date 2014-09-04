# Copyright (c) 2013, Saurabh and Contributors
# See license.txt

import frappe
import unittest

test_records = frappe.get_test_records('Point Transaction')

class TestPointTransaction(unittest.TestCase):
	pass
