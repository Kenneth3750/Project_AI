import whisper
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import threading
import os
from dotenv import load_dotenv
from services.chat import Chat
from mistralai.client import MistralClient
from openai import OpenAI
from services.database import Database



# Load environment variables from .env file a
load_dotenv()

os.environ['REPLICATE_API_TOKEN'] = os.getenv('REPLICATE_API_TOKEN')
client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))
db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
tiny_model = whisper.load_model('tiny')
app = Flask(__name__)
socketio = SocketIO(app)
lock = threading.Lock()
conditional_lock = threading.Condition(lock)
chat = Chat(tiny_model, client)
ai_response_running = None
is_running = None
ai_response = None

def main(tiny_model, audio_file):
    tiny_model = tiny_model
    global is_running
    global ai_response_running
    global ai_response
    try:
        audio = audio_file
        socketio.emit('informacion_del_servidor', {'data': 'AI is thinking...'})
        lock.acquire()
        ai_response_running = True
        ai_response = chat.AI_response(audio, socketio)
        ai_response_running = False
        lock.release()
    except Exception as e:
        print("An error occurred: ", e)


@app.route('/', methods=['GET', 'POST'])
def index():
    history = db.init_conversation(1)
    if history:
        chat.history = history
        print("History: ", history)
        chat.print_history()
    else:
        print("No history")
    return render_template('index.html')

@app.route('/audio', methods=['GET', 'POST'])
def recibir_audio():
    global ai_response_running
    global ai_response
    if request.method == 'POST':
        try:
            audio_file = request.files['audio']
            audio = chat.listen_to_user(audio_file)
            mainthread = threading.Thread(target=main, args=(tiny_model,  audio))
            mainthread.start()
            mainthread.join()
            return {"result": "ok", "text": f"{ai_response}"}
        except Exception as e:
            return jsonify({'error': str(e)})



if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
   





