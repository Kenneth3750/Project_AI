from tools.vision_tools import save_image, save_current_image, upload_configurations, compare_faces, image_to_text, get_knonw_people_names, change_name, return_image, delete_image

class Vision():
    def __init__(self, user_id):
        self.known_face_encodings, self.known_face_names = upload_configurations(user_id)
        self.user_id = user_id

    def start_image_recognition(self, file, user_id):
        try:
            result = self.current_image(file, user_id)
            if result:
                name = self.get_user_name()
                return name
            else:
                return None
        except Exception as e:
            print("An error occurred: ", e)
            raise Exception("There was an error processing the image. Please try again.")

    def current_image(self, image_file, user_id):
        result = save_current_image(image_file, user_id)
        return result
    
    def get_user_name(self):
        name = compare_faces(self.known_face_encodings, self.known_face_names, self.user_id)
        return name
    
    def what_is_in_image(self, api_key, user_id):
        try:
            image_path = f'current/user_{user_id}/image.jpg'
            result = image_to_text(api_key, image_path)
            if result:
                return result
            else:
                return None
        except Exception as e:
            print("An error occurred: ", e)
            raise Exception("There was an error trying to identify what is in the image. Please try again.")
    

def manage_image(file, name, user_id):
    result = save_image(file, name, user_id)
    return result
def manage_current_image(file, user_id):
    result = save_current_image(file, user_id)
    return result
def current_image_description(api_key, user_id):
    try:
        image_path = f'current/user_{user_id}/image.jpg'
        result = image_to_text(api_key, image_path)
        return result
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error trying to identify what is in the image. Please try again.")
    
def list_known_people_names(user_id):
    try:
        result = get_knonw_people_names(user_id)
        return result
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error trying to get the list of known people. Please try again.")
    

def change_image_name(new_name, old_name, user_id):
    try:
        change_name(new_name, old_name, user_id)
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error trying to change the name of the image. Please try again.")
    
def return_user_image(user_id, name):
    try:
        encoded_image = return_image(user_id, name)
        return encoded_image
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error trying to get the image. Please try again.")
    
def delete_user_image(user_id, username):
    try:
        delete_image(user_id, username)
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error trying to delete the image. Please try again.")