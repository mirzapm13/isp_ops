import asyncio
import frappe
from telegram.ext import (
	Application,
	CallbackQueryHandler,
	CommandHandler,
	MessageHandler,
	filters,
)

from isp_ops.telegram.config import get_telegram_settings
from isp_ops.telegram.handlers.detail import detail, detail_callback
from isp_ops.telegram.handlers.photo import photo_handler
from isp_ops.telegram.handlers.start import me_command, start
from isp_ops.telegram.handlers.tickets import tickets


def build_application(token: str = None) -> Application:
	if not token:
		settings = get_telegram_settings()
		token = settings.get("token")

	if not token:
		raise ValueError("Telegram Bot Token is not configured in ISP Ops Settings or site_config.json")

	app = Application.builder().token(token).build()

	# Register Command Handlers
	app.add_handler(CommandHandler("start", start))
	app.add_handler(CommandHandler("tickets", tickets))
	app.add_handler(CommandHandler("detail", detail))
	app.add_handler(CommandHandler("me", me_command))

	# Register Message Handlers
	app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

	# Register Callback Query Handlers
	app.add_handler(CallbackQueryHandler(detail_callback, pattern=r"^detail:"))
	app.add_handler(CallbackQueryHandler(tickets, pattern=r"^tickets"))

	return app


def start_polling():
	"""
	CLI / Bench runner helper for polling mode (e.g., bench execute isp_ops.telegram.bot.start_polling)
	"""
	async def run():
		app = build_application()
		print("Starting Telegram Bot in polling mode...")
		await app.initialize()
		await app.start()
		await app.updater.start_polling()

		while True:
			await asyncio.sleep(3600)

	asyncio.run(run())
