# university_tools.py
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from tools.conversation import generate_response, extract_json
from tools.database_tools import database_connection
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI as LangChainOpenAI

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
    llm = LangChainOpenAI(temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )

    return qa_chain

# Inicializar RAG
qa_chain = initialize_rag()

def query_rag(query):
    return qa_chain.run(query)

def get_professor_info(params, user_id, role_id):
    try:
        professor_name = params.get('professor_name')
        course_name = params.get('course_name', '')
        if not professor_name:
            return {"error": "Se requiere el nombre del profesor."}
        
        query = f"Proporciona información sobre el profesor {professor_name}"
        if course_name:
            query += f" en relación con el curso {course_name}"
        
        result = query_rag(query)
        return {"message": result}
    except Exception as e:
        return {"error": f"Error al obtener información del profesor: {str(e)}"}

def get_course_info(params, user_id, role_id):
    try:
        course_code = params.get('course_code')
        if not course_code:
            return {"error": "Se requiere el código del curso."}
        
        query = f"Proporciona información sobre el curso con código {course_code}"
        result = query_rag(query)
        return {"message": result}
    except Exception as e:
        return {"error": f"Error al obtener información del curso: {str(e)}"}

def get_exam_schedule(params, user_id, role_id):
    try:
        course_code = params.get('course_code')
        if not course_code:
            return {"error": "Se requiere el código del curso."}
        
        query = f"¿Cuál es el horario de examen para el curso con código {course_code}?"
        result = query_rag(query)
        return {"message": result}
    except Exception as e:
        return {"error": f"Error al obtener el horario de examen: {str(e)}"}

def university_tools():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_professor_info",
                "description": "Obtener información sobre un profesor específico",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "professor_name": {
                            "type": "string",
                            "description": "El nombre del profesor"
                        },
                        "course_name": {
                            "type": "string",
                            "description": "El nombre del curso (opcional)"
                        }
                    },
                    "required": ["professor_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_course_info",
                "description": "Obtener información sobre un curso específico",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_code": {
                            "type": "string",
                            "description": "El código del curso"
                        }
                    },
                    "required": ["course_code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_exam_schedule",
                "description": "Obtener el horario de examen para un curso específico",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_code": {
                            "type": "string",
                            "description": "El código del curso"
                        }
                    },
                    "required": ["course_code"]
                }
            }
        }
    ]

    available_functions = {
        "get_professor_info": get_professor_info,
        "get_course_info": get_course_info,
        "get_exam_schedule": get_exam_schedule
    }

    return tools, available_functions