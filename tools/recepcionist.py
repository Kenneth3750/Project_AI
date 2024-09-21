from heyoo import WhatsApp
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import os
from dotenv import load_dotenv
from tools.conversation import generate_response, extract_json
from tools.database_tools import database_connection
from datetime import datetime, timedelta
import json
from html import escape
from typing import List, Dict
from serpapi import GoogleSearch
from urllib.parse import urlencode
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))


def send_alert_to_apartment_owner(params, user_id, role_id):
    try:
        messenger = WhatsApp(os.environ.get("whatsapp_token"), phone_number_id=os.environ.get("phone_id"))
        media_path = os.path.join("current", f"user_{user_id}", "image.jpg")
        media_id = messenger.upload_media(
            media=media_path,
        )['id']
        message = params.get("message")
        apartment = params.get("apartment")

        data = get_apartments(user_id)
  
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
    

def send_announcent_to_all(params, user_id, role_id):
    try:
        messenger = WhatsApp(os.environ.get("whatsapp_token"), phone_number_id=os.environ.get("phone_id"))
        message = params.get("message")
        data = get_apartments(user_id)
        data = json.loads(data)
        for owner_number in data.values():
            messenger.send_message(f"{message}", owner_number)
        return {"message": "The owners have been successfully notified."}

    except Exception as e:
        return {"error": str(e)}  

def check_reservation_exists(cursor, user_id, place, date, start_time, end_time):
    query = (
        "SELECT 1 FROM recepcionist_reservations "
        "WHERE place = %s AND reservation_date = %s "
        "AND ("
        "    (%s BETWEEN reservation_start_time AND reservation_end_time) "
        "    OR (%s BETWEEN reservation_start_time AND reservation_end_time) "
        "    OR (reservation_start_time BETWEEN %s AND %s) "
        "    OR (reservation_end_time BETWEEN %s AND %s)"
        ") "
        "AND user_id <> %s"
    )
    cursor.execute(query, (place, date, start_time, end_time, start_time, end_time, start_time, end_time, user_id))
    result = cursor.fetchone()
    print("Result:", result)
    return result is not None

def select_all_reservations_by_date(cursor, date, place):
    query = (
        "SELECT * FROM recepcionist_reservations WHERE reservation_date = %s and place = %s"
    )
    cursor.execute(query, (date, place))
    return cursor.fetchall()

def get_last_reservation(cursor, user_id, place, name):
    query = ("SELECT * FROM recepcionist_reservations WHERE user_id = %s AND place = %s AND user_name = %s ORDER BY created_at DESC LIMIT 1")
    cursor.execute(query, (user_id, place, name))
    return cursor.fetchone()




def insert_reservation(params, user_id, role_id):
    try:
        connection = database_connection(
            {
             "user": os.getenv('user'), 
             "password": os.getenv('password'), 
             "host": os.getenv('host'), 
             "db": os.getenv('db')
            }
        )
        user_id = user_id
        user_query = params['user_query']
        place = params['place']
        date = params['date']
        start_time = params['start_time']
        end_time = params['end_time']
        name = params['name']

        cursor = connection.cursor()
        current_reservartions = select_all_reservations_by_date(cursor, date, place)
        print("Current reservations:", current_reservartions)
        messages = [
            {"role": "system", "content": f"""You are a db manager. 
            Your only labour is to see if the reservation that the user wants to do overlaps with another reservation. The table is called recepcionist_reservations and has the following columns:\n
            create table if not exists recepcionist_reservations (
                id int primary key auto_increment,
                user_id int not null,
                place enum('gym', 'pool', 'court', 'event room') not null,
                reservation_date date not null,
                reservation_start_time time not null,
                reservation_end_time time not null,
                user_name varchar(50) not null,
                created_at date not null,
                foreign key (user_id) references users(id) on delete cascade
            );
            the current reservations are:\n
            {current_reservartions}\n

            If the date given by the user overlaps with another reservation, you must return a json with the key 'error' and the value 'The reservation overlaps with another reservation. Please select another date or time, the times that are already reserved are ...'.\n
            If the date given by the user does not overlap with another reservation, you must return a json with the key 'query' and the value the SQL query to insert the reservation.\n
            
            
             """
            },
            {"role": "user", "content": f"The request is {user_query}, on date: {date}, from {start_time} to {end_time} for place {place}. The user id is {user_id} and the name is {name}"}
        ]

        response = generate_response(client, messages)
        query = extract_json(response)
        print("Query:", query)
        query = json.loads(query)
        if 'error' in query:
            raise Exception(query['error'])
        query = query['query']
        cursor.execute(query)
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "The reservation has been successfully made."}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
    

def change_reservation(params, user_id, role_id):
    try:
        connection = database_connection(
            {
             "user": os.getenv('user'), 
             "password": os.getenv('password'), 
             "host": os.getenv('host'), 
             "db": os.getenv('db')
            }
        )
        user_id = user_id
        user_query = params['user_query']
        place = params['place']
        date = params['date']
        name = params['name']
        cursor = connection.cursor()
        last_reservation = get_last_reservation(cursor, user_id, place, name)
        current_reservations = select_all_reservations_by_date(cursor, date, place)
        messages = [
            {"role": "system", "content": f"""You are a db manager. 
            Your labour is to translate a user petition into a SQL update query only. The table is called recepcionist_reservations and has the following columns:\n 
            create table if not exists recepcionist_reservations (
                id int primary key auto_increment,
                user_id int not null,
                place enum('gym', 'pool', 'court', 'event room') not null,
                reservation_date date not null,
                reservation_start_time time not null,
                reservation_end_time time not null,
                user_name varchar(50) not null,
                created_at date not null,
                foreign key (user_id) references users(id) on delete cascade
            );
            You need tu update the date or time or both of the following reservation depending on the user petition:\n
            {last_reservation}/n
            You must return a json with the key 'query' and the value the SQL query.
            If the user reservation overlaps with another reservation, you must return a json with the key 'error' and the value 'The reservation overlaps with another reservation. Please select another date or time, the times that are already reserved are ...'.\n
            The current reservations for the new date are:\n
            {current_reservations}\n
            """},
            {"role": "user", "content": f"The request is {user_query}, for place {place}. The user id is {user_id} and the name is {name}"}
        ]
        response = generate_response(client, messages)
        query = extract_json(response)
        print("Query:", query)
        query = json.loads(query)
        if 'error' in query:
            raise Exception(query['error'])
        query = query['query']
        cursor.execute(query)
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "The reservation has been successfully updated."}


    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}


def see_current_reservations(params, user_id, role_id):
    try:
        connection = database_connection(
            {
             "user": os.getenv('user'), 
             "password": os.getenv('password'), 
             "host": os.getenv('host'), 
             "db": os.getenv('db')
            }
        )
        user_id = user_id
        place = params['place']
        date = params['date']

        cursor = connection.cursor()
        current_reservartions = select_all_reservations_by_date(cursor, date, place)
        cursor.close()
        connection.close()
        print("Current reservations:", current_reservartions)
        return {"message": f"The reservation already made are: \n {current_reservartions}"}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
    
def delete_last_reservation(params, user_id, role_id):
    try:
        connection = database_connection(
            {
             "user": os.getenv('user'), 
             "password": os.getenv('password'), 
             "host": os.getenv('host'), 
             "db": os.getenv('db')
            }
        )
        user_id = user_id
        place = params['place']
        name = params['name']
        cursor = connection.cursor()
        query = ("DELETE FROM recepcionist_reservations WHERE user_id = %s AND place = %s AND user_name = %s ORDER BY created_at DESC LIMIT 1")
        cursor.execute(query, (user_id, place, name))
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "The reservation has been successfully deleted."}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
    
def json_to_html_events(json_data, location):
    events = json.loads(json_data)
    html = "<html><head><style>body{font-family:Arial,sans-serif;line-height:1.6;margin:0;padding:20px;background-color:#f4f4f4}h1{color:#333}ul{list-style-type:none;padding:0}li{background-color:#fff;margin-bottom:10px;padding:15px;border-radius:5px;box-shadow:0 2px 5px rgba(0,0,0,0.1)}h2{margin-top:0;color:#2c3e50}a{color:#3498db;text-decoration:none}a:hover{text-decoration:underline}</style></head><body>"
    html += f"<h1>Events in {location}</h1><ul>"

    for event in events:
        html += f"<li>"
        html += f"<h2>{escape(event['title'])}</h2>"
        if 'date' in event and 'when' in event['date']:
            html += f"<p><strong>Fecha:</strong> {escape(event['date']['when'])}</p>"
        if 'address' in event:
            html += f"<p><strong>Lugar:</strong> {escape(', '.join(event['address']))}</p>"
        if 'description' in event:
            html += f"<p>{escape(event['description'][:150])}...</p>"
        if 'link' in event:
            html += f"<p><a href='{escape(event['link'])}' target='_blank'>Más información</a></p>"
        html += "</li>"

    html += "</ul></body></html>"
    return html
def json_to_html_food(json_data, location):
    restaurants = json.loads(json_data)
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; }
            h1 { color: #333; }
            .restaurant { background-color: #fff; margin-bottom: 20px; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .restaurant h2 { margin-top: 0; color: #2c3e50; }
            .restaurant img { max-width: 100%; height: auto; border-radius: 5px; margin-bottom: 10px; }
            .restaurant p { margin: 5px 0; }
            .restaurant a { color: #3498db; text-decoration: none; }
            .restaurant a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
    """
    html += f"<h1>Restaurants in {location}</h1>"
    for restaurant in restaurants:
        html += '<div class="restaurant">'
        html += f'<h2>{escape(restaurant["title"])}</h2>'
        
        if 'images' in restaurant and restaurant['images']:
            html += f'<img src="{escape(restaurant["images"][0])}" alt="{escape(restaurant["title"])}">'
        
        if 'rating' in restaurant:
            html += f'<p><strong>Calificación:</strong> {restaurant["rating"]} ({restaurant["reviews"]} reseñas)</p>'
        
        if 'price' in restaurant:
            html += f'<p><strong>Precio:</strong> {restaurant["price"]}</p>'
        
        if 'address' in restaurant:
            html += f'<p><strong>Dirección:</strong> {escape(restaurant["address"])}</p>'
        
        if 'hours' in restaurant:
            html += f'<p><strong>Horario:</strong> {escape(restaurant["hours"])}</p>'
        
        if 'links' in restaurant:
            if 'website' in restaurant['links']:
                html += f'<p><a href="{escape(restaurant["links"]["website"])}" target="_blank">Sitio web</a></p>'
            if 'order' in restaurant['links']:
                html += f'<p><a href="{escape(restaurant["links"]["order"])}" target="_blank">Ordenar en línea</a></p>'
            if 'directions' in restaurant['links']:
                html += f'<p><a href="{escape(restaurant["links"]["directions"])}" target="_blank">Cómo llegar</a></p>'
        
        html += '</div>'

    html += "</body></html>"
    return html

def json_to_html_places(json_data):
    places = json.loads(json_data)
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; }
            h1 { color: #333; text-align: center; }
            .place { background-color: #fff; margin-bottom: 20px; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .place h2 { margin-top: 0; color: #2c3e50; }
            .place img { max-width: 100%; height: auto; border-radius: 5px; margin-bottom: 10px; }
            .place p { margin: 5px 0; }
            .place .rating { font-weight: bold; color: #f39c12; }
        </style>
    </head>
    <body>
        <h1>Lugares para visitar en Barranquilla y alrededores</h1>
    """

    for place in places:
        html += '<div class="place">'
        html += f'<h2>{escape(place["title"])}</h2>'
        
        if 'thumbnail' in place:
            html += f'<img src="{escape(place["thumbnail"])}" alt="{escape(place["title"])}">'
        
        if 'rating' in place and 'reviews' in place:
            html += f'<p class="rating">Calificación: {place["rating"]} ({place["reviews"]} reseñas)</p>'
        
        if 'type' in place:
            html += f'<p><strong>Tipo:</strong> {escape(place["type"])}</p>'
        
        if 'address' in place:
            html += f'<p><strong>Dirección:</strong> {escape(place["address"])}</p>'
        
        if 'description' in place:
            html += f'<p><strong>Descripción:</strong> {escape(place["description"])}</p>'
        
        if 'hours' in place:
            html += f'<p><strong>Horario:</strong> {escape(place["hours"])}</p>'
        
        html += '</div>'

    html += "</body></html>"
    return html
    

def get_location_events(params, user_id, role_id):
    try:
        location = params["location"]

        params_google = {
            "engine": "google_events",
            "q": f"Events in {location}" ,
            "hl": "en",
            "gl": "us",
            "api_key": os.getenv('SEARCH_WEB_API_KEY')
        }

        search = GoogleSearch(params_google)
        results = search.get_dict()
        events_results = results["events_results"]
        return {"display": json_to_html_events(json.dumps(events_results), location), 
                "message": "The events have been successfully retrieved. Tell the user to check the screen, mention some of the events and suggest some activities but do not add links and nothing like that on the message."}
    except Exception as e:
        return {"error": str(e)}
    

def get_restaurants(params, user_id, role_id):
    try: 
        location = params["location"]
        food_query = params["food_query"]
        params = {
        "engine": "google_food",
        "q": food_query,
        "location": location,
        "api_key": os.getenv('SEARCH_WEB_API_KEY')
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        local_results = results["local_results"]
        return {"display": json_to_html_food(json.dumps(local_results), location), "message": "The restaurants have been successfully retrieved. Tell the user to check the screen, mention some of the restaurants and suggest some activities but do not add links and nothing like that on the message."}
    except Exception as e:
        return {"error": str(e)}
    
def get_location_places(params, user_id, role_id):
    try:
        location = params["location"]
        params = {
        "engine": "google_local",
        "q": "Places to visit",
        "location": location,
        "api_key": os.getenv('SEARCH_WEB_API_KEY')
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        local_results = results["local_results"]
        return {"display": json_to_html_places(json.dumps(local_results)), 
                "message": "The places have been successfully retrieved. Tell the user to check the screen, mention some of the places and suggest some activities but do not add links and nothing like that on the message."}
    except Exception as e:
        return {"error": str(e)}


def recepcionist_tools(user_id):

    areas = get_recepcionist_areas(user_id)
    tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "send_alert_to_apartment_owner",
                        "description": "Alert the owner of an apartment when someone is serching for him, or if there is someone leaving a package or a message for him, every time someone ask for an apartment this function must be used",
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

                },
                {
                    "type": "function",
                    "function": {
                        "name": "send_announcent_to_all",
                        "description": "Send a message to all the owners of the apartments",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "The message the visitor wants to send to all the owners of the apartments"
                                }
                            },
                            "required": ["message"]
                        }
                    }
                },
        {
            "type": "function",
            "function": {
                "name": "insert_reservation",
                "description": "Make a reservation for the users of the building ",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "format": "date",
                            "description": "The date of the reservation"
                        },
                        "start_time": {
                            "type": "string",
                            "format": "time",
                            "description": "The start time of the reservation"
                        },
                        "end_time": {
                            "type": "string",
                            "format": "time",
                            "description": "The end time of the reservation"
                        },
                        "place": {
                            "type": "string",
                            "enum": areas,
                            "description": "The place where the reservation will be made"
                        },
                        "user_query": {
                            "type": "string",
                            "description": "The user request to make the reservation"
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the user"
                        }
                    },
                    "required": ["date", "start_time", "end_time", "place", "user_query", "name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "see_current_reservations",
                "description": "See all the reservations made for a specific date and place",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "format": "date",
                            "description": "The date of the reservation"
                        },
                        "place": {
                            "type": "string",
                            "enum": areas,
                            "description": "The place where the reservation will be made"
                        },
                    },
                    "required": ["date", "place"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "change_reservation",
                "description": "Change the date or time or both of a reservation depending on the user petition and the user name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "format": "date",
                            "description": "The date of the current reservation"
                        },
                        "place": {
                            "type": "string",
                            "enum": areas,
                            "description": "The place where the reservation will be made"
                        },
                        "user_query": {
                            "type": "string",
                            "description": "The user request to make the reservation"
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the user"
                        }
                    },
                    "required": ["date", "place", "user_query", "name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_last_reservation",
                "description": "Delete the last reservation made for a specific user and place",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "place": {
                            "type": "string",
                            "enum": areas,
                            "description": "The place where the reservation will be made"
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the user"
                        }
                    },
                    "required": ["place", "name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_location_events",
                "description": "Recommend the user what to do in the location provided or provided the events of the location if the user asks for it",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to search for events on the following format: city, country or city, state, country according to the location provided by the user"
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_restaurants",
                "description": "Recommend, show or suggest the user the restaurants of the food type the user wants to eat in the location provided",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to search for restaurants on the following format: city, country or city, state, country according to the location provided by the user"
                        },
                        "food_query": {
                            "type": "string",
                            "description": "The type of food the user wants to eat"
                        }
                    },
                    "required": ["location", "food_query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_location_places",
                "description": "Recommend, show or suggest the user the places to visit in the location provided",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to search for places to visit on the following format: city, country or city, state, country according to the location provided by the user"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
]

    available_functions = {
        "send_alert_to_apartment_owner": send_alert_to_apartment_owner,
        "send_announcent_to_all": send_announcent_to_all,
        "insert_reservation": insert_reservation,   
        "see_current_reservations": see_current_reservations,
        "change_reservation": change_reservation,
        "delete_last_reservation": delete_last_reservation,
        "get_location_events": get_location_events,
        "get_restaurants": get_restaurants,
        "get_location_places": get_location_places

    }

    return tools, available_functions

def format_hotel_results_to_html(data: Dict) -> str:
    hotels = data.get('data', [])
    html_output = "<div class='hotel-results'>"

    for hotel in hotels[:5]:  
        html_output += f"<div class='hotel' id='{hotel['id']}'>"
        
        html_output += f"<h2>{hotel['name']}</h2>"
        html_output += f"<img src='{hotel['main_photo']}' alt='{hotel['name']}' class='hotel-image'>"
        
        html_output += f"<p><strong>Location:</strong> {hotel['city']}, {hotel['country']}</p>"
        html_output += f"<p><strong>Address:</strong> {hotel['address']}, {hotel['zip']}</p>"
        html_output += f"<p><strong>Stars:</strong> {hotel['stars']}</p>"
        

        description = hotel['hotelDescription'][:200] + "..." if len(hotel['hotelDescription']) > 200 else hotel['hotelDescription']
        html_output += f"<p><strong>Description:</strong> {description}</p>"
        
        html_output += f"<p><strong>Amenities:</strong> {hotel.get('business_amenities', 'Information not available')}</p>"
        
        html_output += f"<a href='https://example.com/book/{hotel['id']}' target='_blank' class='book-now'>Book Now</a>"
        
        html_output += "</div>" 

    html_output += "</div>"  
    return html_output


def add_apartment(apartment, phone, user_id):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    query = ("SELECT apartment_json from recepcionist_apartments WHERE user_id = %s")
    cursor.execute(query, (user_id,))
    data = cursor.fetchone()
    if data:
        apartments = json.loads(data[0])
        apartments[apartment] = phone
        query = ("UPDATE recepcionist_apartments SET apartment_json = %s WHERE user_id = %s")
        cursor.execute(query, (json.dumps(apartments), user_id))
    else:
        apartments = {apartment: phone}
        query = ("INSERT INTO recepcionist_apartments (user_id, apartment_json) VALUES (%s, %s)")
        cursor.execute(query, (user_id, json.dumps(apartments)))
    connection.commit()
    cursor.close()
    connection.close()

def get_apartments(user_id):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    query = ("SELECT apartment_json from recepcionist_apartments WHERE user_id = %s")
    cursor.execute(query, (user_id,))
    data = cursor.fetchone()
    cursor.close()
    connection.close()
    if data:
        return json.loads(data[0])
    return {}

def erase_apartment(user_id, apartment):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    query = ("SELECT apartment_json from recepcionist_apartments WHERE user_id = %s")
    cursor.execute(query, (user_id,))
    data = cursor.fetchone()
    if data:
        apartments = json.loads(data[0])
        if apartment in apartments:
            del apartments[apartment]
            query = ("UPDATE recepcionist_apartments SET apartment_json = %s WHERE user_id = %s")
            cursor.execute(query, (json.dumps(apartments), user_id))
            connection.commit()
            cursor.close()
            connection.close()
        else:
            raise Exception("The apartment does not exist.")
    else:
        raise Exception("The user does not have any apartments.")
    
def add_recepcionist_area(user_id, area):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    query = ("SELECT areas_array from recepcionist_areas WHERE user_id = %s")
    cursor.execute(query, (user_id,))
    data = cursor.fetchone()
    if data:
        areas = json.loads(data[0])
        areas.append(area)
        query = ("UPDATE recepcionist_areas SET areas_array = %s WHERE user_id = %s")
        cursor.execute(query, (json.dumps(areas), user_id))
    else:
        areas = [area]
        query = ("INSERT INTO recepcionist_areas (user_id, areas_array) VALUES (%s, %s)")
        cursor.execute(query, (user_id, json.dumps(areas)))
    connection.commit()
    cursor.close()
    connection.close()

def get_recepcionist_areas(user_id):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    query = ("SELECT areas_array from recepcionist_areas WHERE user_id = %s")
    cursor.execute(query, (user_id,))
    data = cursor.fetchone()
    cursor.close()
    connection.close()
    if data:
        return json.loads(data[0])
    return []

def delete_recepcionist_area(user_id, area):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    query = ("SELECT areas_array from recepcionist_areas WHERE user_id = %s")
    cursor.execute(query, (user_id,))
    data = cursor.fetchone()
    if data:
        areas = json.loads(data[0])
        if area in areas:
            areas.remove(area)
            query = ("UPDATE recepcionist_areas SET areas_array = %s WHERE user_id = %s")
            cursor.execute(query, (json.dumps(areas), user_id))
            connection.commit()
            cursor.close()
            connection.close()
        else:
            raise Exception("The area does not exist.")
    else:
        raise Exception("The user does not have any areas.")



def list_of_reservations(user_id):
    current_date = datetime.now().date().strftime("%Y-%m-%d") 
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    query = ("SELECT * FROM recepcionist_reservations WHERE user_id = %s AND reservation_date >= %s")
    cursor.execute(query, (user_id, current_date))
    reservations = cursor.fetchall()
    cursor.close()
    connection.close()
    formatted_reservations = []
    for reservation in reservations:
        formatted_reservation = {
            "place": reservation[2],
            "reservation_date": reservation[3].strftime("%Y-%m-%d"),
            "start_time": str(reservation[4]),  
            "end_time": str(reservation[5]),
            "user_name": reservation[6],
            "created_at": reservation[7].strftime("%Y-%m-%d")
        }
        formatted_reservations.append(formatted_reservation)

    return formatted_reservations


def get_user_current_location(user_id):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    sql = "SELECT city, country FROM user_useful_info WHERE user_id = (%s)"
    cursor.execute(sql, (user_id,))
    data = cursor.fetchone()
    cursor.close()
    connection.close()
    city = data[0]
    country = data[1]
    if data:
        return city, country
    return None, None