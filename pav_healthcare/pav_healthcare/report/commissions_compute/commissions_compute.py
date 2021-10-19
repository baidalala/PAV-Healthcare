# Copyright (c) 2013, Partner Consulting Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, throw

def execute(filters=None):
	columns, data = [], []
	args = frappe._dict()
	# if not filters.get("item_code") and not filters.get("party"):
	# 	frappe.throw(_("You Should Select at least Either Item or Party"))
	cond=''
	filter1=[]
	if filters.get("posting_date"):
		cond +=' and cc.posting_date=%s '
		filter1.append(filters.get("posting_date"))
	if filters.get("item_code"):
		cond +=' and cci.item_code=%s '
		filter1.append(filters.get("item_code"))

	# if filters.get('party_type') and not filters.get('party'):
	# 	frappe.throw(_("You Should Select Party"))
	if (filters.get("item_code") or filters.get("posting_date"))  and not filters.get("party_type") and not filters.get("party") :
		data1=frappe.db.sql("""select cci.item_code ,cci.internal_doctor as party,cci.internal_party_amount as amount, cc.name as commission_compute
			from `tabCommission Compute Item` cci 
			LEFT JOIN  `tabCommission Compute` cc 
			ON cci.parent=cc.name where cc.docstatus=1 {0}
			""".format(cond), filter1, as_dict=True)
		data2=frappe.db.sql("""select cci.item_code ,cci.external_doctor as party,cci.external_doctor_amount as amount, cc.name as commission_compute
				from `tabCommission Compute Item` cci 
				LEFT JOIN  `tabCommission Compute` cc 
				ON cci.parent=cc.name where cc.docstatus=1 {0}
				""".format(cond), filter1, as_dict=True)
		data3=frappe.db.sql("""select cci.item_code ,cci.marketer as party,cci.market_amount as amount, cc.name as commission_compute
				from `tabCommission Compute Item` cci 
				LEFT JOIN  `tabCommission Compute` cc 
				ON cci.parent=cc.name where cc.docstatus=1 {0}
				""".format(cond), filter1, as_dict=True)
		for d in data1:
			data.append([d.item_code,"Healthcare Practitioner",d.party,d.amount,d.commission_compute])
		for d in data2:
			data.append([d.item_code,"Sales Partner",d.party,d.amount,d.commission_compute])
		for d in data3:
			data.append([d.item_code,"Sales Partner",d.party,d.amount,d.commission_compute])

	if filters.get("party_type") and filters.get("party_type")=="Healthcare Practitioner" and filters.get("party"):
		data1={}
		cond +=' and internal_doctor=%s'
		filter1.append(filters.get("party"))

		data1=frappe.db.sql("""select cci.item_code ,cci.internal_doctor as party,cci.internal_party_amount as amount, cc.name as commission_compute
			from `tabCommission Compute Item` cci 
			LEFT JOIN  `tabCommission Compute` cc 
			ON cci.parent=cc.name where cc.docstatus=1 {0}
			""".format(cond), filter1, as_dict=True)
		for d in data1:
			data.append([d.item_code,"Healthcare Practitioner",d.party,d.amount,d.commission_compute])

	if filters.get("party_type") and filters.get("party_type")=="Sales Partner" and filters.get("party"):
		data1={}
		cond1=cond
		cond +=' and cci.external_doctor=%s '
		filter1.append(filters.get("party"))

		data1=frappe.db.sql("""select cci.item_code ,cci.external_doctor as party,cci.external_doctor_amount as amount, cc.name as commission_compute
			from `tabCommission Compute Item` cci 
			LEFT JOIN  `tabCommission Compute` cc 
			ON cci.parent=cc.name where cc.docstatus=1 {0}
			""".format(cond), filter1, as_dict=True)

		if not data1:
			cond=cond1
			filter1.pop()
			if filters.get("party"):
				cond +=' and cci.marketer=%s '
				filter1.append(filters.get("party"))
				data1=frappe.db.sql("""select cci.item_code ,cci.marketer as party,cci.market_amount as amount, cc.name as commission_compute
				from `tabCommission Compute Item` cci 
				Left JOIN  `tabCommission Compute` cc 
				ON cci.parent=cc.name where cc.docstatus=1 {0}
				""".format(cond), filter1, as_dict=True)

		for d in data1:
			data.append([d.item_code,"Sales Partner",d.party,d.amount,d.commission_compute])

	columns = get_column(filters)

	return columns, data

def get_column(filters):
	columns = [{
		"fieldname": "item_code",
		"label": _("Item"),
		"fieldtype": "Link",
		"options": "Item",
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
		"fieldname": "amount",
		"label": _("Amount"),
		"fieldtype":"Currency",
		
		"width": 100
	},
	{
		"fieldname": "commission_compute",
		"label": _("Commission Compute"),
		"fieldtype":"Link",
		"options": "Commission Compute",
		"width": 100
	}
	]
	

	return columns
