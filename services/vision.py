from tools.vision_tools import save_image, send_current_image

class Vision():
    def __init__(self,):
        self.string = "hola"
        

    def manage_image(self, file, name):
        result = save_image(file, name)
        return result
    
    def current_image(self, image_file):
        result = send_current_image(image_file)
        return result
    