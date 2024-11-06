# university_assistant.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import OpenAI as LangChainOpenAI
from email.mime.text import MIMEText
import smtplib
from tools.database_tools import database_connection
from openai import OpenAI
import requests
import base64

# Cargar variables de entorno
load_dotenv()

PERSIST_DIRECTORY = 'tools/chroma_db'
DOCUMENTS_DIRECTORY = 'tools/documents'

# Verificar la clave API de OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_TOKEN')
client = OpenAI(api_key=OPENAI_API_KEY)

if not OPENAI_API_KEY:
    raise ValueError("No se encontró la clave API de OpenAI. Asegúrate de tener un archivo .env con OPENAI_API_KEY=tu_clave_api")

def load_documents():
    """Carga los documentos usando diferentes métodos."""
    loaders = [
        (DirectoryLoader, {"glob": "**/*.pdf", "loader_cls": UnstructuredPDFLoader}),
        (DirectoryLoader, {"glob": "**/*.pdf", "loader_cls": PyPDFLoader}),
        (DirectoryLoader, {"glob": "**/*.pdf"})  # Intenta con el loader predeterminado
    ]
    
    for loader_class, loader_args in loaders:
        try:
            print(f"Intentando cargar con {loader_class.__name__}...")
            loader = loader_class(DOCUMENTS_DIRECTORY, **loader_args)
            documents = loader.load()
            print(f"Documentos cargados exitosamente con {loader_class.__name__}")
            return documents
        except Exception as e:
            print(f"Error al cargar con {loader_class.__name__}: {str(e)}")
    
    raise Exception("No se pudo cargar los documentos con ningún método.")

def create_vectorstore():
    """Crea la base de datos vectorial si no existe."""
    if not os.path.exists(PERSIST_DIRECTORY):
        print("Creando nuevo vectorstore...")
        try:
            documents = load_documents()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(documents)
            embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            vectorstore = Chroma.from_documents(texts, embeddings, persist_directory=PERSIST_DIRECTORY)
            vectorstore.persist()
            print("Vectorstore creado y guardado.")
        except Exception as e:
            print(f"Error al crear vectorstore: {str(e)}")
            raise
    else:
        print("El vectorstore ya existe.")

def query_university_info(params, user_id, role_id):
    """Realiza una consulta en la base de datos vectorial."""
    try:
        query = params["query"]
        if not query:
            return {"error": "Se requiere una consulta."}

        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectorstore = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embeddings)
        llm = LangChainOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever()
        )
        
        result = qa_chain.invoke(query)

        question = result.get("query")
        answer = result.get("result")
        display = f"""
        <h3><b>Question</b></h3><br>
        <p>{question}</p><br>
        <h3><b>Answer</b></h3><br>
        <p>{answer}</p><br>
        """

        return {"display": display,
                "message": "The result of the embeddings is on screen. Now you must explain the answer to the user in a proper way for a voice assistant."}
    except Exception as e:
        return {"error": f"Error al buscar información: {str(e)}"}
    

def get_university_email(user_id):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    sql = "SELECT email FROM university_emails WHERE user_id = %s"
    cursor.execute(sql, (user_id))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None

    

def send_university_info_to_email(params, user_id, role_id):
    try:
        query = params["query"]
        user_name = params["name"]
        receiver_email = get_university_email(user_id)
        receiver_email_complete = f"{receiver_email}"
        if not query:
            return {"error": "Se requiere una consulta."}
        emmbedings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectorstore = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=emmbedings)
        llm = LangChainOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever()
        )
        result = qa_chain.invoke(f"Give the complete information of '{query}' formatted in a proper way to send it to an email. The name of the user that will receive the email is {user_name}.")
        answer = result.get("result")
        print(answer)
        sender = os.getenv("GMAIL_USERNAME")
        password = os.getenv("GMAIL_PASSWORD")


        recipients = [receiver_email_complete]
        msg = MIMEText(answer)
        msg['Subject'] = "University Information"
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, recipients, msg.as_string())
        return {"message": "The information has been sent to the email."}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"error": f"Error sending the email: {str(e)}"}
    
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def get_path_info(api_key, image_path, where_i_am, where_i_want_to_go):
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "system",
        "content": f"""You must only indicate the number of the locations in order to give the user the info needed to understad the map.
                Biblioteca

                1. Biblioteca Karl C. Parrish

                Bloques

                2. Bloque A
                3. Bloque Administrativo I
                4. Bloque Administrativo II
                5. Bloque B
                6. Bloque C
                7. Bloque D
                8. Bloque E
                9. Bloque F
                10. Bloque G. Edificio Postgrados
                11. Bloque I. Instituto de Idiomas
                12. Bloque J
                13. Bloque K. Edificio de Ingenierías
                14. Bloque L. Edificio Julio Muvdi
                15. Bloque M
                16. Laboratorio de Arquitectura Tropical
                17. Laboratorio de Energías Renovables
                18. Bloque de Salud  

                Escenarios Deportivos y culturales

                19. Canchas Múltiples
                20. Coliseo Cultural y Deportivo Los Fundadores (GYM is located here, inside the Coliseum)

                Parqueaderos

                21. Parqueadero administrativo principal
                22. Parqueadero Bloque C
                23. Parqueadero Bloque J
                24. Parqueadero canchas de futbol
                25. Parqueader Coliseo 
                26. Parqueadero Edificio Postgrados
                27. Parqueadero 10

                Tiendas y Restaurantes

                28. DuNord Café
                29. DuNord Express
                30. DuNord Graphique
                31. DuNord Plaza
                32. DuNord Terrasse
                33. Iwanna Store
                34. Km5
                35. Le Salon
                36. Restaurante 1966

        You must respond like this "According to the map you are now on {where_i_am} listed with the number (add the number of the location) and you want to go to {where_i_want_to_go} listed with the number (add the number of the location)."
        If the location where the user wants to go or where the user is in, is an access, you must tell the user that on the map is written the name of the access."""
    }]
    )
    return completion.choices[0].message.content



def give_location_info(params, user_id, role_id):
    try:
        where_i_want_to_go = params["where_i_want_to_go"]
        where_i_am = params["where_i_am"]
        response = get_path_info(OPENAI_API_KEY, "frontend/static/img/uni_map.png", where_i_am, where_i_want_to_go)
        image_link = f"<a href='/uni_map' target='_blank'><span style='color: blue; text-decoration: underline;'>Click here to see the University map</span></a>"

        return {"display": image_link, "message": f""" Tell the user the following information: {response}. Do not add the link of the map on your response cause it is already on screen.
                Remember to always use the number of the location in the map to give the user the information needed to understand the map. Do not add directions like go to the east, go to the west, etc. Just use the number of the location."""}
                
    except Exception as e:
        print(f"An error ocurred: {e}")
        return {"error": str(e)}


def university_assistant_tools():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "query_university_info",
                "description": "Answer any question related to college/university information. You must call this function always a person asks a question about college/university information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The question about college/university information."
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_university_info_to_email",
                "description": "Send the answer to a question or information related to university 'Universidad del Norte' to an institutional email.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The question or info the user wants to know about 'Universidad del Norte'"
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the user that you are interacting with. If you already have the name, you can use it."
                        }
                    },
                    "required": ["query", "name"]
                }
            }
        },

        {
            "type": "function",
            "function": {
                "name": "give_location_info",
                "description": "Give the user the information to get from one place to another in the university. If the user is not on the university, you must put the variable 'where_i_am' as 'acceso 07' ",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "where_i_am": {
                            "type": "string",
                            "description": "The place where the user is. This also means the place where the user is going to start."
                        },
                        "where_i_want_to_go": {
                            "type": "string",
                            "description": "The place where the user wants to go."
                        }
                    },
                    "required": ["where_i_am", "where_i_want_to_go"]
                }
            }
        }
    ]

    available_functions = {
        "query_university_info": query_university_info,
        "send_university_info_to_email": send_university_info_to_email,
        "give_location_info": give_location_info
    }

    return tools, available_functions



def update_university_email(user_id, email):
    connection = database_connection(
        {
            "user": os.getenv('user'), 
            "password": os.getenv('password'), 
            "host": os.getenv('host'), 
            "db": os.getenv('db')
        }
    )
    cursor = connection.cursor()
    sql = "SELECT email FROM university_emails WHERE user_id = %s"
    cursor.execute(sql, (user_id))
    result = cursor.fetchone()
    if not result:
        sql = "INSERT INTO university_emails (email, user_id) VALUES (%s, %s)"
        cursor.execute(sql, (email, user_id))
    else:
        sql = "UPDATE university_emails SET email = %s WHERE user_id = %s"
        cursor.execute(sql, (email, user_id))
    connection.commit()
    connection.close()