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
    
def get_last_conversation(connection, user_id):
    cursor = connection.cursor()
    sql = "SELECT conversations FROM user_conversations WHERE user_id = (%s) ORDER BY id DESC LIMIT 1"
    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()
    if result:
        conversation = result[0]
        return conversation
    else:
        return None
    
def save_conversation(connection, user_id, conversation):
    cursor = connection.cursor()
    sql = "INSERT INTO user_conversations (user_id, conversations) VALUES (%s, %s)"
    cursor.execute(sql, (user_id, conversation))
    connection.commit()
    return True

def update_conversation(connection, user_id, conversation):
    cursor = connection.cursor()
    sql = "UPDATE user_conversations SET conversations = %s WHERE user_id = %s"
    cursor.execute(sql, (conversation, user_id))
    connection.commit()
    return True

    
