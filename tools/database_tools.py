import pymysql
from datetime import datetime
from tools.conversation import count_tokens

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
        print(f"Error: {e}")
        return None
    


def get_last_conversation_resume(connection, user_id):
    try: 
        cursor = connection.cursor()
        sql = "select created_at, user_resume from user_conversation_history where user_id = (%s) order by id desc limit 1"
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        if result:
            sql = "select created_at, conversations from user_conversations where user_id = (%s) order by id desc limit 1"
            cursor.execute(sql, (user_id,))
            result_complete = cursor.fetchone()
            conversation = None
            resume = None
            tokens = count_tokens(result_complete[1])
            if result_complete:
                historic_date = result[0]
                complete_date = result_complete[0]
                if historic_date > complete_date:
                    resume = True
                    conversation = result[1]
                elif historic_date == complete_date:
                    if tokens > 1000:
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
            sql = "select conversations from user_conversations where user_id = (%s) order by id desc limit 1"
            cursor.execute(sql, (user_id,))
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

    
def save_conversation(connection, user_id, conversation):
    try: 
        cursor = connection.cursor()
        sql = "select conversations, created_at from user_conversations where user_id = (%s) order by id desc limit 1"
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        current_date = datetime.now().date()
        if result:
            if result[0] == current_date:
                tokens = count_tokens(conversation)
                if tokens > 1000:
                    sql = "INSERT INTO user_conversations (user_id, conversations, created_at) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (user_id, conversation, datetime.now().date()))
                    connection.commit()
                    return True
                else:
                    update_conversation(connection, user_id, conversation)
                    return True
            else:
                sql = "INSERT INTO user_conversations (user_id, conversations, created_at) VALUES (%s, %s, %s)"
                cursor.execute(sql, (user_id, conversation, datetime.now().date()))
                connection.commit()
                return True
        else:
            sql = "INSERT INTO user_conversations (user_id, conversations, created_at) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, conversation, datetime.now().date()))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    
def save_conversation_history(connection, user_id, conversation):
    try:
        cursor = connection.cursor()
        sql = "select created_at from user_conversation_history where user_id = (%s) order by id desc limit 1"
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        current_date = datetime.now().date()
        if result:
            if result[0] == current_date:
                upddate_conversation_history(connection, user_id, conversation)
                return True
            else:
                sql = "INSERT INTO user_conversation_history (user_id, user_resume, created_at) VALUES (%s, %s, %s)"
                cursor.execute(sql, (user_id, conversation, datetime.now().date()))
                connection.commit()
                return True
        else:
            sql = "INSERT INTO user_conversation_history (user_id, user_resume, created_at) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, conversation, datetime.now().date()))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def update_conversation(connection, user_id, conversation):
    try:
        cursor = connection.cursor()
        sql = "UPDATE user_conversations SET conversations = %s WHERE user_id = %s"
        cursor.execute(sql, (conversation, user_id))
        connection.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    

def upddate_conversation_history(connection, user_id, conversation):
    try:
        cursor = connection.cursor()
        sql = "UPDATE user_conversation_history SET user_resume = %s WHERE user_id = %s"
        cursor.execute(sql, (conversation, user_id))
        connection.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False 

    

    
