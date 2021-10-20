# Copyright (c) 2013, Partner Consulting Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, throw

def execute(filters=None):
	if filters.get("item_group") and filters.get("item"):
		frappe.throw("Chose Only One of these (Item or Item Group)")
	columns, data = [], []
	args = frappe._dict()
	cond='where 1=1 '
	filter1=[]
	if filters.get("item_group") and not filters.get("item"):
		cond +=' and item=%s '
		filter1.append(filters.get("item_group"))
	if filters.get("item") and not filters.get("item_group"):
		cond +=' and item=%s '
		filter1.append(filters.get("item"))
	if filters.get("party_type"):
		cond +=' and party_type=%s '
		filter1.append(filters.get("party_type"))
	if filters.get("party"):
		cond +=' and party=%s '
		filter1.append(filters.get("party"))

	data1=frappe.db.sql("""select item_type ,item,party_type,party,rate,name
		from `tabItem Commission` ic
			{0}
		""".format(cond), filter1, as_dict=True)
		

	for d in data1:
		data.append([d.item_type,d.item,d.party,d.party_type,d.rate,d.name])

	columns = get_column(filters)

	return columns, data

def get_column(filters):
	columns = [{
		"fieldname": "item_type",
		"label": _("Item"),
		"fieldtype": "Data",
		"width": 90
	},
	{
			"fieldname":"item",
			"label": _("Item"),
			"fieldtype": "Data",
		"width": 90
			
		},

	{
		"fieldname": "party_type",
		"label": _("Party Type"),
		"fieldtype":"Link",
		"options": "Party Type",
		"width": 160
	},
	{
		"fieldname": "party",
		"label": _("Party"),
		"fieldtype":"DynamicLink",
		"options": "party_type",
		"width": 160
	},
	{
		"fieldname": "rate",
		"label": _("Rate"),
		"fieldtype":"Currency",
		
		"width": 100
	},
	{
		"fieldname": "item_commission",
		"label": _("Item Commission"),
		"fieldtype":"Link",
		"options": "Item Commission",
		"width": 100
	}
	]
	

	return columns

