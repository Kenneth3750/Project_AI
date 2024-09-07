# university_assistant.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import OpenAI as LangChainOpenAI
from openai import OpenAI


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
        query = params.get('query')
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
        
        result = qa_chain.run(query)
        return {"display": result}
    except Exception as e:
        return {"error": f"Error al buscar información: {str(e)}"}

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
        }
    ]

    available_functions = {
        "query_university_info": query_university_info
    }

    return tools, available_functions

# Crear el vectorstore al iniciar (esto puede moverse a un script separado si es necesario)
create_vectorstore()