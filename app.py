from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_session import Session
import threading
import os
from functools import wraps
from dotenv import load_dotenv
from services.chat import Chat, AI_response, check_current_conversation, create_voice, send_intro, send_bye
from services.roles import return_role, roles_list, return_tools
from services.vision import Vision, manage_image
from services.support import new_apartment, save_pdf, return_apartments, new_email, return_emails, delete_email, get_reservations
from tools.conversation import generate_response
from openai import OpenAI
from groq import Groq
from services.database import Database
import json
from redis import Redis
from elevenlabs.client import ElevenLabs
import mimetypes
from flask_cors import CORS
mimetypes.add_type('application/javascript', '.js')

load_dotenv()

os.environ['REPLICATE_API_TOKEN'] = os.getenv('REPLICATE_API_TOKEN')
# client =  Groq(api_key=os.environ.get("GROP_API_TOKEN"))

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))
voice_client = ElevenLabs(api_key=os.getenv("ELEVEN_LABS_API_KEY"))
# tiny_model = whisper.load_model('tiny')
app = Flask(__name__, static_folder='frontend', static_url_path='/')
app.secret_key = "hola34"

SESSION_TYPE = 'redis'
SESSION_REDIS = Redis(host='localhost', port=6379)
app.config.from_object(__name__)
Session(app)
CORS(app)



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
                    return jsonify({'error': 'No face detected in the image'})
            else:
                return jsonify({'error': 'Error saving image'})
    return send_from_directory(app.static_folder, 'templates/home.html')
    

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
                return send_from_directory(app.static_folder,'templates/login.html')
        except Exception as e:
            return jsonify({'error': str(e)})
    return send_from_directory(app.static_folder,'templates/login.html')




@app.route('/chat/<int:role_id>', methods=['GET', 'POST'])
@login_required
def index(role_id):
    user_id = session['user_id']
    vision = Vision(user_id)
    role_id = int(role_id)
    session['role_id'] = role_id
    if role_id not in roles_list:
        return redirect(url_for('role_error'))
    if request.method == 'POST':
        try:
            if 'image' in request.files:
                image_file = request.files['image'] 
                name = vision.start_image_recognition(image_file, user_id)
                vision_prompt = vision.what_is_in_image(os.getenv('OPENAI_API_TOKEN'), user_id)
                print("vision prompt:", vision_prompt)
                if name:
                    print("el nombre es:", name)
                    db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
                    conversation, resume = db.init_conversation(user_id, client, role_id)
                    system_prompt = return_role(user_id, role_id, name, vision_prompt)
                    if conversation:
                        chat = Chat(conversation=conversation, client=client, resume = resume, system_prompt=system_prompt, name=name)
                    else:
                        chat = Chat(client=client, system_prompt=system_prompt, name=name)
                    session['chat'] = chat.get_messages()
                    return jsonify({"name": name})
                else:
                    return jsonify({'stop': 'stop'})
        except Exception as e:
            return jsonify({'error': str(e)})
    return send_from_directory(app.static_folder,'index.html')



@app.route('/audio', methods=['GET', 'POST'])
def recibir_audio():
    role_id = session['role_id']
    tools, available_functions = return_tools(role_id)
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            user_input = request.get_json().get('message')
            print("el mensaje es:", user_input)
            if user_input == "welcome":
                 return jsonify(messages = send_intro())
            elif user_input == "goodbye":
                return jsonify(messages = send_bye())
            else:
                messages = json.loads(session['chat'])
                ai_response, display_responses = AI_response(client, user_input, messages, tools, available_functions, role_id, user_id)
                message_response = create_voice(voice_client, user_id, ai_response)
                session['chat'] = json.dumps(messages)

                print("display responses:", display_responses)  
                print(type(display_responses))

                return jsonify(messages=message_response, display_responses=display_responses)
        except Exception as e:
            return jsonify({'error': str(e)})
        


@app.route('/save', methods=['GET', 'POST'])
def save():
    if request.method == 'POST':
        role_id = int(request.form['role_id'])
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

@app.route('/logout', methods=['POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('login'))

@app.route('/check_session')
def check_session():
    return jsonify({'logged_in': 'user_id' in session})

@app.route("/role_error")
def role_error():
    return "<h1>Role not valid </h1>"

@app.route("/chat")
@login_required
def chat_error():
    return redirect(url_for('role-error'))


@app.route('/avatar')
def avatar_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'src', 'assets'), filename)
@app.route('/models/<path:filename>')
def serve_models(filename):
    return send_from_directory(os.path.join(app.static_folder, 'public', 'models'), filename)
@app.route('/animations/<path:filename>')
def serve_animations(filename):
    return send_from_directory(os.path.join(app.static_folder, 'public', 'animations'), filename)

@app.route('/src/<path:filename>')
def serve_jsx(filename):
    return send_from_directory(os.path.join(app.static_folder, 'src'), filename, mimetype='application/javascript')


@app.route('/audio_prueba', methods=['POST'])
def audio_prueba():
    message = request.get_json()
    system_prompt ="""You are an avatar virtual assistant named NAIA.
        You will always reply with a JSON array of messages. With a maximum of 3 messages.
        Each message has a text, facialExpression, and animation property.
        The different facial expressions are: smile, sad, angry, surprised, funnyFace, and default.
        The different animations are: Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, and Angry. """
    text = generate_response(client, [{"role": "system", "content":  system_prompt}
                                      ,{"role": "user", "content": message["message"]}])

    message_response = create_voice(voice_client, 1, text)

    return jsonify(messages = message_response)

@app.route('/pdfreader', methods=['POST'])
def pdfreader():
    if request.method == 'POST':
        try:
            file = request.files['pdf']
            user_id = session['user_id']
            role_id = session['role_id']
            save_pdf(user_id, file, role_id)
            return jsonify({'result': 'ok'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        

@app.route('/apartment', methods=['GET', 'POST'])
def apartment():
    if request.method == "POST": 
        try:
            data = request.get_json()
            user_id = session['user_id']
            apartment = data.get('apartmentNumber')
            phone = data.get('apartmentPhone')
            result = new_apartment(apartment, phone, user_id)
            return result
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    if request.method == "GET":
        try:
            user_id = session['user_id']
            apartments_json = return_apartments(user_id)
            return jsonify(apartments_json)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/email', methods=['POST', 'GET', 'DELETE'])
def email():
    if request.method == "POST":
        try:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            user_id = session['user_id']
            result = new_email(name, email, user_id)
            return result
        except Exception as e:
            return jsonify({'error': str(e)}), 500     
    if request.method == "GET":
        try:
            user_id = session['user_id']
            emails_json = return_emails(user_id)
            return jsonify(emails_json)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    if request.method == "DELETE":
        try:
            user_id = session['user_id']
            delete_email(user_id)
            return "Email deleted successfully"
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
@app.route('/reservations', methods=['GET'])
def reservations():
    if request.method == "GET":
        try:
            user_id = session['user_id']
            reservations = get_reservations(user_id)
            print("reservations:", reservations)
            return jsonify({"reservation": reservations})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


if __name__ == "__main__":  
    app.run(debug=True, host='0.0.0.0', port=5000,
           ssl_context=('cert.pem', 'key.pem') )
   