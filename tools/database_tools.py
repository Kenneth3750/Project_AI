import pymysql


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
            result_2 = cursor.fetchone()
            conversation = None
            if result_2:
                historic_date = result_2[0]
                complete_date = result[0]
                if historic_date >= complete_date:
                    conversation = result_2[1]
                else:
                    conversation = result[1] 
            return conversation
        else:
            sql = "select conversations from user_conversations where user_id = (%s) order by id desc limit 1"
            cursor.execute(sql, (user_id,))
            result_2 = cursor.fetchone()
            if result_2:
                return result_2[0]
            else:
                return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

    
def save_conversation(connection, user_id, conversation):
    try: 
        cursor = connection.cursor()
        sql = "INSERT INTO user_conversations (user_id, conversations) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, conversation))
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
    
