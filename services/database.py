from tools.database_tools import database_connection,  save_conversation, update_conversation, get_last_conversation_resume



class Database:
    def __init__(self, db_data):
        self.db_data = db_data

    def connect(self):
        return database_connection(self.db_data)
    
    def init_conversation(self, user_id):
        connection = self.connect()
        conversation = get_last_conversation_resume(connection, user_id)
        connection.close()
        if conversation:
            return conversation
        else:
            return None