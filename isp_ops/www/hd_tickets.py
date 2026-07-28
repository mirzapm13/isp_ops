import frappe

def get_context(context):
    # if frappe.session.user == "Guest":
    #     frappe.local.flags.redirect_location = "/login"
    #     raise frappe.Redirect

    # 1. Fetch tickets with the dynamic link fields included
    # Note: Double-check your exact field names in Frappe. 
    # Sometimes they are named 'ref_doctype' and 'ref_name' instead of 'reference_type'.
    tickets = frappe.get_all(
        "HD Ticket",
        filters={}, 
        fields=["name", "subject", "status", "creation", "custom_reference_type", "custom_reference_name"],
        order_by="creation desc",
        limit_page_length=50
    )

    # 2. Loop through tickets and safely fetch dynamic data
    for ticket in tickets:
        # Set defaults so Jinja doesn't crash if the fields are empty
        ticket.customer_name = "N/A"
        ticket.address = "N/A"
        
        # Only proceed if the dynamic link actually has data
        if ticket.custom_reference_type and ticket.custom_reference_name:
            
            # Check which Doctype it is pointing to before fetching fields
            if ticket.custom_reference_type == "Installation Request":
                linked_data = frappe.db.get_value(
                    ticket.custom_reference_type,  # The Doctype (e.g., "Installation Request")
                    ticket.custom_reference_name,  # The Document ID (e.g., "REQ-001")
                    ["applicant_name", "full_address", "name", "phone_number", "google_maps_url", "internet_package"], 
                    as_dict=True
                )
                
                if linked_data:
                    ticket.applicant_name = linked_data.applicant_name
                    ticket.full_address = linked_data.full_address
                    ticket.installation_id = linked_data.name
                    ticket.phone_number = linked_data.phone_number
                    ticket.google_maps_url = linked_data.google_maps_url
                    ticket.internet_package = linked_data.internet_package
                    
            # elif ticket.reference_type == "Maintenance Ticket":
                # You can handle other Doctypes here if your dynamic link points to multiple things

    open_tickets=[]
    pending_tickets=[]

    for ticket in tickets:
        # Separate them based on your reference_type
        if ticket.status == "Open":
            open_tickets.append(ticket)
        elif ticket.status == "Pending":
            pending_tickets.append(ticket)

    context.tickets = tickets
    context.open_tickets = open_tickets
    context.pending_tickets = pending_tickets