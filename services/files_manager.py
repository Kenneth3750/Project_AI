import os
import glob
from tools.pdf_tools import save_pdf_tool, read_pdf_tool

def save_pdf(user_id, file, role_id):
    if not os.path.exists(f"pdf/user_{user_id}/role_{role_id}/{file.filename}"):
        save_pdf_tool(user_id, file, role_id)
        read_pdf_tool(user_id, file, role_id)
