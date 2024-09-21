from __future__ import print_function
import smtplib
from email.mime.text import MIMEText
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from tools.conversation import generate_response, extract_json
import base64
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tools.database_tools import database_connection
import datetime
from html import escape
from serpapi import GoogleSearch
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))
SCOPES = ['https://www.googleapis.com/auth/calendar.events',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']



def extract_array_from_string(input_string):
        start = input_string.find('[')
        end = input_string.rfind(']') + 1
        if start != -1 and end != -1:
            return input_string[start:end]
        else:
            return input_string



def authenticate(user_id):
    token_path = f'tokens/token_{user_id}.json'
    
    if not os.path.exists(token_path):
        print(f"No se encontró el archivo de token para el usuario {user_id}")
        return None
    
    with open(token_path, 'r') as token_file:
        token_data = json.load(token_file)
    
    if 'refresh_token' not in token_data:
        print(f"No se encontró refresh_token para el usuario {user_id}")
        return None
    
    creds = Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        scopes=token_data.get('scope', '').split()
    ) 
    if creds.expired and creds.refresh_token:
        print(f"Refrescando token para el usuario {user_id}")
        try:
            creds.refresh(Request())
            create_email_token(user_id, {
                'access_token': creds.token,
                'refresh_token': creds.refresh_token,
                'scope': ' '.join(creds.scopes)
            })
        except Exception as e:
            print(f"Error al refrescar el token: {e}")
            return None
    
    return creds
    
def get_calendar_service(user_id):
    creds = authenticate(user_id)
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_user_email(creds):
    try:
        """Obtiene el correo electrónico del usuario autenticado"""
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        return user_info.get('email')
    except Exception as e:
        print(e)
        return Exception("Problema al obtener el correo electrónico del usuario")


def get_gmail_service(creds):
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_chat_service(creds):
    service = build('chat', 'v1', credentials=creds)
    return service


def create_google_calendar_reminder(params, user_id, role_id):
    """Crea un recordatorio en Google Calendar"""
    try:
        some_google_operation(user_id)
        summary = params['summary']
        description = params['description']
        start_time = params['start_time']
        end_time = params['end_time']
        reminders_minutes = params['reminders_minutes']

        service = get_calendar_service(user_id)
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Bogota',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Bogota',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'popup', 'minutes': minutes} for minutes in reminders_minutes],
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f'Recordatorio creado: {event.get("htmlLink")}')
        return {'message': f'Reminder created successfully. Add a comment about the user look if that does not compromise retrieving the full information.'}
    except Exception as e:
        print(e)
        return {'error': str(e)}
    


def get_user_agenda(params, user_id, role_id):
    try:
        service = get_calendar_service(user_id)
        now = datetime.datetime.now(datetime.timezone.utc)
        time_min = now.isoformat()
        events_result = service.events().list(calendarId='primary', timeMin=time_min,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        if not events:
            return {'message': 'No recent events found'}
        else:
            return {'message': f""" According to the current time, the next 10 events are:\n {events}\n
            Mention the user the time and names of the the events that are going to happen near the current time that means that you don't have to mention all the events.\n
            Your response will pass a TTS model so do not add links or images, just text in a proper way for a voice assistant. Add a comment about the user look if that does not compromise retrieving the full information."""}
    except Exception as e:
        print(e)
        return {'error': str(e)}



def send_email(params, user_id, role_id):
    try:
        creds = authenticate(user_id)
        service = get_gmail_service(creds)
        sender_email = get_user_email(creds)
        
        names = params['names']
        subject = params['subject']
        message = params['message']
               
        users = get_emails(user_id)
        users = json.dumps(users)


        messages = [{"role": "system", "content": f"Return only an array of strings in which you relate each name on a list of names with emails on a json. I want you to return the emails of the users that are most likely to be the same. Example, i can hve on the json the name christian, but the text model maybe wrote crsitian, so i want you to know that, except for the little mistakes, the names are the same."},
                    {"role": "user", "content": f"The names of the users are {names} and the user emails are {users} " }]
        completion = generate_response(client, messages)
        completion = extract_json(completion)
        print(completion)
        completion = json.loads(completion)
        emails = completion

        recipients = emails
        subject = subject
        body = message

        html_message = MIMEText(body, "html")
        html_message["Subject"] = subject
        html_message["From"] = sender_email
        html_message["To"] = ", ".join(recipients)
        raw_message = base64.urlsafe_b64encode(html_message.as_bytes()).decode("utf-8")
        message = {"raw": raw_message}
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        return {'message': f'Email sent successfully to {", ".join(recipients)} with id {sent_message["id"]}. Add a comment about the user look if that does not compromise retrieving the full information.'}
    except Exception as e:
        print(e)
        return {'error': str(e)}
    


def send_visitor_info(params, user_id, role_id):
    try:
        creds = authenticate(user_id)
        service = get_gmail_service(creds)
        sender_email = get_user_email(creds)

        body = params['user_message']

        html_message = MIMEText(body, "html")
        html_message["Subject"] = f"Visitor info from {params['user_name']}"
        html_message["From"] = sender_email
        html_message["To"] = sender_email
        raw_message = base64.urlsafe_b64encode(html_message.as_bytes()).decode("utf-8")
        message = {"raw": raw_message}
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        return {'message': f'Visitor info sent successfully'}
    except Exception as e:
        print(e)
        return {'error': str(e)}
    
def news_json_to_html(json_data, location):
    news_items = json.loads(json_data)
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Barranquilla News</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; }
            h1 { color: #333; text-align: center; }
            .news-item { background-color: #fff; margin-bottom: 20px; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .news-item h2 { margin-top: 0; color: #2c3e50; }
            .news-item img { max-width: 100%; height: auto; border-radius: 5px; margin-bottom: 10px; }
            .news-item p { margin: 5px 0; }
            .news-item a { color: #3498db; text-decoration: none; }
            .news-item a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
    """
    html += f'<h1>Latest news from {escape(location)}</h1>'
    for item in news_items:
        html += '<div class="news-item">'
        html += f'<h2>{escape(item["title"])}</h2>'
        
        if 'thumbnail' in item:
            html += f'<img src="{escape(item["thumbnail"])}" alt="{escape(item["title"])}">'
        
        if 'source' in item:
            source_name = item['source'].get('name', 'Unknown source')
            html += f'<p><strong>Source:</strong> {escape(source_name)}</p>'
        
        if 'date' in item:
            html += f'<p><strong>Date:</strong> {escape(item["date"])}</p>'
        
        if 'description' in item:
            html += f'<p>{escape(item["description"])}</p>'
        
        if 'link' in item:
            html += f'<p><a href="{escape(item["link"])}" target="_blank">Read more</a></p>'
        
        html += '</div>'

    html += """
    </body>
    </html>
    """
    return html

def get_current_news(params, user_id, role_id):
    location = params.get('location')
    params_search = {
    "engine": "google_news",
    "q": location,
    "gl": "us",
    "hl": "en",
    "api_key": os.getenv('SEARCH_WEB_API_KEY')
    }

    search = GoogleSearch(params_search)
    results = search.get_dict()
    news_results = results["news_results"]
    return {"display": news_json_to_html(json.dumps(news_results), location), 
            "message": f"Here are the latest news from {location}. Make a brief summary of the news and mention the most important news. Do not add links or images, just text in a proper way for a voice assistant. Mention that the news are displayed in the screen."}


def fahrenheit_to_celsius(temp_f):
    try:
        temp_f = float(temp_f)
        return round((temp_f - 32) * 5/9, 1)
    except ValueError:
        return "N/A"

def weather_json_to_html(json_data):
    weather_data = json.loads(json_data)
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Current Weather</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; }
            h1 { color: #333; }
            .weather-card { background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; }
            .weather-info { margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="weather-card">
            <h1>Current Weather in %s</h1>
    """ % escape(weather_data.get('location', 'Unknown Location'))

    # Convert temperature to Celsius
    temp_f = weather_data.get('temperature', 'N/A')
    temp_c = fahrenheit_to_celsius(temp_f)

    weather_items = [
        ('Temperature', f"{temp_c}°C"),
        ('Weather', weather_data.get('weather', 'N/A')),
        ('Precipitation', weather_data.get('precipitation', 'N/A')),
        ('Humidity', weather_data.get('humidity', 'N/A')),
        ('Wind', weather_data.get('wind', 'N/A')),
        ('Last Updated', weather_data.get('date', 'N/A'))
    ]

    for label, value in weather_items:
        html += f'<div class="weather-info"><strong>{label}:</strong> {escape(str(value))}</div>'

    html += """
        </div>
    </body>
    </html>
    """

    return html

def get_weather_info(params, user_id, role_id):
    location = params.get('location')
    params_search = {
    "q": f"What's the weather in {location}? ",
    "hl": "en",
    "gl": "us",
    "api_key": os.getenv('SEARCH_WEB_API_KEY')
    }

    search = GoogleSearch(params_search)
    results = search.get_dict()
    answer_box = results["answer_box"]
    return {"display": weather_json_to_html(json.dumps(answer_box)),
            "message": f"Here is the weather forecast for {location}. Make a brief summary of the weather forecast and mention the most important details. Do not add links or images, just text in a proper way for a voice assistant. Mention that the weather forecast is displayed in the screen."}



def assistant_tools():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Write an email accodring to the user's input and send it to the users the user wants to send it to.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "names": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "The names of the users the user wants to send the email to."
                        },
                        "subject": {
                            "type": "string",
                            "description": "The subject of the email the user wants to send drafted in a proper way for an email structure."
                        },
                        "message": {
                            "type": "string",
                            "description": "The message the user wants to send converted to an html format and drafted in a proper way for an email structure. If the message given by the user is not well written, you must adapt it to a proper email structure."
                        }
                    },
                    "required": ["names", "subject", "message"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_google_calendar_reminder",
                "description": "Create a reminder for the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "The summary of the reminder."
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the reminder."
                        },
                        "start_time": {
                            "type": "string",
                            "description": "The start time of the reminder in the format 'YYYY-MM-DDTHH:MM:SS'."
                        },
                        "end_time": {
                            "type": "string",
                            "description": "The end time of the reminder in the format 'YYYY-MM-DDTHH:MM:SS'."
                        },
                        "reminders_minutes": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            },
                            "description": "The minutes before the reminder to send the reminder."
                        }
                    },
                    "required": ["summary", "description", "start_time", "end_time", "reminders_minutes"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_visitor_info",
                "description": "Leave a message for the main user when a visitor arrives.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_name": {
                            "type": "string",
                            "description": "The name of the visitor."
                        },
                        "user_message": {
                            "type": "string",
                            "description": "The message of the visitor formatted in html."
                        }
                    },
                    "required": ["user_name", "user_message"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_user_agenda",
                "description": "Get the agenda of the user from the current time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "current_time": {
                            "type": "string",
                            "description": "The current time in the format 'YYYY-MM-DDTHH:MM:SS'."
                        }
                    },
                    "required": ["current_time"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_current_news",
                "description": "Tell and inform the user about the latest news from a location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get the news from formatted like: 'city, country' or 'city, state, country'."
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather_info",
                "description": "Tell and inform the user about the weather from a location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get the weather forecast from formatted like: 'city, country' or 'city, state, country'."
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    available_functions = {
        "send_email": send_email,
        "create_google_calendar_reminder": create_google_calendar_reminder,
        "send_visitor_info": send_visitor_info,
        "get_user_agenda": get_user_agenda,
        "get_current_news": get_current_news,
        "get_weather_info": get_weather_info
    }

    return tools, available_functions


def add_email(name, email, user_id):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    sql = "Select email_json from assistant_emails_registerd where user_id = %s"
    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()
    if result:
        emails = json.loads(result[0])
        emails[name] = email
        emails = json.dumps(emails)
        sql = "UPDATE assistant_emails_registerd SET email_json = %s WHERE user_id = %s"
        cursor.execute(sql, (emails, user_id))
        connection.commit()
    else:
        emails = {name: email}
        emails = json.dumps(emails)
        sql = "INSERT INTO assistant_emails_registerd (user_id, email_json) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, emails))
        connection.commit()
    cursor.close()
    connection.close()

def get_emails(user_id):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    sql = "Select email_json from assistant_emails_registerd where user_id = %s"
    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()
    if result:
        emails = json.loads(result[0])
        cursor.close()
        connection.close()
        return emails
    else:
        cursor.close()
        connection.close()
        return {}
    
def erase_email_contact(user_id, name, email):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    sql = "Select email_json from assistant_emails_registerd where user_id = %s"
    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()
    if result:
        emails = json.loads(result[0])
        if name in emails:
            del emails[name]
            emails = json.dumps(emails)
            sql = "UPDATE assistant_emails_registerd SET email_json = %s WHERE user_id = %s"
            cursor.execute(sql, (emails, user_id))
            connection.commit()
    cursor.close()
    connection.close()
    

def erase_email_token(user_id):
    token_path = f'tokens/token_{user_id}.json'
    os.remove(token_path)

def create_email_token(user_id, token):
    token_data = {
        "token": token,
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'), 
    }
    
    if 'refresh_token' in token:
        token_data["refresh_token"] = token['refresh_token']
    
    token_path = f'tokens/token_{user_id}.json'
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, 'w') as token_file:
        json.dump(token_data, token_file)

def refresh_token_if_expired(creds, user_id):
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        create_email_token(user_id, creds.to_json())
    return creds


def some_google_operation(user_id):
    creds = authenticate(user_id)
    if not creds:
        raise Exception("No credentials found")
    
    creds = refresh_token_if_expired(creds, user_id)