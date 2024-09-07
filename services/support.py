from tools.recepcionist import add_apartment, get_apartments, list_of_reservations, erase_apartment, add_recepcionist_area, get_recepcionist_areas, delete_recepcionist_area
import os
import glob
from tools.pdf_tools import save_pdf_tool, read_pdf_tool
from tools.personal_assistant import add_email, get_emails, erase_email_token, create_email_token, erase_email_contact
from tools.trainer import get_html_summary

def save_pdf(user_id, file, role_id):
    if not os.path.exists(f"pdf/user_{user_id}/role_{role_id}/{file.filename}"):
        save_pdf_tool(user_id, file, role_id)
        read_pdf_tool(user_id, file, role_id)

def save_token(user_id, token):
    try:
        create_email_token(user_id, token)
        return {"message": "Token added successfully"}
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error adding the token. Please try again.")


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
    
def delete_apartment(user_id, apartment):
    try:
        erase_apartment(user_id, apartment)
        return {"message": "Apartment deleted successfully"}
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error deleting the apartment. Please try again.")
    
def get_areas(user_id):
    try:
        areas = get_recepcionist_areas(user_id)
        return areas
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error retrieving the areas. Please try again.")
    
def add_area(user_id, area):
    try:
        add_recepcionist_area(user_id, area)
        return {"message": "Area added successfully"}
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error adding the area. Please try again.")
    
def delete_area(user_id, area):
    try:
        delete_recepcionist_area(user_id, area)
        return {"message": "Area deleted successfully"}
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error deleting the area. Please try again.")
    

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
    
def delete_contact_email(user_id, name, email):
    try:
        erase_email_contact(user_id, name, email)
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
    
def get_summary(user_id):
    try:
        html = get_html_summary(user_id)
        return html
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error retrieving the summary. Please try again.")