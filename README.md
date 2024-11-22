*NAIA*

**Guia de instalacion**

### Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Node.js

### Instalación

1. Clona el repositorio:
    ```bash
    git clone https://github.com/Kenneth3750/Project_AI.git
    ```
2. Navega al directorio del proyecto:
    ```bash
    cd Project_AI
    ```
3. Crea un entorno virtual:
    ```bash
    python -m venv venv
    ```
4. Activa el entorno virtual:
    - En Windows:
        ```bash
        venv\Scripts\activate
        ```
    - En macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
5. Instala las dependencias de Python:
    ```bash
    pip install -r requirements.txt
    ```
6. Navega al directorio `frontend`:
    ```bash
    cd frontend
    ```
7. Instala las dependencias de Node.js:
    ```bash
    npm install
    ```
8. Compila el proyecto:
    ```bash
    npm run build
    ```

# Configuración del Archivo `.env`

Este proyecto utiliza un archivo `.env` para gestionar las variables de entorno necesarias para su funcionamiento. Estas variables contienen información confidencial como claves API, credenciales de bases de datos y configuraciones específicas. **Asegúrate de mantener este archivo privado y nunca compartirlo públicamente.**

## Pasos para Configurar el Archivo `.env`

1. Crea un archivo llamado `.env` en la raíz del proyecto.
2. Copia y pega las siguientes líneas en el archivo `.env` y completa los valores según corresponda:


# OpenAI API Key para interactuar con los modelos de IA.
OPENAI_API_TOKEN=tu_api_token_de_openai
https://openai.com/

# API Key para servicios de búsqueda web.
SEARCH_WEB_API_KEY=tu_api_key_de_SerpAPI
https://serpapi.com/

# Credenciales del cliente de Google para autenticación OAuth2.
GOOGLE_CLIENT_ID=tu_client_id_de_google
GOOGLE_CLIENT_SECRET=tu_client_secret_de_google
https://cloud.google.com/?hl=es_419

# Configuración de conexión a la base de datos MySQL.
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=tu_contraseña_de_mysql
DB_NAME=prueba_ai

# Token y ID del teléfono para integraciones con WhatsApp Business.
WHATSAPP_TOKEN=tu_token_de_whatsapp
PHONE_ID=tu_id_del_teléfono_de_whatsapp
https://developers.facebook.com/

# Credenciales de Gmail para el envío de correos electrónicos del guia universitario.
GMAIL_USERNAME=tu_correo_gmail
GMAIL_PASSWORD=tu_contraseña_de_aplicación_gmail

# Iniciar base de datos

Este módulo proporciona funcionalidad para gestionar y manipular oraciones en la base de datos.

Para iniciar y crear las tablas de la base de datos, simplemente puedes entrar a MySQL desde la raíz del proyecto y ejecutar el siguiente comando:
```sql
source sentences.sql
```



### Configuración de Redis

Este proyecto utiliza Redis para la gestión de caché y cola de tareas. A continuación, se detallan los pasos para instalar y poner en funcionamiento Redis.

## Instalación de Redis

1. **En Windows:**
    - Descarga Redis desde [este enlace](https://github.com/microsoftarchive/redis/releases).
    - Extrae el contenido del archivo descargado.
    - Ejecuta `redis-server.exe` para iniciar el servidor Redis.

2. **En macOS:**
    - Utiliza Homebrew para instalar Redis:
        ```bash
        brew install redis
        ```
    - Inicia el servidor Redis:
        ```bash
        brew services start redis
        ```

3. **En Linux:**
    - Utiliza el gestor de paquetes de tu distribución para instalar Redis. Por ejemplo, en Ubuntu:
        ```bash
        sudo apt update
        sudo apt install redis-server
        ```
    - Inicia el servidor Redis:
        ```bash
        sudo systemctl start redis
        ```

## Verificación de Redis

Para verificar que Redis está funcionando correctamente, ejecuta el siguiente comando:
```bash
redis-cli ping
```
Deberías recibir una respuesta `PONG`.

### Configuración de Certificados SSL

Para asegurar las comunicaciones, este proyecto utiliza certificados SSL. Puedes generar tus propios certificados utilizando OpenSSL o utilizar certificados válidos si ya los tienes.

## Generación de Certificados SSL con OpenSSL

1. Abre una terminal y navega al directorio raíz del proyecto.
2. Ejecuta los siguientes comandos para generar un certificado y una clave privada:

    ```bash
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem
    ```

3. Completa la información solicitada durante la generación del certificado.

Si ya tienes certificados válidos, simplemente colócalos en la raíz del proyecto con los nombres `cert.pem` y `key.pem`.



## Configuración de Eleven Labs API

Este proyecto también utiliza la API de Eleven Labs. Para configurar la clave de API, sigue estos pasos:

1. Crea un archivo llamado `config.js` en la raíz del proyecto.
2. Copia y pega la siguiente línea en el archivo `config.js` y completa el valor de la clave API:

    ```javascript
    export const ELEVEN_LABS_API_KEY = 'tu_api_key_de_eleven_labs';
    ```

3. Navega al directorio `frontend`:
    ```bash
    cd frontend
    ```

4. Compila el proyecto nuevamente:
    ```bash
    npm run build
    ```

## Configuración de Correos Electrónicos Autorizados

Para restringir el acceso a la aplicación a ciertos correos electrónicos, sigue estos pasos:

1. Crea un archivo llamado `config.py` en la raíz del proyecto.
2. Copia y pega el siguiente código en el archivo `config.py`:

    ```python
    authorized_emails = [
        "example1@gmail.com",
        "example2@gmail.com"
    ]
    ```

3. Asegúrate de que el archivo `config.py` sea importado y utilizado en tu aplicación para verificar los correos electrónicos autorizados.


## Extracción de Archivos ZIP

Este proyecto incluye un archivo ZIP llamado `audio.zip` que contiene archivos de audio necesarios para su funcionamiento. A continuación, se detallan los pasos para extraer este archivo.

1. Asegúrate de que el archivo `audio.zip` se encuentra en la raíz del proyecto.
2. Extrae el contenido del archivo ZIP utilizando el siguiente comando:

    ```bash
    unzip audio.zip -d audio
    ```

    Esto creará un directorio llamado `audio` y extraerá todos los archivos dentro de él.

3. Verifica que los archivos de audio se hayan extraído correctamente en el directorio `audio`.


# Configuración de `credentials.json` para Envío de Correos

Este proyecto utiliza un archivo `credentials.json` proporcionado por Google Cloud Platform (GCP) para autenticar el envío de correos electrónicos a través de sus servicios. Sigue los pasos a continuación para configurar este archivo.

## Pasos para Obtener el Archivo `credentials.json`

1. **Accede a la Consola de GCP**: Ve a [Google Cloud Console](https://console.cloud.google.com/).

2. **Crea un Proyecto** (si no tienes uno): 
   - Haz clic en "Seleccionar proyecto" en la barra superior y luego en "Nuevo proyecto".
   - Asigna un nombre al proyecto y haz clic en "Crear".

3. **Habilita la API de Gmail**:
   - Ve al apartado "APIs y servicios" en el menú de navegación.
   - Haz clic en "Habilitar APIs y servicios".
   - Busca "Gmail API" y haz clic en "Habilitar".

4. **Configura una Credencial OAuth 2.0**:
   - Dirígete a "Credenciales" en el menú de "APIs y servicios".
   - Haz clic en "Crear credenciales" y selecciona "ID de cliente de OAuth".
   - Completa los pasos para configurar la pantalla de consentimiento de OAuth (si aún no lo has hecho).
   - Selecciona "Aplicación de escritorio" como tipo de aplicación y haz clic en "Crear".
   - Descarga el archivo `credentials.json` que se genera.

5. **Coloca el Archivo en el Proyecto**:
   - Guarda el archivo `credentials.json` en la raíz del proyecto.



### Uso

1. Ejecuta el script principal:
    ```bash
    python app.py
    ```


