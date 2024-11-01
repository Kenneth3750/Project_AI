#this script contains the chat class which is used to handle the conversation between the user and the bot
from tools.conversation import  generate_response, check_conversation_length, make_resume_prompt, get_role_prompt, generate_response_with_tools
from tools.conversation import lipSync, audio_file_to_base64, read_json_transcript
from services.roles import return_role
import json
import random



class Chat:
    def __init__(self, conversation=None, client=None, resume=None, system_prompt=None, name=None, vision_prompt=None):
        self.client = client
        self.name = name
        string_dialogue = system_prompt
        self.resume = resume
        self.is_conversation = conversation
        if self.is_conversation:
            if resume:
                name_content = f"Now you are talking to {name}"
                resume_content= f"here is a resume of pasts conversations: {conversation}"
                new_vision_prompt = f"Here is the vision prompt: {vision_prompt}"
                self.conversation = [{"role": "system", "content": string_dialogue}]
                self.conversation.append({"role": "user", "content": name_content})
                self.conversation.append({"role": "user", "content": resume_content})
                self.conversation.append({"role": "user", "content": new_vision_prompt})
                self.messages = self.conversation
            else:
                name_content = f"Now you are talking to {name}"
                new_vision_prompt = f"Here is the vision prompt: {vision_prompt}"
                self.messages = json.loads(conversation)
                self.messages.insert(0, {"role": "system", "content": string_dialogue})
                self.messages.append({"role": "user", "content": name_content})
                self.messages.append({"role": "user", "content": new_vision_prompt})

        else:
            new_vision_prompt = f"Here is the vision prompt: {vision_prompt}"
            self.messages = [{"role": "system", "content": string_dialogue}]
            self.messages.append({"role": "user", "content": new_vision_prompt})
        print("--"*20)
        print("La conversación es:", self.messages)
        print("--"*20)

    def get_messages(self):
        return json.dumps(self.messages)
    


def AI_response(client, user_input, messages, tools, available_functions, role_id, user_id, language):
    try:
        print("--"*20)
        text = user_input
        if text:
            messages.append({"role": "user", "content": text})
            print(f"user: {text}")
            response, display_responses = generate_response_with_tools(client, messages, tools, available_functions, role_id, user_id, language)
            print(f"AI: {response}")
            print("--"*20)
            messages.append({"role": "assistant", "content": response})
        return response, display_responses
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error generating the response. Please try again.")



def check_current_conversation(messages, client, db, user_id, role_id):
    try:
        message_for_role = messages
        messages = json.loads(messages)
        if messages[0].get("role") == "system":
            messages.pop(0)
        messages = json.dumps(messages)
        is_to_long = check_conversation_length(messages)
        if is_to_long:
            make_resume = make_resume_prompt(messages)
            if make_resume:
                new_resume = generate_response(client, make_resume)
                db.save_conversation_historic(user_id, new_resume, role_id)
                role_prompt = get_role_prompt(message_for_role)
                new_chat = role_prompt
                new_chat.append({"role": "user", "content": f"here is a resume of pasts conversations: {new_resume}"})
                return new_chat
            else:
                return None
        else:
            return None
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error checking the conversation length. Please try again. Your next conversation can last longer than usual.")
    

def create_voice(client, user_id, text ):
    try:
        messages = json.loads(text)
        if "messages" in messages:
            messages = message["messages"]
        for i, message in enumerate(messages):
            # generate audio file
            text_input = message['text']
            animations = ["Talking_0", "Talking_2", "Crying", "Laughing", "Rumba", "Idle", "Terrified", "Angry", "standing_greeting", "raising_two_arms_talking", "put_hand_on_chin", "one_arm_up_talking", "happy_expressions"]
            #create_voice_file(client, user_id, text_input, i)
            # generate lipsync
            #lipSync(user_id, i)
            if message['animation'] not in animations:
                animations_random = ["Talking_0", "Talking_2"]
                message['animation'] = random.choice(animations_random)
    
            message['audio'] = None
            message['lipsync'] = read_json_transcript(f"audio/default.json")
        return messages
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error elaborating the response. Please try again.")
    
def add_new_vision_prompt(messages, vision_prompt, role_id, name, user_id):
    try:
        if messages[0].get("role") == "system":
            new_system_prompt = return_role(user_id, role_id, name, vision_prompt)
            messages[0]["content"] = new_system_prompt
            return messages
        else:
            return None
    except Exception as e:
        print("An error occurred: ", e)
        raise Exception("There was an error adding the new vision prompt. Please try again.")

def send_intro(language):
    if language == "es":
        text = "Hola, me llamo NAIA. Soy tu asistente virtual, ¿en qué puedo ayudarte?"
        audio = "welcome_es.mp3"
    elif language == "en":
        text = "Hello, I am is NAIA, your virtual assistant, how can I help you?"
        audio = "welcome_en.mp3"
    message = [{
        "text": text,
        "facialExpression": "default",
        "audio": audio_file_to_base64(f"audio/{audio}"),
        "lipsync": read_json_transcript("audio/default.json"),
        "animation": "Talking_1"

    }]
    return message

def send_bye(language):
    if language == "es":
        text = "Hasta luego, que tengas un buen día"
        audio = "bye_es.mp3"
    elif language == "en":
        text = "See you later, have a nice day"
        audio = "bye_en.mp3"
    message = [{
        "text": text,
        "facialExpression": "default",
        "audio": audio_file_to_base64(f"audio/{audio}"),
        "lipsync": read_json_transcript("audio/default.json"),
        "animation": "Talking_2"
    }]
    return message

