#this script contains the chat class which is used to handle the conversation between the user and the bot
from tools.conversation import  generate_response, listen_to_user_tool, remove_audio_tool, check_conversation_length, make_resume_prompt, get_role_prompt

import json



class Chat:
    def __init__(self, conversation=None, client=None, resume=None, system_prompt=None, name=None):
        self.client = client
        self.name = name
        string_dialogue = system_prompt
        self.resume = resume
        self.is_conversation = conversation
        if self.is_conversation:
            if resume:
                name_content = f"My name is {name}"
                resume_content= f"here is a resume of pasts conversations: {conversation}"
                self.conversation = [{"role": "system", "content": string_dialogue}]
                self.conversation.append({"role": "user", "content": name_content})
                self.conversation.append({"role": "user", "content": resume_content})
                self.messages = self.conversation
            else:
                name_content = f"My name is {name}"
                self.messages = json.loads(conversation)
                self.messages.insert(0, {"role": "system", "content": string_dialogue})
                self.messages.append({"role": "user", "content": name_content})

        else:
            self.messages = [{"role": "system", "content": string_dialogue}]
        print("--"*20)
        print("La conversación es:", self.messages)
        print("--"*20)

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

def AI_response(client, user_input, messages):
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
        # speak_text(response)
    return response

def check_current_conversation(messages, client, db, user_id, role_id):
    is_to_long = check_conversation_length(messages)
    if is_to_long:
        make_resume = make_resume_prompt(messages)
        new_resume = generate_response(client, make_resume)
        db.save_conversation_historic(user_id, new_resume, role_id)
        role_prompt = get_role_prompt(messages)
        new_chat = role_prompt
        new_chat.append({"role": "user", "content": f"here is a resume of pasts conversations: {new_resume}"})
        return new_chat
    else:
        return None

