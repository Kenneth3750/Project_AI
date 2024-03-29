from os import system
import speech_recognition as sr
import whisper
import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import threading
import os
from dotenv import load_dotenv
from services.chat import Chat
from tools.conversation import speak_text
from mistralai.client import MistralClient



# Load environment variables from .env file
load_dotenv()

os.environ['REPLICATE_API_TOKEN'] = os.getenv('REPLICATE_API_TOKEN')
client = MistralClient(api_key=os.getenv('MISTRAL_API_TOKEN'))
tiny_model = whisper.load_model('tiny')
app = Flask(__name__)
socketio = SocketIO(app)
lock = threading.Lock()
conditional_lock = threading.Condition(lock)
chat = Chat(tiny_model, client)
ai_response_running = None
is_running = None

def main(tiny_model):
    tiny_model = tiny_model
    global is_running
    global ai_response_running
    while is_running:
        try:
            filename = "input.wav"
            socketio.emit('informacion_del_servidor', {'data': 'Recording'})
            if not is_running:
                print(is_running)
                print('break1')
                break
            else: 
                audio = chat.listen_to_user()
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
                            ai_response_running = True
                            chat.AI_response(filename, socketio)
                            ai_response_running = False
                            lock.release()
        except Exception as e:
            print("An error occurred: ", e)


@app.route('/', methods=['GET', 'POST'])
def index():
    global is_running
    global ai_response_running

    ai_response_running = False
    is_running = False
    print(ai_response_running)
    print(is_running)
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
            socketio.emit('informacion_del_servidor', {'data': 'Sleeping...'})  
            lock.release()
            print('stop')

    return render_template('index.html')




if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0')
   





