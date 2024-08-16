# university_tools.py
from dotenv import load_dotenv
from openai import OpenAI
import os
from tools.conversation import generate_response, extract_json
from tools.database_tools import database_connection
import json
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_TOKEN'))

# Inicializar el sistema RAG
def initialize_rag():
    # Cargar documentos
    loader = DirectoryLoader('documents', glob="**/*.pdf")
    documents = loader.load()

    # Dividir documentos en chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    # Crear embeddings y almacenar en Chroma
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(texts, embeddings)

    # Crear cadena de recuperación
    qa_chain = RetrievalQA.from_chain_type(
        llm=OpenAI(),
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )

    return qa_chain

qa_chain = initialize_rag()

def query_rag(query):
    return qa_chain.run(query)

def get_course_info(params, user_id, role_id):
    try:
        course_code = params.get('course_code')
        query = f"Provide information about the course with code {course_code}"
        result = query_rag(query)
        return {"message": result}
    except Exception as e:
        return {"error": str(e)}

def get_professor_info(params, user_id, role_id):
    try:
        professor_name = params.get('professor_name')
        query = f"Provide information about professor {professor_name}"
        result = query_rag(query)
        return {"message": result}
    except Exception as e:
        return {"error": str(e)}

def get_exam_schedule(params, user_id, role_id):
    try:
        course_code = params.get('course_code')
        query = f"What is the exam schedule for the course with code {course_code}?"
        result = query_rag(query)
        return {"message": result}
    except Exception as e:
        return {"error": str(e)}

def university_tools():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_course_info",
                "description": "Get information about a specific course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_code": {
                            "type": "string",
                            "description": "The code of the course"
                        }
                    },
                    "required": ["course_code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_professor_info",
                "description": "Get information about a specific professor",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "professor_name": {
                            "type": "string",
                            "description": "The name of the professor"
                        }
                    },
                    "required": ["professor_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_exam_schedule",
                "description": "Get the exam schedule for a specific course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_code": {
                            "type": "string",
                            "description": "The code of the course"
                        }
                    },
                    "required": ["course_code"]
                }
            }
        }
    ]

    available_functions = {
        "get_course_info": get_course_info,
        "get_professor_info": get_professor_info,
        "get_exam_schedule": get_exam_schedule
    }

    return tools, available_functions