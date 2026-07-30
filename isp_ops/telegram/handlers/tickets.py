from telegram import Update
from telegram.ext import ContextTypes

from isp_ops.telegram.services.briefing_service import BriefingService
from isp_ops.telegram.services.ticket_service import TicketService


async def tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
	ticket_service = TicketService()
	briefing_service = BriefingService()

	args = []

	if context.args:
		match context.args[0].lower():
			case "open":
				args = [["status", "=", "open"]]
			case "pending":
				args = [["status", "=", "pending"]]

	ticket_list = ticket_service.get_installation_tickets(args)

	if not ticket_list:
		reply_target = update.message or (update.callback_query.message if update.callback_query else None)
		if reply_target:
			await reply_target.reply_text("No installation tickets found.")
		return

	target = update.message or (update.callback_query.message if update.callback_query else None)

	for ticket in ticket_list:
		await briefing_service.send_ticket_briefing(
			target,
			context,
			ticket,
		)
