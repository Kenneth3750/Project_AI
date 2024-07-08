#this script contains the chat class which is used to handle the conversation between the user and the bot
from tools.conversation import  generate_response, check_conversation_length, make_resume_prompt, get_role_prompt, generate_response_with_tools
from tools.conversation import lipSync, audio_file_to_base64, read_json_transcript
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
                name_content = f"Now you are talking to {name}"
                resume_content= f"here is a resume of pasts conversations: {conversation}"
                self.conversation = [{"role": "system", "content": string_dialogue}]
                self.conversation.append({"role": "user", "content": name_content})
                self.conversation.append({"role": "user", "content": resume_content})
                self.messages = self.conversation
            else:
                name_content = f"Now you are talking to {name}"
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
    


def AI_response(client, user_input, messages, tools, available_functions):
    print("--"*20)
    text = user_input
    if text:
        messages.append({"role": "user", "content": text})
        print(f"user: {text}")
        response = generate_response_with_tools(client, messages, tools, available_functions)
        print(f"AI: {response}")
        print("--"*20)
        messages.append({"role": "assistant", "content": response})
    return response



def check_current_conversation(messages, client, db, user_id, role_id):
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
    

def create_voice(client, user_id, text ):
    messages = json.loads(text)
    if "messages" in messages:
        messages = message["messages"]
    for i, message in enumerate(messages):
        # generate audio file
        text_input = message['text']
        #create_voice_file(client, user_id, text_input, i)
        # generate lipsync
        #lipSync(user_id, i)
        if message['animation'] == "smile":
            message["animation"] = "Talking_1"
  
        message['audio'] = None
        message['lipsync'] = read_json_transcript(f"audio/default.json")
    return messages

def send_intro():
    message = [{
        "text": "Bienvenido. Me llamo Naia, tu asistente virtual. ¿con qué puedo ayudarte hoy?",
        "facialExpression": "default",
        "audio": audio_file_to_base64("audio/intro2.wav"),
        "lipsync": read_json_transcript("audio/intro2.json"),
        "animation": "Talking_1"

    }]
    return message

def send_bye():
    message = [{
        "text": "Hasta luego, un placer haber hablado contigo, nos vemos pronto.",
        "facialExpression": "default",
        "audio": audio_file_to_base64("audio/Bye.wav"),
        "lipsync": read_json_transcript("audio/Bye.json"),
        "animation": "Talking_2"
    }]
    return message

