from os import system
import speech_recognition as sr
from gpt4all import GPT4All
import replicate
import whisper
import os
import pyttsx3
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import threading
import os
from dotenv import load_dotenv



# Load environment variables from .env file
load_dotenv()

os.environ['REPLICATE_API_TOKEN'] = os.getenv('REPLICATE_API_TOKEN')
tiny_model = whisper.load_model('tiny')
is_running = False
app = Flask(__name__)
socketio = SocketIO(app)
lock = threading.Lock()
conditional_lock = threading.Condition(lock)
ai_response_running = False

def transcribe_audio_to_text(filename):
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except:
        print('Skipping unrecognized audio')


def generate_response(prompt):
    model = GPT4All("C:/Users/kenne/AppData/Local/nomic.ai/GPT4All//gpt4all-falcon-newbpe-q4_0.gguf")
    output = model.generate(prompt, max_tokens=200)
    return output

def generate_mixtral_response(prompt_input):
    string_dialogue = """You are a electronic engineer with a PhD, that enjoys to feel superior to other people.
    User:   """
    
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



def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def AI_response(filename, tiny_model):
    global is_running
    global ai_response_running
    ai_response_running = True
    audio_text = tiny_model.transcribe(filename)
    text = audio_text['text']
    if text:
        print(f"User: {text}")
        response = generate_mixtral_response(text)
        message = ''.join(response)
        full_respone = ''
        #for item in response:
            #full_respone += item
        print(f"AI: {full_respone}")
        speak_text(full_respone)
        print(f"AI: {message}")
        socketio.emit('informacion_del_servidor', {'data': 'Talking...'})
        speak_text(message)
    ai_response_running = False


def main(tiny_model):
    tiny_model = tiny_model
    global is_running
    while is_running:
        try:
            filename = "input.wav"
            socketio.emit('informacion_del_servidor', {'data': 'Recording'})
            with sr.Microphone() as source:
                recognizer = sr.Recognizer()
                source.pause_threshold = 2
                audio = recognizer.listen(source, phrase_time_limit=None, timeout=None)
            if not is_running:
                print(is_running)
                print('break2')
                break
            else:
                with open(filename, "wb") as f:
                    f.write(audio.get_wav_data())
                    if not is_running:
                        print(is_running)
                        print('breakBeforeAI')
                        break
                    else:    
                        socketio.emit('informacion_del_servidor', {'data': 'AI is thinking...'})
                        lock.acquire()
                        AI_response(filename, tiny_model)
                        lock.release()
        except Exception as e:
            print("An error occurred: ", e)







@app.route('/', methods=['GET', 'POST'])
def index():
    global is_running
    if request.method == 'POST':
        data = request.form['status']
        print(data)
        if data == 'start':
            is_running = True
            speak_text('Bienvenido, Kenneth')
            threading.Thread(target=main, args=(tiny_model,)).start()
        else:
            is_running = False
            lock.acquire()
            if ai_response_running:
                conditional_lock.wait()
            speak_text('Hasta luego')
            lock.release()
            print('stop')

    return render_template('index.html')




if __name__ == "__main__":
    socketio.run(app, debug=True)
   





