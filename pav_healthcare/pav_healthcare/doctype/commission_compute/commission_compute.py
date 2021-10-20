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
					if item.external_doctor:
						doc.db_set("external", 1, update_modified=False)
					if item.internal_doctor:
						doc.db_set("internal", 1, update_modified=False)
					if item.marketer:
						doc.db_set("marketer", 1, update_modified=False)
				else:
					if item.external_doctor:					
						doc.db_set("external", 0, update_modified=False)
					if item.internal_doctor:
						doc.db_set("internal", 0, update_modified=False)
					if item.marketer:
						doc.db_set("marketer", 0, update_modified=False)

	def on_cancel(self):
		self.make_gl_entries(cancel=True)

	def make_gl_entries(self, cancel = False):
		gl_entries=[]
		self.make_commissions_gl_entry(gl_entries,mark_as_calc=cancel)
		if gl_entries:
			make_gl_entries(gl_entries, cancel = cancel)

	def make_commissions_gl_entry(self, gl_entries,mark_as_calc=True):
		for row in self.get("items"):
			doc = frappe.get_doc('Sales Invoice Item',row.sii_no)
			total=0.0
			if row.total_external_doctor>0.0:
				# doc.db_set("external", mark_as_calc, update_modified=False)
				gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": self.external_account,
						"party_type": "Sales Partner",
						"party": row.external_doctor,						
						"credit": flt((row.total_external_doctor*self.exchange_rate),2),
						"credit_in_account_currency":flt(( row.total_external_doctor),2),
						"account_currency":row.transaction_currency,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"remarks": self.get("remarks") or _("Accounting Entry for External Doctor"),
						"cost_center": row.cost_center,
						"project": row.project 
					}, item=self))
				total+=flt(( row.total_external_doctor),2)
			if row.total_internal_doctor>0.0:
				# doc.db_set("internal", mark_as_calc, update_modified=False)
				gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": self.internal_account,
						"party_type": "Healthcare Practitioner",
						"party": row.internal_doctor,						
						"credit": flt((row.total_internal_doctor*self.exchange_rate),2),
						"credit_in_account_currency": flt((row.total_internal_doctor),2),
						"account_currency":row.transaction_currency,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"remarks": self.get("remarks") or _("Accounting Entry for Internal Doctor"),
						"cost_center": row.cost_center,
						"project": row.project 
					}, item=self))
				total+=flt(( row.total_internal_doctor),2)
			if row.total_marketer:
				# doc.db_set("marketer", mark_as_calc, update_modified=False)
				gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": self.marketer_account,
						"party_type": "Sales Partner",
						"party": row.marketer,						
						"credit": flt((row.total_marketer*self.exchange_rate),2),
						"credit_in_account_currency": flt((row.total_marketer),2),
						"account_currency":row.transaction_currency,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"remarks": self.get("remarks") or _("Accounting Entry for Marketer"),
						"cost_center": row.cost_center,
						"project": row.project 
					}, item=self))	
				total+=flt(( row.total_marketer),2)
			if total>0.0:		
				gl_entries.append(
					self.get_gl_dict({
						"posting_date":self.posting_date,
						"account": row.item_account,
						"debit": flt((total*self.exchange_rate),2),
						"debit_in_account_currency": flt((total),2),
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"remarks": self.get("remarks") or _("Accounting Entry for commissions"),
						"cost_center": row.cost_center,
						"project": row.project 
					}, item=self))
		# frappe.msgprint("gl_entries={0}".format(gl_entries))

	def get_commissions_list(self):
		
		return frappe.db.sql("""select sii.external,sii.internal,sii.marketer, si.name as sale,sii.item_code,sii.item_name,sii.qty,sii.rate,si.sales_partner_name,sii.income_account,sii.cost_center,
		(select pmr.practitioner from `tabPatient Medical Record` pmr where pmr.sales_invoice=si.name and pmr.item=sii.item_code limit 1) as practitioner,
		(select pmr.amount from `tabPatient Medical Record` pmr where pmr.sales_invoice=si.name and pmr.item=sii.item_code limit 1) as practitioner_rate,sii.name as sii_no,sp.sales_partner_marketer
		
		from `tabSales Invoice Item` sii
		INNER JOIN  `tabSales Invoice` si 
		ON sii.parent=si.name
		INNER JOIN  `tabSales Partner` sp
		ON si.sales_partner_name=sp.name

		INNER JOIN  `tabAccount` acc
		ON sii.income_account=acc.name
		
		where si.currency=%s and acc.account_currency=%s and si.posting_date >= %s and si.posting_date <= %s and si.docstatus=1 and sii.external=0 and sii.internal=0 and sii.marketer=0
		
		 """,[self.transaction_currency,self.transaction_currency,self.from_date,self.to_date], as_dict=True)

	def get_exchange_rate(self):
		return frappe.db.sql("""select exchange_rate as rate
		from `tabCurrency Exchange`
		where from_currency= %s and to_currency= %s order by date desc
		 """,[self.c_currency,self.transaction_currency], as_dict=True)

	def fill_commission(self):
		self.items=None
		self.transaction_currency=frappe.db.get_single_value("PAV Healthcare Settings", "transaction_currency")
		exchange_rate=self.get_exchange_rate()
		self.exchange_rate=exchange_rate[0].rate
		# frappe.msgprint(transaction_currency)
		commissions = self.get_commissions_list()
		if not commissions:
				frappe.msgprint(_("No commissions"))
		for d in commissions:
			row=self.append('items', {})
			row.transaction_currency=self.transaction_currency
			row.sales_invoice=d.sale
			row.item_code=d.item_code
			row.item_name=d.item_name
			row.qty=d.qty
			row.amount=d.rate
			if not d.external:
				row.external_doctor=d.sales_partner_name
			if not d.internal:
				row.internal_doctor=d.practitioner
			details=get_item_detail(self.company,d.item_code)
			# frappe.msgprint(frappe.as_json(details))
			row.item_account=d.income_account
			row.item_group=details['item_group']
			row.cost_center=d.cost_center
			# row.project=details['project']
			row.total_internal_doctor=0.0
			row.external_doctor_amount=0.0
			row.market_amount=0.0
			if d.practitioner:
				rate=get_item_commission(item=d.item_code,item_group=row.item_group,party=d.practitioner,party_type='Healthcare Practitioner')
				# row.internal_party_amount=flt(n*self.exchange_rate)
				row.total_internal_doctor=flt(rate*row.qty)
			
			if not d.marketer:
				if d.sales_partner_name:
					rate=get_item_commission(item=d.item_code,item_group=row.item_group,party=d.sales_partner_name,partner_type='Doctor',party_type='Sales Partner')				
					# row.external_doctor_amount= flt(ex *self.exchange_rate)
					row.total_external_doctor=flt(rate *row.qty)
					if d.sales_partner_marketer:
						row.marketer=d.sales_partner_marketer
						rate=get_item_commission(item=d.item_code,item_group=row.item_group,partner_type='Marketer',party_type='Sales Partner')
						# row.market_amount=flt(m*self.exchange_rate)
						row.total_marketer=flt(rate*row.qty)

			# frappe.msgprint("{0},{1}.{2}".format(row.internal_amount,row.external_doctor_amount,row.market_amount))
			row.total_commission=(row.total_internal_doctor+row.total_external_doctor+row.total_marketer)*self.exchange_rate
			row.remaining_amount=row.amount-row.total_commission
			row.sii_no=d.sii_no
		if not self.external_account: self.external_account=frappe.db.get_single_value("PAV Healthcare Settings", "external_doctor_account")
		if not self.internal_account: self.internal_account=frappe.db.get_single_value("PAV Healthcare Settings", "internal_doctor_account")
		if not self.marketer_account: self.marketer_account=frappe.db.get_single_value("PAV Healthcare Settings", "marketer_account")
		
		self.save()		
		self.reload()

# def get_marketer(dr):
# 	return frappe.db.sql("""select sales_partner_marketer from `tabSales Partner` where partner_type='Doctor'
# 	and name=%s 
# 	""",dr, as_dict=True)

def get_item_commission(item=None,item_group=None, party=None,partner_type=None,party_type=None):
	# it_doc = frappe.db.sql("""select rate from `tabItem Commission` where item=%s and party is null and partner_type is null and party_type is null and disabled=0 limit 1""",[item])	
	it_doc=None
	if not it_doc and item and partner_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item' and item=%s and partner_type=%s and disabled=0 limit 1""",[item,partner_type])
	if not it_doc and item_group and partner_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item Group' and item=%s and partner_type=%s and disabled=0 limit 1""",[item_group,partner_type])
	if not it_doc and item and party and party_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item' and item=%s and party=%s and party_type=%s and disabled=0 limit 1""",[item,party,party_type])
	if not it_doc and item_group and party and party_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item Group' and item=%s and party=%s and party_type=%s and disabled=0 limit 1""",[item_group,party,party_type])
	if not it_doc and item and party_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item' and item=%s and party_type = %s and party is null and disabled=0 limit 1""",[item,party_type])
	if not it_doc and item_group and party_type:
		it_doc= frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item Group' and item=%s and party_type = %s and party is null and disabled=0 limit 1""",[item_group,party_type])
	if not it_doc:
		it_doc = frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item' and item=%s and party is null and partner_type is null and party_type is null and disabled=0 limit 1""",[item])	
	if not it_doc:
		it_doc = frappe.db.sql("""select rate from `tabItem Commission` where item_type='Item Group' and item=%s and party is null and partner_type is null and party_type is null and disabled=0 limit 1""",[item_group])	

	
	rate=0.0
	if it_doc:
		rate=it_doc[0][0]
	# frappe.msgprint("rate={0}".format(rate))
	return rate



def get_item_details(args=None):
	item = frappe.db.sql("""select i.name,i.item_group
			from `tabItem` i 
			where i.name=%s """,(args.get('item_code')), as_dict = True)
	if not item:
			frappe.throw(_("Item {0} is not active or end of life has been reached").format(args.get("item_code")))

	return item[0]

from erpnext.accounts.utils import get_company_default

@frappe.whitelist()
def get_item_detail(company,item_code):
	item_dict = {}
	item_details = get_item_details({'item_code': item_code, 'company': company})
	# item_dict['income_account'] = (item_details.get("income_account") or get_item_group_defaults(item_code, company).get("income_account") or 
			# get_company_default(company, "default_income_account") or frappe.get_cached_value('Company',  company, 
			# "default_income_account"))
	item_dict['item_group']=item_details.get('item_group')
	# item_dict['cost_center'] = item_details.get('income_cost_center')
	return item_dict