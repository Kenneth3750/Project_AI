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
        return {'message': f'Recordatorio creado existosamente'}
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
        return {'message': f'Email sent successfully to {", ".join(recipients)} with id {sent_message["id"]}' }
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

def assistant_tools():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Send an email to the specified user names.",
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
                            "description": "The subject of the email the user wants to send."
                        },
                        "message": {
                            "type": "string",
                            "description": "The message the user wants to send converted to an html format and written in a proper way for an email structure."
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
        }
    ]
    available_functions = {
        "send_email": send_email,
        "create_google_calendar_reminder": create_google_calendar_reminder,
        "send_visitor_info": send_visitor_info
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