#this file contains all functions for the investigator role
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))

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
