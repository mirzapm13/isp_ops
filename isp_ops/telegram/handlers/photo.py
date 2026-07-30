import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from isp_ops.telegram.services.file_service import FileService


async def photo_handler(
	update: Update,
	context: ContextTypes.DEFAULT_TYPE,
):
	photo = update.message.photo[-1]
	file = await context.bot.get_file(photo.file_id)

	temp_dir = tempfile.gettempdir()
	filename = os.path.join(temp_dir, f"{photo.file_unique_id}.jpg")

	await file.download_to_drive(filename)

	await update.message.reply_text("Photo downloaded successfully. Uploading to Frappe...")

	try:
		file_service = FileService()
		result = file_service.upload_file(filename)
		await update.message.reply_text(f"Uploaded to Frappe: {result.file_name} ({result.file_url})")
	finally:
		if os.path.exists(filename):
			os.remove(filename)
