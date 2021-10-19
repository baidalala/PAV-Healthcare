// Copyright (c) 2016, Partner Consulting Solutions and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Commissions Compute"] = {
	"filters": [
		{
			"fieldname":"posting_date",
			"label": __("Posting Date"),
			"fieldtype": "Date",
			
		},
		{
			"fieldname":"item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			
		},
		{
			"fieldname":"party_type",
			"label": __("Party Type"),
			"fieldtype": "Link",
			"options": "Party Type",
			
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "DynamicLink",
			"options": "party_type",
			
		},
	



	]
};
