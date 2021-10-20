// Copyright (c) 2021, Partner Consulting Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('PAV Healthcare Settings', {
currency: function(frm) {
	frm.set_query("external_doctor_account", function() {
	return {
		filters: {
			"account_type": "Payable",
			"company": frm.doc.company,
			"account_currency":frm.doc.currency
		}
	}
})
frm.set_query("internal_doctor_account", function() {
	return {
		filters: {
			"account_type": "Payable",
			"company": frm.doc.company,
			"account_currency":frm.doc.currency
		}
	}
})
frm.set_query("marketer_account", function() {
	return {
		filters: {
			"account_type": "Payable",
			"company": frm.doc.company,
			"account_currency":frm.doc.currency
		}
	}
})
}
});
