from __future__ import unicode_literals
from frappe import _

def get_data():
	return [	
		{
			"label": _("Commission"),
			"items": [
				{
					"type": "doctype",
					"name": "Commission Compute",
					"description":_("Commission Compute"),
					"onboard": 1,
				},
					{
					"type": "doctype",
					"name": "Item Commission",
					"description":_("Item Commission"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "PAV Healthcare Settings",
					"description":_("PAV Healthcare Settings"),
					"onboard": 1,
				},
				
			]
		},
		
	]
