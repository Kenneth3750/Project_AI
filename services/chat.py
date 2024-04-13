#this script contains the chat class which is used to handle the conversation between the user and the bot
from tools.conversation import  generate_response, listen_to_user_tool, remove_audio_tool, speech_to_text, translate_from_whisper_api
import json



class Chat:
    def __init__(self, conversation=None):
        string_dialogue = """"You are an assistant that relies on writing and research support for a researcher. 
Your tasks involve assisting the person speaking with you in drafting writings, reading documents, providing accurate information, suggesting ideas, and always being ready to help. 
You are not limited to answering questions outside the context of research or writing, but you will only do so if the user requests it. Remember, you must always respond in the same language the user speaks."""

        self.messages = [{"role": "system", "content": string_dialogue}]
    def get_messages(self):
        return json.dumps(self.messages)
    
# def print_history(self):
#     history = self.history
#     messages = self.messages
#     print(history)
#     print(type(history))
#     print(type(messages))

def remove_audio(audio_path, output_path):
    remove_audio_tool(audio_path, output_path)

def listen_to_user(audio_file):
    remove_audio('audio.mp3', 'audio_converted.wav')
    audio = listen_to_user_tool(audio_file)
    return audio

def AI_response(client, user_input, socketio, messages):
    print("--"*20)
    # audio_text = speech_to_text(self.text_model, audio)
    # text = audio_text['text']
    text = user_input
    if text:
        messages.append({"role": "user", "content": text})
        print(f"user: {text}")
        response = generate_response(client, messages)
        print(f"AI: {response}")
        print("--"*20)
        messages.append({"role": "assistant", "content": response})
        socketio.emit('informacion_del_servidor', {'data': 'Talking...'})
        # speak_text(response)
    return response


