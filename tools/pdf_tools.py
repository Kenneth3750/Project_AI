import os
import glob
from langchain_community.document_loaders import PyPDFLoader
import tiktoken
import shutil
def save_pdf_tool(user_id, file, role_id):
    if not os.path.exists(f"pdf/user_{user_id}/role_{role_id}"):
        os.makedirs(f"pdf/user_{user_id}/role_{role_id}")
    if os.path.exists(f"pdf/user_{user_id}/role_{role_id}"):
        shutil.rmtree(f"pdf/user_{user_id}/role_{role_id}")
        os.makedirs(f"pdf/user_{user_id}/role_{role_id}")
    file.save(f"pdf/user_{user_id}/role_{role_id}/{file.filename}")
    print("PDF saved")



def read_pdf_tool(user_id, file, role_id):
    loader = PyPDFLoader(f"pdf/user_{user_id}/role_{role_id}/{file.filename}")
    pages = loader.load_and_split()
    pdf_text = ""
    for page in pages:
        pdf_text += page.page_content
        pdf_text += "\n"
    with open(f"pdf/user_{user_id}/role_{role_id}/{file.filename}.txt", "w", encoding='utf-8') as text_file:
        text_file.write(pdf_text)
    encoding = tiktoken.encoding_for_model("gpt-4")
    token_count = len(encoding.encode(pdf_text))
    print(token_count)
    
