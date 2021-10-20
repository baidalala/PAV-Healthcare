// Copyright (c) 2016, Partner Consulting Solutions and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Commission"] = {
	"filters": [
		{
			"fieldname":"item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": 'Item',
		
			
		},
		{
			"fieldname":"item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group",
			// "reqd": 1,
			
		},
		{
			"fieldname":"party_type",
			"label": __("Party Type"),
			"fieldtype": "Link",
			"options":"Party Type"
			// "options": '\nHealthcare Practitioner\nSales Partner',
			
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "DynamicLink",
			"options": "party_type",
			
		},

	]
};
