#this script contains the chat class which is used to handle the conversation between the user and the bot
from tools.conversation import speak_text, generate_response, listen_to_user, remove_audio
from mistralai.models.chat_completion import ChatMessage 



class Chat:
    def __init__(self, tiny_model, client):
        self.tiny_model = tiny_model
        self.client = client
        string_dialogue = """ You are a hotel receptionist, and your duties include:
        Welcoming guests
        Handling guest check-in and check-out
        Providing hotel information: such as buffet menus for breakfast, lunch, or dinner, informing about the availability of hotel facilities like the pool, gym, etc.
        If someone requests to book a room, you should refer them to the person in charge of managing payments. However, if the person already has a reservation, you should assist them with check-in or check-out, so you must ask them accordingly.
        If the user asks about something unrelated to the hotel, politely inform them that you cannot assist with that.
        Do not overcomplicate your responses. Keep them simple and to the point."""
        self.messages = [ChatMessage(role="system", content=f"{string_dialogue}")]

    def remove_audio(self, audio_path, output_path):
        remove_audio(audio_path, output_path)

    def listen_to_user(self, request):
        audio = listen_to_user(request)
        return audio

    def AI_response(self, audio, socketio):
        print("--"*20)
        audio_text = self.tiny_model.transcribe(audio)
        text = audio_text['text']
        if text:
            self.messages.append(ChatMessage(role="user", content=text))
            print(f"user: {text}")
            response = generate_response(self.client, self.messages)
            print(f"AI: {response}")
            print("--"*20)
            self.messages.append(ChatMessage(role="assistant", content=response))
            socketio.emit('informacion_del_servidor', {'data': 'Talking...'})
            speak_text(response)
        return response

    
