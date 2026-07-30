import frappe


def get_telegram_settings():
	"""
	Retrieves Telegram settings from Single DocType 'ISP Ops Settings'
	with fallback to site_config (frappe.conf).
	"""
	token = None
	enabled = True
	webhook_secret = None

	try:
		if frappe.db.exists("DocType", "ISP Ops Settings"):
			doc = frappe.get_single("ISP Ops Settings")
			token = doc.get_password("telegram_bot_token") if hasattr(doc, "get_password") else doc.telegram_bot_token
			enabled = bool(doc.enable_telegram_bot)
			webhook_secret = doc.telegram_webhook_secret
	except Exception as e:
		frappe.log_error(title="Failed to load ISP Ops Settings", message=str(e))

	if not token:
		token = getattr(frappe.conf, "telegram_bot_token", None)

	return {
		"token": token,
		"enabled": enabled,
		"webhook_secret": webhook_secret,
	}
