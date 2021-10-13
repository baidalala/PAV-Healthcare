# -*- coding: utf-8 -*-
# Copyright (c) 2021, Partner Consulting Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _, throw
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from frappe.utils import cint, cstr, formatdate, flt, getdate, nowdate, get_link_to_form
from erpnext.accounts.general_ledger import make_gl_entries, merge_similar_entries
from erpnext.controllers.accounts_controller import AccountsController

class CommissionCompute(AccountsController):
	def on_submit(self):
		self.make_gl_entries()
		self.update_commission_check(cancel=False)
	
		# self.create_log()
	def before_cancel(self):
		self.update_commission_check(cancel=True)

	def update_commission_check(self,cancel=True):
		for item in self.get('items'):
			if item.sii_no:
				doc = frappe.get_doc('Sales Invoice Item',item.sii_no)				
				if cancel==False:
					doc.db_set("external", 1, update_modified=False)
					doc.db_set("internal", 1, update_modified=False)
					doc.db_set("marketer", 1, update_modified=False)
				else:
					doc.db_set("external", 0, update_modified=False)
					doc.db_set("internal", 0, update_modified=False)
					doc.db_set("marketer", 0, update_modified=False)
			
			

	def on_cancel(self):
		self.make_gl_entries(cancel=True)

	def make_gl_entries(self, cancel = False):

		gl_entries = self.get_gl_entries()

		if gl_entries:
			make_gl_entries(gl_entries,  cancel= cancel)

	def get_gl_entries(self, warehouse_account=None):
		gl_entries = []
		self.make_commissions_gl_entry(gl_entries)
	
		gl_entries = merge_similar_entries(gl_entries)

		return gl_entries

	def make_commissions_gl_entry(self, gl_entries):
		for row in self.get("items"):
					
			gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": row.external_account,
						"party_type": "Sales Partner",
						"party": row.external_doctor,						
						"credit": row.external_doctor_amount,
						"credit_in_account_currency": row.external_doctor_amount,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"remarks": self.get("remarks") or _("Accounting Entry for External Doctor"),
						"cost_center": row.cost_center,
						"project": row.project 
					}, item=self))
			gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": row.marketer_account,
						"party_type": "Sales Partner",
						"party": row.marketer,						
						"credit": row.market_amount,
						"credit_in_account_currency": row.market_amount,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"remarks": self.get("remarks") or _("Accounting Entry for Marketer"),
						"cost_center": row.cost_center,
						"project": row.project 
					}, item=self))
			
			gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": row.internal_account,
						"party_type": "Healthcare Practitioner",
						"party": row.internal_doctor,						
						"credit": row.internal_party_amount,
						"credit_in_account_currency": row.internal_party_amount,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"remarks": self.get("remarks") or _("Accounting Entry for Internal Doctor"),
						"cost_center": row.cost_center,
						"project": row.project 
					}, item=self))

			gl_entries.append(
				self.get_gl_dict({
					"posting_date":self.posting_date,
					"account": row.item_account,
					"debit": row.total_commission,
					"debit_in_account_currency": row.total_commission,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"remarks": self.get("remarks") or _("Accounting Entry for commissions"),
					"cost_center": row.cost_center,
					"project": row.project 
				}, item=self))

	def get_commissions_list(self):
		
		return frappe.db.sql("""select si.name as sale,sii.item_code,sii.item_name,sii.qty,sii.rate,si.sales_partner_name
		,pe.practitioner,sii.name as sii_no
		
		from `tabSales Invoice Item` sii
		INNER JOIN  `tabSales Invoice` si 
		ON sii.parent=si.name

		JOIN `tabPatient Encounter` pe
		ON pe.sales_invoice=si.name

		
		where si.posting_date between %s and %s and si.docstatus=1 and sii.external=0 and sii.internal=0 and sii.marketer=0
		
		 """,[self.from_date,self.to_date], as_dict=True)
	
	def fill_commission(self):
		self.items=None
		commissions = self.get_commissions_list()
		if not commissions:
				frappe.msgprint(_("No commissions"))
		for d in commissions:
			row=self.append('items', {})
			row.sales_invoice=d.sale
			row.item_code=d.item_code
			row.item_name=d.item_name
			row.qty=d.qty
			row.amount=d.rate
			row.external_doctor=d.sales_partner_name
			row.internal_doctor=d.practitioner
			details=get_item_detail(self.company,d.item_code)
			# frappe.msgprint(frappe.as_json(details))
			row.item_account=details['income_account']
			row.item_group=details['item_group']
			row.cost_center=details['cost_center']
			row.project=details['project']
			internal_amount=get_item_commission(d.item_code,row.item_group,d.practitioner)
			if internal_amount:
				row.internal_party_amount=internal_amount[0].rate
			external_amount=get_item_commission(d.item_code,row.item_group,d.sales_partner_name)
			if external_amount:
				row.external_doctor_amount=external_amount[0].rate
			marketer=get_marketer(d.sales_partner_name)
			if marketer:
				row.marketer=marketer[0].sales_partner_marketer
				marketer_amount=get_item_commission(d.item_code,row.item_group,row.marketer)
				if marketer_amount:
					row.market_amount=marketer_amount[0].rate
			row.total_commission=row.internal_party_amount+row.external_doctor_amount+row.market_amount
			row.remaining_amount=row.amount-row.total_commission
			row.external_account=frappe.db.get_single_value("PAV Healthcare Settings", "external_doctor_account")
			row.internal_account=frappe.db.get_single_value("PAV Healthcare Settings", "internal_doctor_account")
			row.marketer_account=frappe.db.get_single_value("PAV Healthcare Settings", "marketer_account")
			row.sii_no=d.sii_no

def get_marketer(dr):
	return frappe.db.sql("""select sales_partner_marketer from `tabSales Partner` where partner_type='Doctor'
	and name=%s 
	""",dr, as_dict=True)

def get_item_commission(item=None,item_group=None, party=None,type=None):
	
	it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item=%s
	and party=%s and disabled=0
	""",[item,party], as_dict=True)
	if not it_doc:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item=%s
		and party=%s and disabled=0
	""",[item_group,party], as_dict=True)
	if not it_doc:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item=%s  and party is null and disabled=0
	""",[item], as_dict=True)
	if not it_doc:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item=%s and party is null and disabled=0
	""",[item_group], as_dict=True)

	return it_doc



def get_item_details(args=None):
	item = frappe.db.sql("""select i.name,i.item_group, id.income_account,id.expense_account, id.default_warehouse, id.cost_center, id.project, id.project_activities 
			from `tabItem` i LEFT JOIN `tabItem Default` id ON i.name=id.parent and id.company=%s
			where i.name=%s
				and i.disabled=0
				and (i.end_of_life is null or i.end_of_life='0000-00-00' or i.end_of_life > %s)""",
			(args.get('company'), args.get('item_code'), nowdate()), as_dict = True)
	if not item:
			frappe.throw(_("Item {0} is not active or end of life has been reached").format(args.get("item_code")))

	return item[0]

from erpnext.accounts.utils import get_company_default

@frappe.whitelist()
def get_item_detail(company,item_code):
	item_dict = {}
	item_details = get_item_details({'item_code': item_code, 'company': company})
	item_dict['income_account'] = (item_details.get("income_account") or get_item_group_defaults(item_code, company).get("income_account") or 
			get_company_default(company, "default_income_account") or frappe.get_cached_value('Company',  company, 
			"default_income_account"))
	item_dict['item_group']=item_details.get('item_group')
	item_dict['cost_center'] = item_details.get('cost_center')
	item_dict['project'] = item_details.get('project')
	item_dict['project_activities'] = item_details.get('project_activities')
	return item_dict