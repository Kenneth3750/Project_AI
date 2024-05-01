# Description: This file contains the Vision class which is responsible for image recognition and the management of images
from tools.vision_tools import save_image, save_current_image, upload_configurations, compare_faces

class Vision():
    def __init__(self, user_id):
        self.known_face_encodings, self.known_face_names = upload_configurations(user_id)
        self.user_id = user_id

    def start_image_recognition(self, file, user_id):
        result = self.current_image(file, user_id)
        if result:
            name = self.get_user_name()
            return name
        else:
            return None

    def current_image(self, image_file, user_id):
        result = save_current_image(image_file, user_id)
        return result
    
    def get_user_name(self):
        name = compare_faces(self.known_face_encodings, self.known_face_names, self.user_id)
        return name
    

def manage_image(file, name, user_id):
    result = save_image(file, name, user_id)
    return result