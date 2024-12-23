from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory, abort
from flask_session import Session
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
from dotenv import load_dotenv
from services.chat import Chat, AI_response, check_current_conversation, create_voice, send_intro, send_bye, add_new_vision_prompt
from services.roles import return_role, roles_list, return_tools
from services.vision import Vision, manage_image, manage_current_image, current_image_description, list_known_people_names,change_image_name, return_user_image, delete_user_image
from services.support import new_apartment, save_pdf, return_apartments, new_email, return_emails, get_user_useful_info, get_reservations, delete_apartment, add_area, get_areas, delete_area, save_token, delete_contact_email, get_summary, get_pdf
from services.support import return_university_emails, set_university_email
from tools.conversation import generate_response
from openai import OpenAI
from groq import Groq
from services.database import Database
import json
from redis import Redis
from elevenlabs.client import ElevenLabs
import mimetypes
from authlib.integrations.flask_client import OAuth
import authlib.integrations.base_client.errors
from flask_cors import CORS
from config import authorized_emails
import re
import logging
from logging.handlers import RotatingFileHandler
import sys
mimetypes.add_type('application/javascript', '.js')


load_dotenv()


# client =  Groq(api_key=os.environ.get("GROP_API_TOKEN"))

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))
voice_client = ElevenLabs(api_key=os.getenv("ELEVEN_LABS_API_KEY"))
# tiny_model = whisper.load_model('tiny')
app = Flask(__name__, static_folder='frontend', static_url_path='/')
app.secret_key = "hola34"
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

SESSION_TYPE = 'redis'
SESSION_REDIS = Redis(host='localhost', port=6379)
app.config.from_object(__name__)
Session(app)
CORS(app)
google_client_id = os.getenv('GOOGLE_CLIENT_ID')
google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

oauth = OAuth(app)
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
            'access_type': 'offline',  
            'prompt': 'consent',
            'include_granted_scopes': 'true'
        }
    )

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


@app.errorhandler(403)
def forbidden(e):
    return "Access denied", 403


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'google_token' not in session:
            return redirect(url_for('before_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'google_token' in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function



@app.route('/', methods=['GET', 'POST'])
def root():
    if "google_token" in session:
        try:
            token = session['google_token']
            user = token.get('userinfo')
            print("User info:", user)
            return redirect(url_for("home"))
        except authlib.integrations.base_client.errors.MissingTokenError:
            session.clear()
            return redirect(url_for("before_login"))
    else:
        return redirect(url_for("before_login"))
    
@app.route('/login', methods=['GET', 'POST'])
def before_login():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return send_from_directory(app.static_folder, 'templates/login.html')

@app.route('/google_login', methods=['GET', 'POST'])
@logout_required
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri, access_type='offline', prompt='consent')

@app.route('/authorize')
def authorize():
    try:
        db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
        token = oauth.google.authorize_access_token()
        print("Token:", token)
        print("*"*20)
        user = token.get('userinfo')
        if user:
            user_email = user.get('email')
            if user_email not in authorized_emails:
                return redirect(url_for('unauthorized'))
            session['google_token'] = token
            user_id = db.check_and_create_user(user)
            print("User id:", user_id)
            if user_id:
                session['user_id'] = user_id
            print("User info:", user)
            save_token(session["user_id"], token)
            return redirect(url_for('home'))
        else:
            print("Failed to get user info")
            return redirect(url_for('before_login'))
    except Exception as e:
        print(f"Error in authorize: {str(e)}")
        return redirect(url_for('before_login'))

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if request.method == 'POST' or request.method == 'GET':
        session.clear()
        return redirect(url_for('before_login'))

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if not session.get('user_id') and request.method == 'GET':
        session.clear()
        return redirect(url_for('before_login'))
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
                if name:
                    print("el nombre es:", name)
                    db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
                    conversation, resume = db.init_conversation(user_id, client, role_id)
                    system_prompt = return_role(user_id, role_id, name)
                    if conversation:
                        chat = Chat(conversation=conversation, client=client, resume = resume, system_prompt=system_prompt, name=name, vision_prompt=vision_prompt)
                    else:
                        chat = Chat(client=client, system_prompt=system_prompt, name=name, vision_prompt=vision_prompt)
                    session['chat'] = chat.get_messages()
                    session['name'] = name
                    return jsonify({"name": name})
                else:
                    return jsonify({'stop': 'stop'})
        except Exception as e:
            return jsonify({'error': str(e)})
    elif request.method == 'GET':
        return send_from_directory(app.static_folder,'index.html')



@app.route('/audio', methods=['GET', 'POST'])
def recibir_audio():
    role_id = session['role_id']
    user_id = session['user_id']
    tools, available_functions = return_tools(role_id, user_id)
    if request.method == 'POST':
        try:
            user_input = request.get_json().get('message')
            language = request.get_json().get('language')[0:2]
            print("el mensaje es:", user_input)
            if user_input == "welcome":
                 return jsonify(messages = send_intro())
            elif user_input == "goodbye":
                return jsonify(messages = send_bye())
            else:
                messages = json.loads(session['chat'])

                ai_response, display_responses = AI_response(client, user_input, messages, tools, available_functions, role_id, user_id, language)
                message_response = create_voice(voice_client, user_id, ai_response)
                session['chat'] = json.dumps(messages)

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
            value = db.save_current_conversation(user_id, conversation, role_id)
            if value:
                new_chat = check_current_conversation(conversation, client, db, user_id, role_id)
                if new_chat:
                    session['chat'] = json.dumps(new_chat)
            return jsonify({'result': 'ok'})
        except Exception as e:
            return jsonify({'error': str(e)})
        
@app.route('/saveCurrent', methods=['POST'])
def save_current():
    if request.method == "POST":
        try:
            user_id = session['user_id']
            name = session['name']
            print("name:", name)
            if "image" in request.files:
                image_file = request.files['image']
                result = manage_current_image(image_file, user_id)
                if result:
                    messages = json.loads(session['chat'])
                    vision_prompt = current_image_description(os.getenv('OPENAI_API_TOKEN'), user_id)
                    new_prompt = f"This is the new vision prompt: {vision_prompt}"
                    messages.append({"role": "user", "content": new_prompt})
                    session['chat'] = json.dumps(messages)
                    return jsonify({'result': 'ok'})
                else:
                    return jsonify({'error': 'Error saving image'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    
@app.route('/check_session')
def check_session():
    return jsonify({'logged_in': 'google_token' in session})

@app.route("/role_error")
def role_error():
    return "<h1>Role not valid </h1>"
@app.route("/unauthorized")
def unauthorized():
    return "<h1>You are not authorized to access this page</h1>"

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

@app.route('/user-info')
def get_user_info():
    try:
        user_id = session['user_id']
        db = Database({"user": os.getenv('user'), "password": os.getenv('password'), "host": os.getenv('host'), "db": os.getenv('db')})
        full_name, image_url, name = db.get_user_info(user_id)
        return jsonify({"name": full_name, "image": image_url, "given_name": name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/users', methods=['GET', 'PUT'])
def users():
    user_id = session['user_id']
    if request.method == 'GET':
        try:
            users = list_known_people_names(user_id)
            return jsonify(users)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    elif request.method == 'PUT':
        try:
            data = request.json
            old_username = data['oldUsername']
            new_username = data['newUsername']
            change_image_name(new_username, old_username, user_id)
            return jsonify({"message": "Username updated successfully"})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
@app.route('/users/<username>', methods=['GET', 'DELETE'])
def user(username):
    user_id = session['user_id']
    if request.method == 'GET':
        try:
            photo = return_user_image(user_id, username)
            return jsonify({'photo': photo})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif request.method == 'DELETE':
        try:
            delete_user_image(user_id, username)
            return jsonify({"message": "User deleted successfully"})
        except Exception as e:
            return jsonify({'error': str(e)}), 500



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

@app.route('/pdfreader', methods=['POST', 'GET'])
def pdfreader():
    user_id = session['user_id']
    if request.method == 'POST':
        try:
            file = request.files['pdf']
            role_id = session['role_id']
            save_pdf(user_id, file, role_id)
            return jsonify({'result': 'ok'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        try:
            pdf_path = os.path.join("pdf", f"user_{user_id}", "role_1" )
            pdf_files = [file for file in os.listdir(f"{pdf_path}") if file.endswith(".pdf")]
            if len(pdf_files) == 1:
                pdf_filename = pdf_files[0]
            else:
                pdf_filename = None
            print("pdf_filename:", pdf_filename)
            return jsonify({"pdf_filename": pdf_filename})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


        

@app.route('/apartment', methods=['GET', 'POST', 'DELETE'])
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
    elif request.method == "GET":
        try:
            user_id = session['user_id']
            apartments_json = return_apartments(user_id)
            return jsonify(apartments_json)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif request.method == "DELETE":
        try:
            data = request.get_json()
            apartment = data.get('apartmentNumber')
            user_id = session['user_id']
            delete_apartment(user_id, apartment)
            return "Apartment deleted successfully"
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
            name = request.get_json().get('name')
            email = request.get_json().get('email')
            user_id = session['user_id']
            delete_contact_email(user_id, name, email)
            return "Email deleted successfully"
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == "GET":
        try:
            user_id = session['user_id']
            reservations = get_reservations(user_id)
            print("reservations:", reservations)
            return jsonify({"reservation": reservations})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

        
@app.route('/areas', methods=['POST', 'GET', 'DELETE'])
def areas():
    if request.method == "GET":
        try:
            user_id = session['user_id']
            areas = get_areas(user_id)
            return jsonify({"areas": areas})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == "POST":
        try:
            data = request.get_json()
            user_id = session['user_id']
            new_area = data.get('area')
            add_area(user_id, new_area)
            return jsonify({"message": "Area added successfully"})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    elif request.method == "DELETE":
        try:
            data = request.get_json()
            user_id = session['user_id']
            area = data.get('area')
            delete_area(user_id, area)
            return jsonify({"message": "Area deleted successfully"})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
@app.route('/trainer', methods=['GET'])
def get_summary_trainer():
    user_id = session['user_id']
    try:
        html = get_summary(user_id)
        print("html:", html)
        if html:
            return html
        else:
            return jsonify({'error': 'Error generating summary'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/investigator', methods=['GET'])
def investigator():
    user_id = session['user_id']
    if request.method == "GET":
        try:
            html = get_pdf(user_id)
            if html:
                print("html:", html)
                return html
            else:
                return jsonify({'error': 'Error generating pdf'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
@app.route('/saveLocation', methods=['POST'])
def save_location():
    user_id = session['user_id']
    try:
        location_json = request.get_json()
        print("location_json:", location_json)
        get_user_useful_info(user_id, location_json)
        return jsonify({'result': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/university', methods = ['GET', 'POST'])
def save_university_email():
    user_id = session['user_id']
    if request.method == "GET":
        try:
            emails = return_university_emails(user_id)
            return jsonify(emails)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif request.method == "POST":
        try:
            data = request.get_json()
            email = data.get('email')
            set_university_email(user_id, email)
            return jsonify({"message": "Email saved successfully"})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
@app.route('/uni_map', methods=['GET', 'POST'])
def uni_map():
    return send_from_directory(app.static_folder, 'static/img/uni_map.png')


if __name__ == "__main__":  
    app.run(debug=True, host='0.0.0.0', port=5000, 
           ssl_context=('cert.pem', 'key.pem'), threaded=True) 
    

   