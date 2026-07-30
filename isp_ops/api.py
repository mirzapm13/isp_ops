import hmac
import hashlib
from urllib.parse import parse_qsl, unquote
import json
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


# @frappe.whitelist(allow_guest=True)
# def telegram_login():
    # data = frappe.local.form_dict
    # init_data = data.get("initData")
    # bot_token = "YOUR_TELEGRAM_BOT_TOKEN"  # Or fetch from site config / settings
    
    # if not init_data:
    #     frappe.throw("Missing Telegram initData", frappe.PermissionError)

    # try:
    #     # 1. Validate Telegram initData signature
    #     parsed = dict(parse_qsl(init_data))
    #     hash_str = parsed.pop('hash', None)
        
    #     # Sort keys and create data check string
    #     data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(parsed.items())])
        
    #     secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    #     calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
    #     if calculated_hash != hash_str:
    #         frappe.throw("Invalid Telegram Authentication Signature", frappe.PermissionError)
            
    #     # 2. Extract Telegram User ID
    #     user_data = json.loads(parsed.get('user', '{}'))
    #     telegram_id = str(user_data.get('id'))
        
    #     if not telegram_id:
    #         frappe.throw("Telegram User ID not found", frappe.PermissionError)
            
    #     # 3. Find Frappe User linked to this Telegram ID
    #     user_email = frappe.db.get_value("Telegram User", {"telegram_id": telegram_id}, "user")
        
    #     if not user_email:
    #         frappe.throw(f"No Frappe account linked to Telegram ID: {telegram_id}", frappe.PermissionError)
            
    #     # 4. Programmatically log the user into Frappe
    #     frappe.local.login_manager.login_as(user_email)
        
    #     return {"status": "success", "user": user_email}

    # except Exception as e:
    #     frappe.log_error(title="Telegram Login Failed", message=str(e))
    #     frappe.throw("Authentication failed", frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
def telegram_login():
    data = frappe.local.form_dict
    init_data = data.get("initData")
    bot_token = "6720700580:AAGAaJd19zOVEaPQpgXFe6kNusOlDlsxhcE"  # Replace with your actual bot token
    
    if not init_data:
        frappe.throw("Missing Telegram initData", frappe.PermissionError)

    try:
        # 1. Parse and unquote query parameters properly
        vals = {k: unquote(v) for k, v in [s.split('=', 1) for s in init_data.split('&')]}
        hash_str = vals.pop('hash', None)
        
        if not hash_str:
            frappe.throw("Hash missing from initData", frappe.PermissionError)

        # 2. Build sorted data check string (keys alphabetical, joined by newline)
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(vals.items()))
        
        # 3. Derive secret key using HMAC-SHA256 with key="WebAppData" and value=bot_token
        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        
        # 4. Calculate final hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash != hash_str:
            frappe.log_error("Telegram Auth Mismatch", f"Calculated: {calculated_hash} vs Received: {hash_str}")
            frappe.throw("Invalid Telegram Authentication Signature", frappe.PermissionError)
            
        # 5. Extract User Data
        user_data_raw = vals.get('user', '{}')
        user_data = json.loads(user_data_raw)
        telegram_username = user_data.get('username', 'No Username')
        telegram_id = str(user_data.get('id', ''))

        return {
            "status": "success",
            "telegram_username": telegram_username,
            "telegram_id": telegram_id
        }

    except Exception as e:
        frappe.log_error(title="Telegram Login Exception", message=str(e))
        frappe.throw(f"Authentication failed: {str(e)}", frappe.PermissionError)