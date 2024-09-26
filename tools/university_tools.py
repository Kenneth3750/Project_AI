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

# Cargar variables de entorno
load_dotenv()

PERSIST_DIRECTORY = 'tools/chroma_db'
DOCUMENTS_DIRECTORY = 'tools/documents'

# Verificar la clave API de OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_TOKEN')
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
        user_name = params["user_name"]
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


def university_assistant_tools():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "query_university_info",
                "description": "Answer any question related to college/university information.",
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
        }
    ]

    available_functions = {
        "query_university_info": query_university_info,
        "send_university_info_to_email": send_university_info_to_email
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