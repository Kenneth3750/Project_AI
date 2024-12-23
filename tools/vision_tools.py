
from PIL import Image
import os
import requests
import face_recognition
import base64 


def save_image(file, name, user_id):
    try:
        if not os.path.exists(f"known_people/user_{user_id}/{name}"):
            os.makedirs(f"known_people/user_{user_id}/{name}")
        image = Image.open(file)
        image = image.convert("RGB")
        image.save(f'known_people/user_{user_id}/{name}/image.jpg')
        if os.path.exists(f'known_people/user_{user_id}/{name}/image.jpg'):
            return True
        else:
            return False
    except Exception as e:
        print("An error occurred: ", e)
        return False


    
def save_current_image(file, user_id):
    if not os.path.exists(f"current/user_{user_id}"):
        os.makedirs(f"current/user_{user_id}")
    image = Image.open(file)
    image = image.convert("RGB")
    image.save(f'current/user_{user_id}/image.jpg')
    if os.path.exists(f'current/user_{user_id}/image.jpg'):
        return True
    else:
        return False


    
# def send_current_image(image_file):
#     if image_file.filename != '':
#         image_file.seek(0)
#         files = {'image': image_file}
#         response = requests.post('http://127.0.0.1:15000/current', files=files)
#         if response.status_code == 200:
#             print("Imagen enviada correctamente")
#             return True
#         else:
#             print("Error al enviar la imagen")
#             return False


def upload_configurations(user_id):
    known_face_encodings = []
    known_face_names = []
    if os.path.exists(f'known_people/user_{user_id}'):
        for person_name in os.listdir(f'known_people/user_{user_id}'):
            if os.path.isdir(f'known_people/user_{user_id}/{person_name}'):  # Solo procesa si es un directorio
                for filename in os.listdir(f'known_people/user_{user_id}/{person_name}'):
                    if filename.endswith('.jpg') or filename.endswith('.png'):  # Solo procesa archivos .jpg y .png
                        image = face_recognition.load_image_file(f'known_people/user_{user_id}/{person_name}/{filename}')
                        face_encodings = face_recognition.face_encodings(image)
                        if face_encodings:  
                            face_encoding = face_encodings[0]  
                            known_face_encodings.append(face_encoding)
                            known_face_names.append(person_name)  
    # print("known_face_encodings:", known_face_encodings)
    # print("known_face_names:", known_face_names)
    return known_face_encodings, known_face_names


def compare_faces(known_face_encodings, known_face_names, user_id):
    unknown_image = face_recognition.load_image_file(f'current/user_{user_id}/image.jpg')
    unknown_face_encodings = face_recognition.face_encodings(unknown_image)
    name = "Unknown"
    for unknown_face_encoding in unknown_face_encodings:
        results = face_recognition.compare_faces(known_face_encodings, unknown_face_encoding)
        name = "Unknown"

        if True in results:
            first_match_index = results.index(True)
            name = known_face_names[first_match_index]

    return name


def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  

def image_to_text(api_key, image_path):
    base64_image = encode_image(image_path)
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": """If there is nobody in the image, please type Nobody in the image.
                 If there is a person or people in the image, please follow the instructions below:
                 - Describe the people in a way you give the relevant information about their look, posture, and clothing, to make nice comments about them.
                 - Describe the background and the objects in the image in a way you give the relevant information to make nice comments about the environment.
                 - Make descriptions as detailed as possible in order to help the AI generate more accurate and relevant comments.
                 - Do not make the nice comments, just describe the people and the environment.
                 - Do not use more than 100 words because this description is going to be part of a larger prompt."""
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "details": "high"
                }
                }
            ]
            }
        ],
        "max_tokens": 300
    }
  
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    return response.json().get('choices')[0].get('message').get('content')

def get_knonw_people_names(user_id):
    known_people = []
    if os.path.exists(f'known_people/user_{user_id}'):
        for person_name in os.listdir(f'known_people/user_{user_id}'):
            if os.path.isdir(f'known_people/user_{user_id}/{person_name}'):  
                known_people.append(person_name)
    return known_people

def change_name(new_name, old_name, user_id):
    os.rename(f'known_people/user_{user_id}/{old_name}', f'known_people/user_{user_id}/{new_name}')

def return_image(user_id, name):
    with open(f'known_people/user_{user_id}/{name}/image.jpg', 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def delete_image(user_id, username):
    os.remove(f'known_people/user_{user_id}/{username}/image.jpg')
    os.rmdir(f'known_people/user_{user_id}/{username}')