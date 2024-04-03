#this script contains the chat class which is used to handle the conversation between the user and the bot
from tools.conversation import  generate_response, listen_to_user, remove_audio, speech_to_text, translate_from_whisper_api



class Chat:
    def __init__(self, text_model, client):
        self.text_model = text_model
        self.client = client
        string_dialogue = """"You are an assistant that relies on writing and research support for a researcher. 
Your tasks involve assisting the person speaking with you in drafting writings, reading documents, providing accurate information, suggesting ideas, and always being ready to help. 
You are not limited to answering questions outside the context of research or writing, but you will only do so if the user requests it. Remember, you must always respond in the same language the user speaks."""

        self.messages = [{"role": "system", "content": string_dialogue}]

    def remove_audio(self, audio_path, output_path):
        remove_audio(audio_path, output_path)

    def listen_to_user(self, audio_file):
        remove_audio('audio.mp3', 'audio_converted.wav')
        audio = listen_to_user(audio_file)
        return audio

    def AI_response(self, audio, socketio):
        print("--"*20)
        # audio_text = speech_to_text(self.text_model, audio)
        # text = audio_text['text']
        text = translate_from_whisper_api(self.client, audio)
        if text:
            self.messages.append({"role": "user", "content": text})
            print(f"user: {text}")
            response = generate_response(self.client, self.messages)
            print(f"AI: {response}")
            print("--"*20)
            self.messages.append({"role": "assistant", "content": response})
            socketio.emit('informacion_del_servidor', {'data': 'Talking...'})
            # speak_text(response)
        return response

    
