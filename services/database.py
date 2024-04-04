from tools.database_tools import database_connection, get_last_conversation, save_conversation, update_conversation



class Database:
    def __init__(self, db_data):
        self.db_data = db_data

    def connect(self):
        return database_connection(self.db_data)
    
    def init_conversation(self, user_id):
        connection = self.connect()
        conversation = get_last_conversation(connection, user_id)
        connection.close()
        if conversation:
            return conversation
        else:
            return None