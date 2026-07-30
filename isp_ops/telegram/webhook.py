import asyncio
import json
import frappe
import httpx
from telegram import Update

from isp_ops.telegram.bot import build_application
from isp_ops.telegram.config import get_telegram_settings


@frappe.whitelist(allow_guest=True)
def handle_webhook():
	"""
	Whitelisted HTTP POST endpoint for receiving Telegram Webhook updates.
	Endpoint URL: /api/method/isp_ops.telegram.webhook.handle_webhook
	"""
	if frappe.request.method != "POST":
		frappe.response["status_code"] = 405
		return {"message": "Method Not Allowed"}

	settings = get_telegram_settings()

	if not settings.get("enabled"):
		return {"status": "bot_disabled"}

	token = settings.get("token")
	if not token:
		return {"status": "token_missing"}

	# Optional webhook secret verification header
	secret_token = settings.get("webhook_secret")
	if secret_token:
		header_secret = frappe.get_request_header("X-Telegram-Bot-Api-Secret-Token")
		if header_secret != secret_token:
			frappe.throw("Invalid Telegram Secret Token", frappe.PermissionError)

	raw_data = frappe.request.get_data(as_text=True)
	if not raw_data:
		return {"status": "empty_payload"}

	try:
		payload = json.loads(raw_data)
		asyncio.run(process_update_async(payload, token))
		return {"status": "ok"}
	except Exception as e:
		frappe.log_error(title="Telegram Webhook Error", message=str(e))
		return {"status": "error", "error": str(e)}


async def process_update_async(payload: dict, token: str):
	app = build_application(token=token)
	await app.initialize()
	update = Update.de_json(payload, app.bot)
	await app.process_update(update)
	await app.shutdown()


@frappe.whitelist()
def set_webhook(url: str = None):
	"""
	Utility to register webhook URL with Telegram API.
	Usage from bench console or bench execute:
	bench execute isp_ops.telegram.webhook.set_webhook --kwargs '{"url": "https://yourdomain.com/api/method/isp_ops.telegram.webhook.handle_webhook"}'
	"""
	settings = get_telegram_settings()
	token = settings.get("token")
	if not token:
		frappe.throw("Telegram Bot Token is not set in ISP Ops Settings or site_config.json")

	if not url:
		site_url = frappe.utils.get_url()
		url = f"{site_url}/api/method/isp_ops.telegram.webhook.handle_webhook"

	api_url = f"https://api.telegram.org/bot{token}/setWebhook"
	params = {"url": url}
	secret = settings.get("webhook_secret")
	if secret:
		params["secret_token"] = secret

	with httpx.Client() as client:
		res = client.post(api_url, data=params)
		res_json = res.json()

	if not res_json.get("ok"):
		frappe.throw(f"Failed to set webhook: {res_json.get('description')}")

	return res_json


@frappe.whitelist()
def delete_webhook():
	"""
	Utility to delete webhook registration with Telegram API.
	Usage:
	bench execute isp_ops.telegram.webhook.delete_webhook
	"""
	settings = get_telegram_settings()
	token = settings.get("token")
	if not token:
		frappe.throw("Telegram Bot Token is not set in ISP Ops Settings or site_config.json")

	api_url = f"https://api.telegram.org/bot{token}/deleteWebhook"

	with httpx.Client() as client:
		res = client.post(api_url)
		res_json = res.json()

	if not res_json.get("ok"):
		frappe.throw(f"Failed to delete webhook: {res_json.get('description')}")

	return res_json

