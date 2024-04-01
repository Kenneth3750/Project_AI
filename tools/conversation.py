#this script contains the main tools to handle a chat conversation between the user and the bot
import pyttsx3
import os
import subprocess
from mistralai.models.chat_completion import ChatMessage

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
    
def generate_response(client, messages):
    model = "open-mixtral-8x7b"
    chat_response = client.chat(
        model=model,
        messages=messages
        )
    return chat_response.choices[0].message.content

def remove_audio(audio_path, output_path):
    if os.path.exists(audio_path):
        os.remove(audio_path)
    if os.path.exists(output_path):
        os.remove(output_path)
 

def listen_to_user(audio_file):
    audio_path = 'audio.mp3'
    audio_file.save(audio_path)
    output_path = 'audio_convertido.wav'
    subprocess.run(["ffmpeg",  "-i", "audio.mp3", "audio_convertido.wav"])    
    return output_path