import frappe


# @frappe.whitelist()
# def create_retail_customer(installation_request):
#     ir = frappe.get_doc("Installation Request", installation_request)

#     customer = frappe.new_doc("Retail Customer")

#     FIELD_MAP = {
#         # Basic
#         "request_number": "installation_request",
#         "applicant_name": "customer_name",
#         "phone_number": "phone_number",
#         "alternate_phone": "alternate_phone",
#         "email": "email",
#         "nik": "nik",

#         # Address
#         "full_address": "full_address",
#         "google_maps_url": "google_maps_url",
#         "latitude": "latitude",
#         "longitude": "longitude",

#         # Service
#         "internet_package": "internet_package",

#         # Network
#         "technology": "technology",
#         "onu_brand": "onu_brand",
#         "serial_number": "serial_number",
#         "mac_address": "mac_address",
#         "odp_name": "odp_name",
#         "fiber_distance": "fiber_distance",
#         "dropcore_length": "dropcore_length",

#         # WiFi
#         "wifi_ssid": "wifi_ssid",
#         "wifi_password": "wifi_password",
#         "pppoe_username": "pppoe_username",
#         "pppoe_password": "pppoe_password",
#     }

#     for source, target in FIELD_MAP.items():
#         customer.set(target, ir.get(source))

#     # Fields requiring different logic
#     customer.customer_id = frappe.generate_hash(length=8).upper()
#     customer.installation_request = ir.name
#     customer.installation_date = ir.installation_date
#     customer.activation_date = ir.installation_date
#     customer.customer_status = "Active"

#     customer.service_notes = ir.installation_notes
#     customer.customer_notes = ir.survey_notes

#     customer.insert(ignore_permissions=True)
#     frappe.db.commit()

#     return customer.name

@frappe.whitelist()
def submit_installation_request(installation_request):

    ir = frappe.get_doc("Installation Request", installation_request)

    if ir.status != "Draft":
        frappe.throw("Installation Request has already been submitted.")

    try:
        hd_ticket = create_hd_ticket(ir)

        # ir.helpdesk_ticket = hd_ticket.name
        ir.status = "Submitted"
        ir.hd_ticket = hd_ticket.name
        ir.save(ignore_permissions=True)

        frappe.db.commit()

    except Exception:
        frappe.db.rollback()
        raise

    return hd_ticket.name

@frappe.whitelist()
def create_hd_ticket(ir):

    ticket = frappe.new_doc("HD Ticket")

    ticket.subject = ir.name
    ticket.ticket_type = "Installation"
    ticket.custom_reference_type = "Installation Request"
    ticket.custom_reference_name = ir.name

    ticket.description = build_installation_description(ir)

    ticket.insert(ignore_permissions=True)

    return ticket

@frappe.whitelist()
def build_installation_description(ir):
    description = f"""
## Customer

Name: {ir.applicant_name}

Phone: {ir.phone_number}

Address:
{ir.full_address}

Package:
{ir.internet_package}

Google Maps:
{ir.google_maps_url}
"""
    return description