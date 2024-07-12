#this file contains all functions for the investigator role
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))
current_year = 2024
#response key is display
def generateText(parameters):
    typeOfText = parameters.get("typeOfText")
    topic = parameters.get("topic")
    language = parameters.get("language")
    otherCharacteristics = parameters.get("otherCharacteristics")
    system_prompt = """You are an expert writter. You will always reply a json with the key display and the value of the text you generated.
    Do no add more keys, do not add more, do not even bother to say hello or goodbye. Just give the text."""
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Generate a {typeOfText} about {topic} in {language} taking into account {otherCharacteristics}"}],
    )
    print(completion.choices[0].message.content)
    text_json = json.loads(completion.choices[0].message.content) 
    return text_json


def getPapers(parameters):
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
            if "inline_links" not in result or "cited_by" not in result["inline_links"]:
                new_json.append(f'<div><h5><strong>Paper {i+1}:</strong> {result["title"]}</h5><ul><li>{result["snippet"]}</li><li><strong>Additional info:</strong> {result["publication_info"]}</li><li><strong>Link:</strong> {result["link"]} </li></ul></div><br>')
            else:
                new_json.append(f'<div><h5><strong>Paper {i+1}:</strong> {result["title"]}</h5><ul><li>{result["snippet"]}</li><li><strong>Additional info:</strong> {result["publication_info"]}</li><li><strong>Link:</strong> {result["link"]} </li><li>Cited by: {result["inline_links"]["cited_by"]["total"]}</li></ul></div><br>')

            i+=1
            if i==5:
                break

        single_string = ''.join(new_json)
        text_json = {"display": single_string}

        return text_json
    except Exception as e:
        return {"display": "An error occurred while trying to get the papers. Please try again later."}
            


def investigator_tools():
        tools =  [
    {
        "type": "function",
        "function": {
            "name": "generateText",
            "description": "This function displays on screen the fragment of text the user requested for. It does not generate full text text, only fragments like introductions, conclusions, objectives, etc.",
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
                "description": "This function gives the user the articles or papers he/she requested fot. It does not display the full papers, only the title, the snippet, and the publication info.",
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
    }
]

        available_functions = {
            "generateText": generateText,
            "getPapers": getPapers
        }
        return tools, available_functions
