# import frappe
# from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


# def execute():
#     create_custom_fields(
#         {
#             "HD Ticket": [
#                 {
#                     "fieldname": "installation_request",
#                     "label": "Installation Request",
#                     "fieldtype": "Link",
#                     "options": "Installation Request",
#                     "insert_after": "ticket_type",
#                 }
#             ]
#         },
#         update=True,
#     )