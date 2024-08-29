import pymysql
from datetime import datetime
from tools.conversation import count_tokens, max_tokens

def database_connection(db_data):
    try:
        connection = pymysql.connect(
            host=db_data['host'],
            user=db_data['user'],
            password=db_data['password'],
            db=db_data['db'],

        )

        return connection
    except Exception as e:
        print(f"Error en conectar a la db: {e}")
        return None
    


def get_last_conversation_resume(connection, user_id, role_id):
    try: 
        cursor = connection.cursor()
        sql = "select created_at, user_resume from user_conversation_history where user_id = (%s) and role_id = (%s)  order by id desc limit 1"
        cursor.execute(sql, (user_id, role_id))
        result = cursor.fetchone()
        if result:
            sql = "select created_at, conversations from user_conversations where user_id = (%s) and role_id = (%s) order by id desc limit 1"
            cursor.execute(sql, (user_id, role_id))
            result_complete = cursor.fetchone()
            conversation = None
            resume = None
            tokens = count_tokens(result_complete[1])
            print(f"Tokens de la db, conversacion completa: {tokens}")
            if result_complete:
                historic_date = result[0]
                complete_date = result_complete[0]
                if historic_date > complete_date:
                    resume = True
                    conversation = result[1]
                elif historic_date == complete_date:
                    if tokens > max_tokens:
                        resume = True
                        conversation = result[1]
                    else:
                        conversation = result_complete[1]
                        resume = False
                else:
                    conversation = result_complete[1] 
                    resume = False
            return conversation, resume
        else:
            sql = "select conversations from user_conversations where user_id = (%s) and role_id = (%s) order by id desc limit 1"
            cursor.execute(sql, (user_id, role_id))
            result = cursor.fetchone()
            if result:
                resume = False
                return result[0], resume
            else:
                conversation = None
                resume = None
                return conversation, resume
            
    except Exception as e:
        print(f"Error: {e}")
        return None


def save_conversation(connection, user_id, conversation, role_id):
    try: 
        cursor = connection.cursor()
        sql = "select conversations, created_at from user_conversations where user_id = (%s) and role_id = (%s) order by id desc limit 1"
        cursor.execute(sql, (user_id, role_id))
        result = cursor.fetchone()
        current_date = datetime.now().date()
        if result:
            if result[1] == current_date:
                tokens = count_tokens(result[0])
                if tokens > max_tokens:
                    sql = "INSERT INTO user_conversations (user_id, conversations, created_at, role_id) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (user_id, conversation, datetime.now().date(), role_id))
                    connection.commit()
                    return True
                else:
                    update_conversation(connection, user_id, conversation, role_id)
                    return True
            else:
                sql = "INSERT INTO user_conversations (user_id, conversations, created_at, role_id) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (user_id, conversation, datetime.now().date(), role_id))
                connection.commit()
                return True
        else:
            sql = "INSERT INTO user_conversations (user_id, conversations, created_at, role_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, conversation, datetime.now().date(), role_id))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error: {e}")
        raise Exception("There was an error saving the conversation. Please try again.")

def save_conversation_history(connection, user_id, conversation, role_id):
    try:
        cursor = connection.cursor()
        sql = "select created_at from user_conversation_history where user_id = (%s) and role_id = (%s) order by id desc limit 1"
        cursor.execute(sql, (user_id, role_id))
        result = cursor.fetchone()
        current_date = datetime.now().date()
        if result:
            if result[0] == current_date:
                upddate_conversation_history(connection, user_id, conversation, role_id)
                return True
            else:
                sql = "INSERT INTO user_conversation_history (user_id, user_resume, created_at, role_id) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (user_id, conversation, datetime.now().date(), role_id))
                connection.commit()
                return True
        else:
            sql = "INSERT INTO user_conversation_history (user_id, user_resume, created_at, role_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, conversation, datetime.now().date(), role_id))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def update_conversation(connection, user_id, conversation, role_id):
    try:
        cursor = connection.cursor()
        sql = "UPDATE user_conversations SET conversations = %s WHERE user_id = %s and created_at = %s and role_id = %s order by id desc limit 1"
        cursor.execute(sql, (conversation, user_id, datetime.now().date(), role_id))
        connection.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def upddate_conversation_history(connection, user_id, conversation, role_id):
    try:
        cursor = connection.cursor()
        sql = "UPDATE user_conversation_history SET user_resume = %s WHERE user_id = %s and created_at = %s and role_id = %s"
        cursor.execute(sql, (conversation, user_id, datetime.now().date(), role_id))
        connection.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

    

    
def is_valid_user(connection, username, password):
    try:
        cursor = connection.cursor()
        sql = "select id from users where user_name = (%s) and user_password = (%s)"
        cursor.execute(sql, (username, password))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    

def check_user(connection, user_info):
    try:
        user_email = user_info.get("email")
        cursor = connection.cursor()
        sql = "select id from users where user_email = (%s)"
        cursor.execute(sql, (user_email))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return False
    except Exception as e:
        print(f"Error: {e}")
        raise Exception("There was an error checking the user. Please try again.")
    
def create_user(connection, user_info):
    try:
        cursor = connection.cursor()
        sql = "INSERT INTO users (user_email, user_full_name, user_name, photo_url) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (user_info.get("email"), user_info.get("name"), user_info.get("given_name"), user_info.get("picture")))
        connection.commit()
        sql = "select id from users where user_email = (%s)"
        cursor.execute(sql, (user_info.get("email")))
        result = cursor.fetchone()
        user_id = result[0]
        return user_id
    except Exception as e:
        print(f"Error: {e}")
        raise Exception("There was an error creating the user. Please try again.")
    
def get_user(connection, user_id):
    try:
        cursor = connection.cursor()
        sql = "select user_full_name, photo_url, user_name from users where id = (%s)"
        cursor.execute(sql, (user_id))
        result = cursor.fetchone()
        print(f"Resultado de la db: {result}")
        if result:
            return result[0], result[1], result[2]
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        raise Exception("There was an error getting the user information. Please try again.")