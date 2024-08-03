from heyoo import WhatsApp
import os
import json
from dotenv import load_dotenv
import requests
import base64

load_dotenv()



def new_visitor_alert(params, user_id, role_id):
    try:
        messenger = WhatsApp(os.environ.get("whatsapp_token"), phone_number_id=os.environ.get("phone_id"))
        media_path = os.path.join("current", f"user_{user_id}", "image.jpg")
        media_id = messenger.upload_media(
            media=media_path,
        )['id']
        message = params.get("message")
        apartment = params.get("apartment")

        with open(f"apartment/user_{user_id}/apartment.json", "r") as f:
            data = json.load(f)
            owner_number = data.get(apartment)
            if owner_number:
                messenger.send_message(f"{message}", owner_number)
                messenger.send_image(
                    image=media_id,
                    recipient_id=owner_number,
                    link=False
                )
                return {"message": "The owner has been successfully notified. Inform the visitor about that"}       
            return {"error": "The apartment number is not valid. Please check the number and try again"}
        
    except Exception as e:
        return {"error": str(e)}
    
    


def recepcionist_tools():

    tools = [
        {
            "type": "function",
            "function": {
                "name": "new_visitor_alert",
                "description": "Send a message to the owner of the apartment to alert them of a new visitor",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message the visitor wants to send to the owner of the apartment"
                        },
                        "apartment": {
                            "type": "string",
                            "description": "The apartment number, it can be a number of a mix of letters and numbers, always with no spaces"
                        }
                    },
                    "required": ["message", "apartment"]
                }
            }

        }
    ]

    available_functions = {
        "new_visitor_alert": new_visitor_alert
    }

    return tools, available_functions


def add_apartment(apartment, phone, user_id):
    json_path = os.path.join("apartment", f"user_{user_id}", "apartment.json")
    with open(json_path, "r") as f:
        data = json.load(f)
        data[apartment] = phone
    with open(json_path, "w") as f:
        json.dump(data, f)

def get_apartments(user_id):
    json_path = os.path.join("apartment", f"user_{user_id}", "apartment.json")
    with open(json_path, "r") as f:
        data = json.load(f)
    return data