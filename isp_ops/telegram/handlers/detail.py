from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from isp_ops.telegram.services.ticket_service import TicketService


async def detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
	if not context.args:
		await update.message.reply_text("Usage: /detail <ticket_number>\nExample: /detail 0019")
		return

	ticket_no = context.args[0]
	service = TicketService()
	data = service.get_ticket_detail(ticket_no)

	if not data:
		await update.message.reply_text(f"Ticket #{ticket_no} not found.")
		return

	message = f"""
📌 Ticket #{data["ticket_no"]}

📍 {data.get("full_address") or "-"}

👤 {data.get("applicant_name") or "-"}

📞 {data.get("phone") or "-"}

📦 {data.get("package") or "-"}

Status: {data.get("status") or "-"}
Priority: {data.get("priority") or "-"}
"""

	await update.message.reply_text(message)


async def detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()

	ticket_no = query.data.split(":")[1]
	service = TicketService()
	data = service.get_ticket_detail(ticket_no)

	if not data:
		await query.edit_message_text(text=f"Ticket #{ticket_no} not found.")
		return

	message = f"""
📌 Ticket #{data["ticket_no"]}

📍 {data.get("full_address") or "-"}

👤 {data.get("applicant_name") or "-"}

📞 {data.get("phone") or "-"}
"""

	keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="tickets")]])

	await query.edit_message_text(text=message, reply_markup=keyboard)
