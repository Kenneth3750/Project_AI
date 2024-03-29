#this script contains the main tools to handle a chat conversation between the user and the bot
import pyttsx3
import replicate
import speech_recognition as sr


def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def generate_response(prompt_input, string_dialogue):   
    output = replicate.run("mistralai/mixtral-8x7b-instruct-v0.1", 
                           input={
                                "top_k": 50,
                                "top_p": 0.9,
                                "prompt":f"{string_dialogue} {prompt_input} " ,
                                "temperature": 0.6,
                                "max_new_tokens": 1024,
                                "prompt_template": "<s>[INST] {prompt}  [/INST] ",
                                "presence_penalty": 0,
                                "frequency_penalty": 0
                           })
    return output

def listen_to_user():
    with sr.Microphone() as source:
        recognizer = sr.Recognizer()
        source.pause_threshold = 2
        audio = recognizer.listen(source, phrase_time_limit=None, timeout=None)
    return audio