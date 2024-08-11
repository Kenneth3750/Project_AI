import os
import requests
import base64 
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_TOKEN")
client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))


def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  

def look_advice(params, user_id, role_id):
    try:
        user_petition = params['user_petition']
        base64_image = encode_image(f"current/user_{user_id}/image.jpg")
        headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": f"""
                            Based on the image, make some advices for the user depending on his/her petition. Be concise, clear and straight to the point.\n
                            User Petition: {user_petition}
                    """
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                    }
                ]
                }
            ],
            "max_tokens": 300
        }
    
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response = response.json().get('choices')[0].get('message').get('content')
        print(response)

        return {"message": response}
    except Exception as e:
        print(f"An error ocurred: {e}")
        return {"message": f"An error ocurred: {e}"}
    

def show_me_some_image_advice_examples(params, user_id, role_id):
    try:
        user_petition = params['user_petition']
        response = client.images.generate(
                    model="dall-e-3",
                    prompt=user_petition,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                    )

        image_url = response.data[0].url
        return {"display": image_url}
    except Exception as e:
        print(f"An error ocurred: {e}")
        return {"error": str(e)}
     



def trainer_tools():
    tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "look_advice",
                        "description": "This function will return some advices based on the user look and the situation exposed on the user petition.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_petition": {
                                    "type": "string",
                                    "description": "The user petition that will be used to generate the advices based on the user look."
                                }, 
                            },
                            "required": ["user_petition"],
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "show_me_some_image_advice_examples",
                        "description": "This function will return some images with advices based on the user look and the situation exposed on the user petition.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_petition": {
                                    "type": "string",
                                    "description": "The user petition transformed into a prompt that will generate the images with advices based on the petition."
                                }, 
                            },
                            "required": ["user_petition"],
                        }
                    }
                }
            ]

    available_tools = {
        "look_advice": look_advice,
        "show_me_some_image_advice_examples": show_me_some_image_advice_examples
    }

    return tools, available_tools
