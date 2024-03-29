#this script contains the chat class which is used to handle the conversation between the user and the bot
from tools.conversation import speak_text, generate_response, listen_to_user


class Chat:
    def __init__(self, tiny_model):
        self.tiny_model = tiny_model
    
    def listen_to_user(self):
        audio = listen_to_user()
        return audio

    def AI_response(self, filename, socketio):
        string_dialogue = """ You are a hotel receptionist, and your duties include:
        Welcoming guests
        Handling guest check-in and check-out
        Providing hotel information: such as buffet menus for breakfast, lunch, or dinner, informing about the availability of hotel facilities like the pool, gym, etc.
        If someone requests to book a room, you should refer them to the person in charge of managing payments. However, if the person already has a reservation, you should assist them with check-in or check-out, so you must ask them accordingly.
        If the user asks about something unrelated to the hotel, politely inform them that you cannot assist with that.
        Do not overcomplicate your responses. Keep them simple and to the point.
        You should respond in the same language as the user's input.
    
        User:   """
        audio_text = self.tiny_model.transcribe(filename)
        text = audio_text['text']
        if text:
            print(f"User: {text}")
            response = generate_response(text, string_dialogue)
            message = ''.join(response)
            full_respone = ''
            #for item in response:
                #full_respone += item
            print(f"AI: {message}")
            socketio.emit('informacion_del_servidor', {'data': 'Talking...'})
            speak_text(message)
        
    
