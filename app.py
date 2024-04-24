import whisper
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
import threading
import os
from functools import wraps
from dotenv import load_dotenv
from services.chat import Chat, listen_to_user, AI_response, check_current_conversation
from services.roles import return_role
from mistralai.client import MistralClient
from openai import OpenAI
from services.database import Database
import json



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Load environment variables from .env file a
load_dotenv()

os.environ['REPLICATE_API_TOKEN'] = os.getenv('REPLICATE_API_TOKEN')
client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))
tiny_model = whisper.load_model('tiny')
app = Flask(__name__)
app.secret_key = "hola34"
socketio = SocketIO(app)
lock = threading.Lock()
conditional_lock = threading.Condition(lock)

ai_response_running = None
is_running = None
ai_response = None
role_id = 5

def main(client, tiny_model, user_input, messages):
    tiny_model = tiny_model
    global is_running
    global ai_response_running
    global ai_response
    try:
        user_input = user_input
 
        lock.acquire()
        ai_response_running = True
        ai_response = AI_response(client, user_input, socketio, messages)
        ai_response_running = False
        lock.release()
    except Exception as e:
        print("An error occurred: ", e)


@app.route('/', methods=['GET', 'POST'])
def home():
    if "user_id" in session:
        return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))
    

@app.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
    if request.method == 'POST':
        user_name = request.form['username']
        password = request.form['password']
        try:
            print(user_name, password)
            user_id = db.check_user(user_name, password)
            if user_id:
                session['user_id'] = user_id
                return redirect(url_for('index'))
            else:
                return render_template('login.html')
        except Exception as e:
            return jsonify({'error': str(e)})
    return render_template('login.html')




@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    global role_id
    if request.method == 'POST':
        user_id = session['user_id']
        db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
        conversation, resume = db.init_conversation(user_id, client, role_id)
        system_prompt = return_role(role_id)
        if conversation:
            chat = Chat(conversation=conversation, client=client, resume = resume, system_prompt=system_prompt)
        else:
            chat = Chat(client=client, system_prompt=system_prompt)
        session['chat'] = chat.get_messages()
    return render_template('index.html')



@app.route('/audio', methods=['GET', 'POST'])
def recibir_audio():
    global ai_response_running
    global ai_response
    print("session chat:", session['chat'])
    if request.method == 'POST':
        try:
            user_input = request.form['user']
            print(user_input)
            messages = json.loads(session['chat'])

            mainthread = threading.Thread(target=main, args=(client, tiny_model,  user_input, messages))
            mainthread.start()
            mainthread.join()        
            session['chat'] = json.dumps(messages)


            return {"result": "ok", "text": f"{ai_response}"}
        except Exception as e:
            return jsonify({'error': str(e)})
        


@app.route('/save', methods=['GET', 'POST'])
def save():
    global role_id
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
            conversation = session['chat']
            db.save_current_conversation(user_id, conversation, role_id)
            new_chat = check_current_conversation(conversation, client, db, user_id, role_id)
            if new_chat:
                session['chat'] = json.dumps(new_chat)
            return jsonify({'result': 'ok'})
        except Exception as e:
            return jsonify({'error': str(e)})

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('login'))

@app.route('/check_session')
def check_session():
    return jsonify({'logged_in': 'user_id' in session})


if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
   





