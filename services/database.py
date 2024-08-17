from tools.database_tools import database_connection,  save_conversation, get_last_conversation_resume, save_conversation_history, is_valid_user, check_user, create_user, get_user
from tools.conversation import generate_response,  make_resume_prompt
import json
class Database:
    def __init__(self, db_data):
        self.db_data = db_data

    def connect(self):
        return database_connection(self.db_data)
    
    def init_conversation(self, user_id, client, role_id):
        try:
            connection = self.connect()
            conversation, is_resume = get_last_conversation_resume(connection, user_id, role_id)
            print("La conversación es de la db:", conversation)
            connection.close()
            if conversation:
                if is_resume:
                    resume = True
                    return conversation, resume
                else:
                    need_a_resume = make_resume_prompt(conversation)
                    if need_a_resume:
                        chat_resume = generate_response(client, need_a_resume)
                        self.save_conversation_historic(user_id, chat_resume, role_id)
                        return chat_resume, True
                    else:
                        return conversation, False
            else:
                return None, None
        except Exception as e:
            print("An error occurred: ", e)
            raise Exception("There was an error initializing the conversation. Please try again.")
        
    def save_current_conversation(self, user_id, conversation, role_id):
        connection = self.connect()
        conversation = json.loads(conversation)
        if conversation[0].get("role") == "system":
            conversation.pop(0)
        conversation = json.dumps(conversation)
        save_conversation(connection, user_id, conversation, role_id)
        connection.close()

    
    def save_conversation_historic(self, user_id, conversation, role_id):
        connection = self.connect()
        save_conversation_history(connection, user_id, conversation, role_id)
        connection.close()

    def check_user(self, user_name, password):
        connection = self.connect()
        user_id = is_valid_user(connection, user_name, password)
        connection.close()
        return user_id
    
    def check_and_create_user(self, user_info):
        connection = self.connect()
        user_id = check_user(connection, user_info)
        if not user_id:
            user_id = create_user(connection, user_info)
        connection.close()
        return user_id
    
    def get_user_info(self, user_id):
        connection = self.connect()
        full_name, image_url, name = get_user(connection, user_id)
        connection.close()
        return full_name, image_url, name

