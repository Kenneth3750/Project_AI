from PIL import Image
import os
import requests
from PIL import Image
import os
import requests



def save_image(file, name):
    url = "http://127.0.0.1:15000"
    files = {'image': file}
    data = {'name': name}
    response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        print("Image saved successfully.")
        return True
    else:
        print("Failed to save image.")
        return False
    
def send_current_image(image_file):
    if image_file.filename != '':
        image_file.seek(0)
        files = {'image': image_file}
        response = requests.post('http://127.0.0.1:15000/current', files=files)
        if response.status_code == 200:
            print("Imagen enviada correctamente")
            return True
        else:
            print("Error al enviar la imagen")
            return False


   