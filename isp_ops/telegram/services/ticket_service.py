import json
import frappe


class TicketService:
	def get_installation_tickets(self, args=None):
		filters = []
		if args:
			if isinstance(args, str):
				try:
					filters = json.loads(args)
				except Exception:
					filters = []
			elif isinstance(args, list):
				filters = args

		tickets = frappe.db.get_all(
			"HD Ticket",
			fields=[
				"name",
				"subject",
				"status",
				"ticket_type",
				"custom_reference_type",
				"custom_reference_name",
				"priority",
			],
			filters=filters,
			order_by="creation desc",
			limit_page_length=50,
		)

		result = []
		for ticket in tickets:
			installation = self._get_installation(ticket)
			if not installation:
				continue

			installation_sales = self._get_installation_sales(installation.get("sales_person"))
			attachments = self._get_installation_attachments(installation.get("name"))

			result.append(
				self._build_ticket(ticket, installation, attachments, installation_sales)
			)

		return result

	def get_ticket_detail(self, ticket_no):
		ticket = frappe.db.get_value(
			"HD Ticket",
			ticket_no,
			[
				"name",
				"subject",
				"status",
				"ticket_type",
				"custom_reference_type",
				"custom_reference_name",
				"priority",
			],
			as_dict=True,
		)
		if not ticket:
			return None

		installation = self._get_installation(ticket)
		if not installation:
			return None

		installation_sales = self._get_installation_sales(installation.get("sales_person"))
		attachments = self._get_installation_attachments(installation.get("name"))

		return self._build_ticket(ticket, installation, attachments, installation_sales)

	def _get_installation(self, ticket):
		reference_type = ticket.get("custom_reference_type")
		reference_name = ticket.get("custom_reference_name")

		if reference_type != "Installation Request" or not reference_name:
			return None

		if frappe.db.exists("Installation Request", reference_name):
			doc = frappe.get_doc("Installation Request", reference_name)
			return doc.as_dict()

		return None

	def _get_installation_sales(self, name):
		if not name:
			return None
		return frappe.db.get_value("User", name, ["name", "full_name"], as_dict=True)

	def _get_installation_attachments(self, installation_name):
		if not installation_name:
			return []
		return frappe.db.get_all(
			"File",
			fields=["name", "file_name", "file_url", "is_private"],
			filters={
				"attached_to_doctype": "Installation Request",
				"attached_to_name": installation_name,
			},
			order_by="creation asc",
		)

	def _build_ticket(self, ticket, installation, attachments, installation_sales):
		sales_name = "-"
		if installation_sales and installation_sales.get("full_name"):
			sales_name = installation_sales.get("full_name")

		return {
			# HD Ticket
			"ticket_no": ticket.get("name"),
			"status": ticket.get("status"),
			"priority": ticket.get("priority"),
			# Installation Request
			"applicant_name": installation.get("applicant_name"),
			"phone": installation.get("phone_number"),
			"full_address": installation.get("full_address"),
			"google_maps_url": installation.get("google_maps_url"),
			"package": installation.get("internet_package"),
			# Photos
			"ktp_photo": installation.get("ktp_photo"),
			"house_front_photo": installation.get("house_front_photo"),
			"extra_photos": attachments,
			# Sales Person
			"sales_person": sales_name,
			"notes": installation.get("survey_notes") or installation.get("installation_notes") or "",
		}
