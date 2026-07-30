import os
import frappe
from telegram import Update
from telegram.ext import ContextTypes


class BriefingService:
	def _get_message_target(self, target):
		if hasattr(target, "reply_text"):
			return target
		if getattr(target, "message", None):
			return target.message
		if getattr(target, "callback_query", None) and target.callback_query.message:
			return target.callback_query.message
		return target

	async def send_ticket_briefing(
		self,
		target,
		context: ContextTypes.DEFAULT_TYPE,
		ticket: dict,
	):
		msg_target = self._get_message_target(target)

		formatted_phone = None
		raw_phone = ticket.get("phone")
		if raw_phone:
			if raw_phone.startswith("0"):
				formatted_phone = "+62" + raw_phone[1:]
			elif raw_phone.startswith("+"):
				formatted_phone = raw_phone
			else:
				formatted_phone = "+" + raw_phone

		phone_text = f"https://wa.me/{formatted_phone}" if formatted_phone else "-"

		message = f"""
━━━━━━━━━━━━━━━━━━━━━━

📍 {ticket.get("full_address") or "-"}

👤 {ticket.get("applicant_name") or "-"}
📞 {phone_text}

📦 {ticket.get("package") or "-"}

🎯 Marketing
{ticket.get("sales_person") or "-"}

⚠ Priority
{ticket.get("priority") or "-"}

📋 Status
{ticket.get("status") or "-"}

━━━━━━━━━━━━

📝 Extra Notes

{ticket.get("notes") or "-"}

━━━━━━━━━━━━━━━━━━━━━━
"""

		await msg_target.reply_text(message)

		await self.send_location(msg_target, ticket)
		await self.send_ktp(msg_target, context, ticket)
		await self.send_house_front_photo(msg_target, context, ticket)
		await self.send_extra_photos(msg_target, context, ticket)

	async def send_photo(
		self,
		target,
		path: str,
		caption: str,
	):
		if not path:
			return

		msg_target = self._get_message_target(target)

		# Try sending local file directly if available
		local_path = None
		if path.startswith("/files/"):
			local_path = frappe.get_site_path("public", path.lstrip("/"))
		elif path.startswith("/private/files/"):
			local_path = frappe.get_site_path(path.lstrip("/"))

		if local_path and os.path.exists(local_path):
			try:
				with open(local_path, "rb") as photo_file:
					await msg_target.reply_photo(
						photo=photo_file,
						caption=caption,
					)
				return
			except Exception as e:
				frappe.log_error(title="Failed to send local photo", message=str(e))

		# Fallback to URL
		photo_url = frappe.utils.get_url(path) if not path.startswith("http") else path
		await msg_target.reply_photo(
			photo=photo_url,
			caption=caption,
		)

	async def send_ktp(
		self,
		target,
		context: ContextTypes.DEFAULT_TYPE,
		ticket: dict,
	):
		await self.send_photo(
			target,
			ticket.get("ktp_photo"),
			"🪪 KTP",
		)

	async def send_house_front_photo(
		self,
		target,
		context: ContextTypes.DEFAULT_TYPE,
		ticket: dict,
	):
		await self.send_photo(
			target,
			ticket.get("house_front_photo"),
			"🏠 Rumah",
		)

	async def send_extra_photos(
		self,
		target,
		context: ContextTypes.DEFAULT_TYPE,
		ticket: dict,
	):
		photos = ticket.get("extra_photos", [])

		for photo in photos:
			file_url = photo.get("file_url")
			if file_url == ticket.get("ktp_photo"):
				continue
			if file_url == ticket.get("house_front_photo"):
				continue

			await self.send_photo(
				target,
				file_url,
				"📸 Foto Tambahan",
			)

	async def send_location(
		self,
		target,
		ticket: dict,
	):
		url = ticket.get("google_maps_url")
		if not url:
			return

		msg_target = self._get_message_target(target)
		await msg_target.reply_text(f"🗺 Google Maps\n\n{url}")
