#this file contains all functions for the investigator role
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
import time
from tools.conversation import generate_response, extract_json
from tools.database_tools import database_connection
import pypdf
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))
current_year = int(time.strftime("%Y"))
#response key is display
def generateText(parameters, user_id, role_id):
    try:
        typeOfText = parameters.get("typeOfText")
        topic = parameters.get("topic")
        language = parameters.get("language")
        otherCharacteristics = parameters.get("otherCharacteristics")
        system_prompt = """You are an expert writter. You will always reply a json with the key display and the value of the text you generated.
        Do no add more keys, do not add more, do not even bother to say hello or goodbye. Just give the text."""
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Generate a {typeOfText} about {topic} in {language} taking into account {otherCharacteristics}"}]
        response = generate_response(client, messages)
        response = extract_json(response)
        text_json = json.loads(response) 
        text_json["message"] = "Tell the user the text is on screen, do not add the text on your response, just tell the user to look at the screen. Add a nice comment about using the visiom prompt"
        return text_json
    except Exception as e:
        return {"error": str(e)}

def getPapers(parameters, user_id, role_id):
    try:
        query = parameters.get("query")
        start_year = parameters.get("start_year")
        if start_year:
            if start_year == "None":
                start_year = None
            elif int(start_year) > current_year or int(start_year) < 0:
                start_year = None   
        
        params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": os.getenv('SEARCH_WEB_API_KEY'),
        "as_ylo": start_year,
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results["organic_results"]

        new_json = []
        i=0
        for result in organic_results:
            new_json.append(f"<div>Paper {i+1}: <a href='{result['link']}' target='_blank'><span style='color: blue; text-decoration: underline;'>{result['title']}</span></a></div><br>")
            i+=1
            if i==5:
                break

        single_string = ''.join(new_json)
        text_json = {"display": single_string, "message": "Tell the user the papers are on screen, do not add the papers on your response, just tell the user to look at the screen. Add a nice comment about using the visiom prompt"}

        return text_json
    except Exception as e:
        return {"error": str(e)}
            

def generatePdfInference(parameters, user_id, role_id):
    try:
        query = parameters.get("query")
        system_prompt = """You are an expert reader that recieves a full pdf converted to text. You will always reply a json with the key fragment and the value of the text fragment that contains 
        the answer to the question. Do no add more keys, do not add more text and anything except the json, do not even bother to say hello or goodbye. Just give the text. If the answer is not in the text, just say that you could not find it."""
        text = ""
        folder_path = f"pdf/user_{user_id}/role_{role_id}"
        file_name = [file for file in os.listdir(folder_path) if file.endswith(".txt")][0]  
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read().replace('\n', ' ')
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Find the answer to the question: {query} on this text: {text}"}]
        response = generate_response(client, messages)
        response = extract_json(response)
        text_json = json.loads(response)
        text_json["message"] = "Tell the user the answer is on screen, and explain the inference you made, do not add the answer on your response, just tell the user to look at the screen and explain the inference. Add a nice comment about using the visiom prompt only if that does not compomise a complete explanation"
        return text_json
    except Exception as e:
        return {'error': str(e)}
    

def generatePdfText(params, user_id, role_id):
    try:
        type_of_text = params.get("type_of_text")
        topic = params.get("topic")
        language = params.get("language")
        other_characteristics = params.get("other_characteristics")
        system_prompt = """You are an expert writter. Your labour is to generate a medium to long text based on the user requirements.\n
        You will always reply with a text formatted in html in order to convert it to pdf. Do not add more keys, do not add more text and anything except the text. Do not even bother to say hello or goodbye. Just give the text."""
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Generate a {type_of_text} about {topic} in {language} taking into account {other_characteristics}"}]
        response = generate_response(client, messages)
        connection = database_connection(
            {
             "user": os.getenv('user'), 
             "password": os.getenv('password'), 
             "host": os.getenv('host'), 
             "db": os.getenv('db')
            }
        )
        cursor = connection.cursor()
        sql = "INSERT INTO investigator_long_texts (user_id, long_text) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, response))
        connection.commit()
        connection.close()
        return {"message": "Text generated successfully, tell the user to download the pdf by clicking on the button that is on the investigator section on home page. Add a nice comment about using the visiom prompt"}
    except Exception as e:
        return {"error": str(e)}


def investigator_tools():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generateText",
                "description": "Generate a any kind of text the user wants to generate. But only for short texts like introductions, summaries, conclusions, emails, short arguments, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "typeOfText": {
                            "type": "string",
                            "description": "The type of text the user wants to generate."
                        },
                        "topic": {
                            "type": "string",
                            "description": "The topic of the text the user wants to generate."
                        },
                        "language": {
                            "type": "string",
                            "description": "The language of the text the user wants to generate. If the language is not specified, the default language is the user's language."
                        },
                        "otherCharacteristics": {
                            "type": "string",
                            "description": "Other characteristics the user wants the text to have. Example: formal, informal, academic, maximum length, etc."
                        }
                    },
                    "required": ["typeOfText", "topic"]
                }
            }
        },

        {
            "type": "function",
            "function": {
                "name": "getPapers",
                "description": "Search for papers (academic documents) based on the query the user specifies.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query the user wants to search for. For default you have to translate the query to english. But if the user specifies a language, you have to adjust the query to that language."
                        },
                        "start_year": {
                            "type": "string",
                            "description": "The start year of the papers the user wants to search for. If the user does not specify a start year use value None."
                        }
                    },
                    "required": ["query"]
                }
            }
        },

        {
            "type": "function",
            "function": {
                "name": "generatePdfInference",
                "description": "Get information from a pdf document based on the query the user specifies.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What the users wants to know about the pdf document."
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generatePdfText",
                "description": "Generate a medium to long text based on the user requirements that will be converted to a pdf. Example: essays, articles, reports, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type_of_text": {
                            "type": "string",
                            "description": "The type of text the user wants to generate."
                        },
                        "topic": {
                            "type": "string",
                            "description": "The topic of the text the user wants to generate."
                        },
                        "language": {
                            "type": "string",
                            "description": "The language of the text the user wants to generate. If the language is not specified, the default language is the user's language."
                        },
                        "other_characteristics": {
                            "type": "string",
                            "description": "Other characteristics the user wants the text to have. Example: formal, informal, academic, maximum length, main ideas, focus topics, needed specifications, etc."
                        }
                    },
                    "required": ["type_of_text", "topic"]
                }
            }
        }
    ]

    available_functions = {
        "generateText": generateText,
        "getPapers": getPapers,
        "generatePdfInference": generatePdfInference,
        "generatePdfText": generatePdfText
    }
    return tools, available_functions



def get_html_pdf(user_id):
    connection = database_connection(
        {
         "user": os.getenv('user'), 
         "password": os.getenv('password'), 
         "host": os.getenv('host'), 
         "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    sql = "SELECT long_text FROM investigator_long_texts WHERE user_id = %s"
    cursor.execute(sql, (user_id,))
    long_text = cursor.fetchone()
    connection.close()
    return long_text[0] if long_text else None
