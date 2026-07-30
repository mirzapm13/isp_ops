import os
import frappe
from frappe.utils.file_manager import save_file


class FileService:
	def upload_file(
		self,
		file_path: str,
		dt: str = None,
		dn: str = None,
		is_private: int = 0,
	):
		if not os.path.exists(file_path):
			frappe.throw(f"File not found: {file_path}")

		filename = os.path.basename(file_path)

		with open(file_path, "rb") as f:
			content = f.read()

		saved_file = save_file(
			fname=filename,
			content=content,
			dt=dt,
			dn=dn,
			is_private=is_private,
		)

		return saved_file
