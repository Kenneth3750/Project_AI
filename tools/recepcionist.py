from heyoo import WhatsApp
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import os
from dotenv import load_dotenv
from tools.conversation import generate_response, extract_json
from tools.database_tools import database_connection
import json


load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))


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
    

def send_announcent_to_all(params, user_id, role_id):
    try:
        messenger = WhatsApp(os.environ.get("whatsapp_token"), phone_number_id=os.environ.get("phone_id"))
        message = params.get("message")
        with open(f"apartment/user_{user_id}/apartment.json", "r") as f:
            data = json.load(f)
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
            Your labour is to translate a user petition into a SQL insert only query. The table is called recepcionist_reservations and has the following columns:\n
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
            You have to make sure that the reservation does not overlap with any other reservation for the same place and date. Here are the current reservations for the date {date}:\n
            You must return a json with the key 'query' and the value the SQL query. 
            If the user reservation overlaps with another reservation, you must return a json with the key 'error' and the value 'The reservation overlaps with another reservation. Please select another date or time, the times that are already reserved are ...'.\n
            An user cannot have more than 1 reservation for the same place and date. You can only update the reservation if the user wants to change the date or time of the reservation.\n
            {current_reservartions} 
            
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
                "description": "Make a reservation for the users of the building or update the reservation if the user wants to change the date or time of the reservation",
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
                            "enum": ["gym", "pool", "court", "event room"],
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
                "description": "Select all the reservations made for a specific date and place",
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
                            "enum": ["gym", "pool", "court", "event room"],
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
                            "enum": ["gym", "pool", "court", "event room"],
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
                            "enum": ["gym", "pool", "court", "event room"],
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
        }
    ]

    available_functions = {
        "new_visitor_alert": new_visitor_alert,
        "send_announcent_to_all": send_announcent_to_all,
        "insert_reservation": insert_reservation,   
        "see_current_reservations": see_current_reservations,
        "change_reservation": change_reservation,
        "delete_last_reservation": delete_last_reservation
    }

    return tools, available_functions


def add_apartment(apartment, phone, user_id):
    json_path = os.path.join("apartment", f"user_{user_id}", "apartment.json")
    if not os.path.exists(os.path.dirname(json_path)):
        os.makedirs(os.path.dirname(json_path))
        with open(json_path, "w") as f:
            json.dump({}, f)
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