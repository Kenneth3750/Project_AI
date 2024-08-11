from tools.recepcionist import add_apartment, get_apartments, list_of_reservations
import os
import glob
from tools.pdf_tools import save_pdf_tool, read_pdf_tool
from tools.personal_assistant import add_email, get_emails, erase_email_token

def save_pdf(user_id, file, role_id):
    if not os.path.exists(f"pdf/user_{user_id}/role_{role_id}/{file.filename}"):
        save_pdf_tool(user_id, file, role_id)
        read_pdf_tool(user_id, file, role_id)


def new_apartment(user_id, apartment, phone):
    try:
        add_apartment(user_id, apartment, phone)
        return {"message": "Apartment added successfully"}
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error adding the apartment. Please try again.")
    

def return_apartments(user_id):
    try:
       apartments = get_apartments(user_id)
       return apartments
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error retrieving the apartments. Please try again.")
    

def new_email(name, email, user_id):
    try:
        add_email(name, email, user_id)
        return {"message": "Email added successfully"}
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error adding the email. Please try again.")
    
def return_emails(user_id):
    try:
       emails = get_emails(user_id)
       return emails
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error retrieving the emails. Please try again.")
    
def delete_email(user_id):
    try:
        erase_email_token(user_id)
        return {"message": "Email deleted successfully"}
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error deleting the email. Please try again.")
    
def get_reservations(user_id):
    try:
        reservations = list_of_reservations(user_id)
        return reservations
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error retrieving the reservations. Please try again.")