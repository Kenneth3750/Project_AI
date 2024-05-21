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

max_tokens = 1000

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
    model="gpt-4o",
    messages=messages
    )

    return completion.choices[0].message.content


def remove_audio_tool(audio_path, output_path):
    if os.path.exists(audio_path):
        os.remove(audio_path)
    if os.path.exists(output_path):
        os.remove(output_path)
 

def listen_to_user_tool(audio_file):
    audio_path = 'audio.mp3'
    audio_file.save(audio_path)
    output_path = 'audio_converted.wav'
    subprocess.run(["ffmpeg",  "-i", "audio.mp3", "audio_converted.wav"])    
    return output_path

def speech_to_text(model, audio):
    text = model.transcribe(audio)
    return text

def translate_from_whisper_api(client, audio_file):
    audio = open(audio_file, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio, 
    )
    audio.close()
    print("respuesta desde la api")
    return transcription.text

def make_resume_prompt(conversation):
    encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')
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
    encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')
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
        audio = client.generate(
            text = text,
            voice = "Rachel",
            model = "eleven_multilingual_v2"
        )
        save(audio, f"audio/user_{user_id}/audio_{index}.mp3")
    except Exception as e:
        print("Error al crear el audio:", e)
        return None
    
def lipSync(user_id, index):
    try:
        start_time = time.time()
        
        # -y to overwrite the file
        subprocess.run(f'ffmpeg -y -i audio/user_{user_id}/audio_{index}.mp3 audio/user_{user_id}/audio_{index}.wav', shell=True,  stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f'Conversion done in {time.time() - start_time}ms')
        
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