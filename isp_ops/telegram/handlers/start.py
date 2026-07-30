from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("ISP Bot Online\nUse /tickets")


async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user = update.effective_user

	message = f"""
Telegram Information

ID       : {user.id}
Username : @{user.username}
Name     : {user.full_name}
"""

	await update.message.reply_text(message)
