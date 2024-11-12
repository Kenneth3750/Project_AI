#this script contains the main tools to handle a chat conversation between the user and the bot
import pyttsx3
import os
import subprocess
import openai
import json
import time
from elevenlabs import play, save
import base64 
import tiktoken
import re
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging():
    """Configure logging for the entire application"""
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Set to DEBUG to see all logs

        # Format for the logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # File handler with rotation
        log_file = os.path.join('logs', 'flask_app.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=10,
            mode='a'  # Append mode
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        if root_logger.handlers:
            root_logger.handlers.clear()

        # Add handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        return logging.getLogger(__name__)

    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise

logger = setup_logging()

max_tokens = 5000
function_model = "gpt-4o-mini"
def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


# def generate_response(prompt_input, string_dialogue):   
#     output = replicate.run("mistralai/mixtral-8x7b-instruct-v0.1", 
#                            input={
#                                 "top_k": 50,
#                                 "top_p": 0.9,
#                                 "prompt":f"{string_dialogue} {prompt_input} " ,
#                                 "temperature": 0.6,
#                                 "max_new_tokens": 1024,
#                                 "prompt_template": "<s>[INST] {prompt}  [/INST] ",
#                                 "presence_penalty": 0,
#                                 "frequency_penalty": 0
#                            })
#     return output
    
# def generate_response(client, messages):
#     model = "open-mixtral-8x7b"
#     chat_response = client.chat(
#         model=model,
#         messages=messages
#         )
#     return chat_response.choices[0].message.content
    
def generate_response(client, messages):
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages
    )
    return completion.choices[0].message.content


def generate_response_with_tools(client, messages, tools, available_functions, role_id, user_id, language):
    user_id = user_id
    role_id = role_id
    try:
        tools = json.loads(tools)
        completion = client.chat.completions.create(
            model=function_model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        response = completion.choices[0].message
        display_responses = []
        if response.content is not None:
            first_response = extract_json(response.content)
            first_response = convert_to_array_json(first_response)
            return first_response, display_responses

        i = 1
        tool_calls = response.tool_calls
        if tool_calls:
            messages.append(response)
            print("respose:", response)
            logger.info("Tool calls: %s", tool_calls)
            for tool_call in tool_calls:
                i += 1
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(function_args, user_id, role_id)
                if function_response.get("display"):
                    display_responses.append({"display": function_response.get("display")})
                if function_response.get("fragment"):
                    display_responses.append({"fragment": function_response.get("fragment")})
                print("function_response:", function_response)
                logger.info("Function response: %s", function_response)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(function_response),
                    }
                ) 
            second_completion = client.chat.completions.create(
                    model=function_model,
                    messages=messages        
                )
            messages.append({"role": "assistant", "content": second_completion.choices[0].message.content})

            second_response = second_completion.choices[0].message

            second_response = extract_json(second_response.content)
            second_response = convert_to_array_json(second_response)
        
            remove_i_elements_from_penultimate(messages, i)

            return second_response, display_responses
    except Exception as e:
        print("Error en generate_response_with_tools:", e)
        return return_generate_error_audio(language), []
    

def return_generate_error_audio(language):
    if language == "es":
        text_1 = "Lo siento, hubo un problema generando la respuesta"
        text_2 = "Por favor, inténtalo de nuevo y si el problema persiste, reinicia la aplicación."
        audio_1 = "sorry_es.mp3"
        audio_2 = "tryagain_es.mp3"
    elif language == "en":
        text_1 = "Sorry, there was a problem generating the response."
        text_2 = "Please try again and if the problem persists, restart the application."
        audio_1 = "sorry_en.mp3"
        audio_2 = "tryagain_en.mp3"
    
    message = [{
        "text": text_1,
        "facialExpression": "sad",
        "audio": audio_file_to_base64(f"audio/{audio_1}"),
        "lipsync": read_json_transcript("audio/default.json"),
        "animation": "Crying"
        },
        {
            "text": text_2,
            "facialExpression": "default",
            "audio": audio_file_to_base64(f"audio/{audio_2}"),
            "lipsync": read_json_transcript("audio/default.json"),
        }
    ]
    return message
    
def remove_i_elements_from_penultimate(messages, i):
    penultimate_index = len(messages) - 2
    start_index = max(penultimate_index - i + 1, 0)
    del messages[start_index:penultimate_index + 1]

def convert_to_array_json(response):
    response = json.loads(response)
    if isinstance(response, dict):
        response = [response]
    return json.dumps(response)




def serialize_chat_completion_message(chat_completion_message):
    serialized = {
        "content": chat_completion_message.content,
        "role": chat_completion_message.role,
        "function_call": chat_completion_message.function_call,
        "tool_calls": []
    }
    
    for tool_call in chat_completion_message.tool_calls:
        serialized_tool_call = {
            "id": tool_call.id,
            "function": {
                "arguments": tool_call.function.arguments,
                "name": tool_call.function.name
            },
            "type": tool_call.type
        }
        serialized["tool_calls"].append(serialized_tool_call)
    
    return serialized


def extract_json(response):
    clean_json = re.search(r'```json\n(.*?)\n```', response, flags=re.DOTALL)
    if clean_json:
        return clean_json.group(1)
    else:
        return response



def make_resume_prompt(conversation):
    encoding = tiktoken.encoding_for_model('gpt-4')
    token_count = len(encoding.encode(conversation))
    if token_count > max_tokens:
        conversation = json.loads(conversation)
        if conversation[0].get("role") == "system":
            conversation.pop(0)
        conversation.append({"role": "user", "content": "Make a resume of the conversation of no more than 250 words. Put at first the user's name if you know it."})
        return conversation
    else:
        return None
    
def count_tokens(text):
    encoding = tiktoken.encoding_for_model('gpt-4')
    token_count = len(encoding.encode(text))
    return token_count

def check_conversation_length(messages):
    tokens = count_tokens(messages)
    print(f"Tokens de la conversación: {tokens}")
    if tokens > max_tokens:
        return True
    else:
        return False
def get_role_prompt(comversation):
    json_conversation = json.loads(comversation)
    role_prompt = [json_conversation[0]]
    print("role prompt:", role_prompt)
    return role_prompt


def create_voice_file(client, user_id, text, index):
    try:
        if not os.path.exists(f"audio/user_{user_id}"):
            os.makedirs(f"audio/user_{user_id}")
        response = client.generate(
            model="eleven_multilingual_v2",
            voice ="Rachel",
            text = text
        )
        save(response, f"audio/user_{user_id}/audio_{index}.mp3")
    except Exception as e:
        print("Error al crear el audio:", e)
        return None
    
def lipSync(user_id, index):
    try:
        start_time = time.time()
        
        # -y to overwrite the file
        subprocess.run(f'ffmpeg -y -i audio/user_{user_id}/audio_{index}.mp3 audio/user_{user_id}/audio_{index}.wav', shell=True)
        print(f'Conversion done in {time.time() - start_time}ms')
        #,  stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        # -r phonetic is faster but less accurate
        subprocess.run(f'.\\bin\\rhubarb.exe -f json -o audio\\user_{user_id}\\audio_{index}.json audio\\user_{user_id}\\audio_{index}.wav -r phonetic', shell=True)        
        print(f'Lip sync done in {time.time() - start_time}ms')
    
    except Exception as e:
        print("Error al hacer el lip sync:", e)
        return None
    
def audio_file_to_base64(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode('utf-8')

def read_json_transcript(json_file_path):
    with open(json_file_path, "r") as json_file:
        return json.load(json_file)