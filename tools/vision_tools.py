
from PIL import Image
import os
import requests
import face_recognition
import base64 




# def save_image(file, name):
#     url = "http://127.0.0.1:15000"
#     files = {'image': file}
#     data = {'name': name}
#     response = requests.post(url, files=files, data=data)
#     if response.status_code == 200:
#         print("Image saved successfully.")
#         return True
#     else:
#         print("Failed to save image.")
#         return False


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
        "model": "gpt-4-turbo",
        "messages": [
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": "If there is a person in the image, please describe him/her. If there is no person, please type 'No person in the image. If there is a group of people, please describe the group.'"
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
                }
            ]
            }
        ],
        "max_tokens": 300
    }
  
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    return response.json().get('choices')[0].get('message').get('content')




   