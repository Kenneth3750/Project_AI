import whisper
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
import threading
import os
from functools import wraps
from dotenv import load_dotenv
from services.chat import Chat, AI_response, check_current_conversation
from services.roles import return_role
from services.vision import Vision, manage_image
from openai import OpenAI
from groq import Groq
from services.database import Database
import json
from redis import Redis
import requests




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
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Load environment variables from .env file a
load_dotenv()

os.environ['REPLICATE_API_TOKEN'] = os.getenv('REPLICATE_API_TOKEN')
# client =  Groq(
#     api_key=os.environ.get("GROP_API_TOKEN"),
# )

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))
tiny_model = whisper.load_model('tiny')
app = Flask(__name__)
app.secret_key = "hola34"


SESSION_TYPE = 'redis'
SESSION_REDIS = Redis(host='localhost', port=6379)
app.config.from_object(__name__)
Session(app)


lock = threading.Lock()
conditional_lock = threading.Condition(lock)

ai_response_running = None
is_running = None
ai_response = None
role_id = 1

def main(client, tiny_model, user_input, messages):
    tiny_model = tiny_model
    global is_running
    global ai_response_running
    global ai_response
    try:
        user_input = user_input
 
        lock.acquire()
        ai_response_running = True
        ai_response = AI_response(client, user_input, messages)
        ai_response_running = False
        lock.release()
    except Exception as e:
        print("An error occurred: ", e)


@app.route('/', methods=['GET', 'POST'])
def root():
    if "user_id" in session:
        return redirect(url_for("home"))
    else:
        return redirect(url_for("login"))
    


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    user_id = session['user_id']
    if request.method == 'POST':    
        file = request.files['image']
        name = request.form['personName']
        if file:
            image = manage_image(file, name, user_id)
            if image:
                vision = Vision(user_id)
                if name in vision.known_face_names:
                    return jsonify({'result': 'ok'})
                else:
                    return jsonify({'error': 'Error saving image'})
            else:
                return jsonify({'error': 'Error saving image'})
    return render_template('home.html')
    

@app.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
    if request.method == 'POST':
        user_name = request.form['username']
        password = request.form['password']
        try:
            user_id = db.check_user(user_name, password)
            if user_id:
                session['user_id'] = user_id
                return redirect(url_for('login'))
            else:
                return render_template('login.html')
        except Exception as e:
            return jsonify({'error': str(e)})
    return render_template('login.html')




@app.route('/chat', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    vision = Vision(user_id)
    global role_id
    if request.method == 'POST':
        if 'image' in request.files:
            image_file = request.files['image'] 
            name = vision.start_image_recognition(image_file, user_id)
            vision_prompt = vision.what_is_in_image(os.getenv('OPENAI_API_TOKEN'), user_id)
            print("vision prompt:", vision_prompt)
            if name:
                print("el nombre es:", name)
                db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
                conversation, resume = db.init_conversation(user_id, client, role_id)
                system_prompt = return_role(role_id, name, vision_prompt)
                if conversation:
                    chat = Chat(conversation=conversation, client=client, resume = resume, system_prompt=system_prompt)
                else:
                    chat = Chat(client=client, system_prompt=system_prompt)
                session['chat'] = chat.get_messages()
            else:
                return jsonify({'stop': 'stop'})
    return render_template('index.html')



@app.route('/audio', methods=['GET', 'POST'])
def recibir_audio():
    global ai_response_running
    global ai_response
    print("session chat:", session['chat'])
    if request.method == 'POST':
        try:
            user_input = request.form['user']
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
    app.run(debug=True, host='0.0.0.0', port=5000, 
                 ssl_context=('cert.pem', 'key.pem'))
   





