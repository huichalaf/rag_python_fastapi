from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from main import *
import os
import uvicorn
import os
import json
import base64
import asyncio
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from functions import auth_user, imagen_a_bytesio, get_type_user, update_credentials, get_user_data, create_user, update_type_user, change_filename, get_user
from cost_manager import add_daily_query_usage, get_daily_query_usage, get_monthly_whisper_usage, calculate_tokens, get_monthly_embeddings_usage
from function_callin import chat
import document_generator as qg

origins = ["http://localhost:5173", "http://localhost:4173"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
files_path = os.getenv("FILES_PATH")
monthly_basic_limit = os.getenv("MONTHLY_EMBEDDINGS_BASIC_LIMIT")
monthly_pro_limit = os.getenv("MONTHLY_EMBEDDINGS_PRO_LIMIT")
monthly_free_limit = os.getenv("MONTHLY_EMBEDDINGS_FREE_LIMIT")
monthly_basic_limit = int(monthly_basic_limit)
monthly_pro_limit = int(monthly_pro_limit)
monthly_free_limit = int(monthly_free_limit)
basic_limit = os.getenv("DAILY_QUERYS_BASIC_LIMIT")
pro_limit = os.getenv("DAILY_QUERYS_PRO_LIMIT")
free_limit = os.getenv("DAILY_QUERYS_FREE_LIMIT")
basic_limit = int(basic_limit)
pro_limit = int(pro_limit)
free_limit = int(free_limit)
whisper_pro_limit = os.getenv("MONTHLY_AUDIO_PRO_LIMIT")
whisper_basic_limit = os.getenv("MONTHLY_AUDIO_BASIC_LIMIT")
whisper_free_limit = os.getenv("MONTHLY_AUDIO_FREE_LIMIT")
whisper_pro_limit = int(whisper_pro_limit)
whisper_basic_limit = int(whisper_basic_limit)
whisper_free_limit = int(whisper_free_limit)
context_selected_path = os.getenv("CONTEXT_SELECTED_PATH")
autentication_token = os.getenv("AUTENTICATION_TOKEN")

class Message(BaseModel):
    user: str
    token: str
    type_user: str
    text: str
    temperature: int
    max_tokens: int

class UserData(BaseModel):
    user: str

@app.get("/")
async def read_root(request: Request):
    client_ip = request.client.host
    print(f"Access from IP address: {client_ip}")
    return {"Status": "Running"}

@app.post("/load_context")
async def save_context(request: Request):  # Agregar el parámetro Request
    global files_path
    data = await request.json()  # Usar await para obtener los datos del body de la solicitud
    try:
        user = data['user']
    except:
        return {"result": False, "message": "Invalid parameters"}
    user = await get_user(user)

    files_prev = os.listdir(f"{files_path}subject/pending")
    files = []
    for i in files_prev:
        if user in i:
            files.append(i)
    files_pdf = [i for i in files if i.split(".")[-1] == "pdf"]
    files_txt = [i for i in files if i.split(".")[-1] == "txt"]
    files_audio = [i for i in files if i.split(".")[-1] == "mp3" or i.split(".")[-1] == "wav"]
    try:
        if len(files_pdf) > 0:
            for i in files_pdf:
                text = await read_one_pdf(f"{files_path}subject/pending/"+i)
                if text:
                    response_save = await save_document(user, i)
                    try:
                        if not response_save:
                            return {"result": False}
                    except:
                        pass
    except Exception as e:
        print("\033[91merror en pdf: \033[0m",e)
        return {"result": False}
    try:
        if len(files_audio) > 0:
            for i in files_audio:
                text = await transcribe_audio(user, f"{files_path}subject/pending/"+i)
                if text:
                    response_save = await save_audio(user, i, text)
                    try:
                        if not response_save:
                            return {"result": False}
                    except:
                        pass
    except Exception as e:
        print("\033[91merror en audio: \033[0m",e)
        return {"result": False}
    try:
        if len(files_txt) > 0:
            for i in files_txt:
                text = await read_one_txt(f"{files_path}subject/pending/"+i)
                if text:
                    response_save = await save_text(user, i)
                    try:
                        if not response_save:
                            return {"result": False}
                    except:
                        pass
    except Exception as e:
        print("\033[91merror en txt: \033[0m",e)
        return {"result": False}

    total_files = []
    total_files.extend(files_audio)
    total_files.extend(files_pdf)
    total_files.extend(files_txt)
    if len(total_files) > 0:
        with open(f"{files_path}context_selected/{user}.txt", 'a') as f:
            for i in total_files:
                i = i.replace(user, "")
                f.write(i+"\n")
    return {"result": True}
        
@app.post("/context")
async def get_context(request: Request):  # Agregar el parámetro Request
    data = await request.json()
    try:
        user = data['user']
        prompt = data['text']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    try:
        closer = await get_closer(user, prompt, number=10)
    except Exception as e:
        print(f"\033[91m{e}\033[0m")
        return "Answer this question: "
    if type(closer) == bool:
        return "Answer this question: "
    context = closer['text'].tolist()
    await add_daily_query_usage(user, 1)
    plain_text = " ".join(context)
    return plain_text

@app.post("/update_context_files")
async def update_context_files(request: Request):
    global context_selected_path
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
        files = data['files']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    with open(f"{context_selected_path}{user}.txt", 'w') as f:
        try:
            for i in files:
                f.write(i+"\n")
        except:
            return False
    return True

@app.post("/get_documents")
async def get_documents(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    documentos = await documents_user(user)
    #obtenemos los nombres reales
    df = pd.read_csv("names.csv")
    try:
        documentos = [df[df.hash_name == i].name.tolist()[0] for i in documentos]
    except:
        documentos = []
    #ahora eliminamos el correo si existe
    dominio = '@gmail.com'
    for i in range(len(documentos)):
        if "@" in documentos[i]:
            #identificamos el correo
            correo = documentos[i].split("@")[0]
            correo = correo + dominio
            documentos[i] = documentos[i].replace(correo, "")
    return {'result': documentos}

@app.post("/delete_name")
async def delete_name(request: Request):  # Agregar el parámetro Request
    global files_path
    data = await request.json()
    try:
        user = data['user']
        name_file = data['name']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    df = pd.read_csv("names.csv")
    #conseguimos el hash_name del archivo
    hash_name = df[df.name == name_file].hash_name.tolist()[0]
    #borramos el archivo
    await delete_document(user, hash_name)
    try:
        os.remove(f"{files_path}subject/pending/"+hash_name)
    except:
        os.remove(f"{files_path}subject/embed/"+hash_name)
    embed_name = hash_name.split(".")[0:-1]
    embed_name = "".join(embed_name)
    os.remove(f"{files_path}embeddings/"+embed_name+".csv")
    #borramos el registro del archivo
    df = df[df.name != name_file]
    df.to_csv("names.csv", index=False)
    return True

@app.post("/get_chats")
async def get_chats():
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    chats = await get_all_chats(user)
    chats = chats.to_json()
    return {"result": True, "message": "Chats retrieved successfully", "chats": chats}

@app.post("/usage")
async def get_usage(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}    
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    usage_query = await get_daily_query_usage(user)
    usage_whisper = await get_monthly_whisper_usage(user)
    usage_embeddings = await get_monthly_embeddings_usage(user)
    #transformamos los datos de uso en un porcentaje dependiendo del tipo de usuario:
    type_user = await get_type_user(user)
    if type_user == "free":
        usage_query = usage_query/free_limit*100
        usage_whisper = usage_whisper/whisper_free_limit*100
        usage_embeddings = usage_embeddings/monthly_free_limit*100
    elif type_user == "basic":
        usage_query = usage_query/basic_limit*100
        usage_whisper = usage_whisper/whisper_basic_limit*100
        usage_embeddings = usage_embeddings/monthly_basic_limit*100
    elif type_user == "pro":
        usage_query = usage_query/pro_limit*100
        usage_whisper = usage_whisper/whisper_pro_limit*100
        usage_embeddings = usage_embeddings/monthly_pro_limit*100
    #ahora acortamos los numeros
    usage_query = round(usage_query, 2)
    usage_whisper = round(usage_whisper, 2)
    usage_embeddings = round(usage_embeddings, 2)
    usage_resume = {
        "query": usage_query,
        "embeddings": usage_embeddings,
        "audio": usage_whisper
    }
    return {"usage": usage_resume}

@app.post("/chat")
async def chat_endpoint(request: Request):
    message = await request.json()
    try:
        user = message['user']
        token = message['token']
        text = message['message']
        temperature = message['temperature']
        max_tokens = message['max_tokens']
    except:
        return {"result": False, "message": "Invalid parameters"}
    type_user = await get_type_user(user)

    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    
    daily_query_usage = await get_daily_query_usage(user)
    if daily_query_usage >= free_limit and type_user == "free":
        return {"user": user, "message": "Exceeded daily query limit for free user", "image": None}
    if daily_query_usage >= basic_limit and type_user == "basic":
        return {"user": user, "message": "Exceeded daily query limit for basic user", "image": None}
    if daily_query_usage >= pro_limit and type_user == "pro":
        return {"user": user, "message": "Exceeded daily query limit for pro user", "image": None}

    try:
        response = await chat(user, text, temperature, max_tokens)
        await add_daily_query_usage(user, 1)
    except Exception as e:
        return {"user": user, "message": "Error in chat"}

    state_chart = response[1]
    response_text = response[0]
    
    if state_chart:
        try:
            imagen = await imagen_a_bytesio(f"{files_path}images/{user}.png")
            imagen_base64 = base64.b64encode(imagen).decode("utf-8")
        except Exception as e:
            return {"user": user, "message": response_text, "image": None}
        return {"user": user, "message": response_text, "image": imagen_base64}
        
    else:
        return {"user": user, "message": response_text, "image": None}

@app.post("/create_exam")
async def create_exam(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
        type_user = data['type_user']
        subject = data['subject']
        questions = data['questions']
        difficulty = data['difficulty']
        hints = data['hints']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    result = await qg.main(subject, questions, difficulty, hints, user)
    if result:
        await add_daily_query_usage(user, 1)
        return {"result": True, "message": "Exam created successfully", "title": result}
    else:
        return {"result": False, "message": "Error creating exam", "title": None}

@app.post("/get_exam")
async def get_exam(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
        title = data['title']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    try:
        with open(title, "rb") as f:
            pdf = f.read()
        pdf_base64 = base64.b64encode(pdf).decode("utf-8")
        return {"result": True, "message": "Exam retrieved successfully", "pdf": pdf_base64}
    except:
        return {"result": False, "message": "Error retrieving exam", "pdf": None}
    
@app.post("/auth_user")
async def auth0(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    return {"result": True, "message": "Valid token"}

@app.post("/get_user_type")
async def get_user_type(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}
    user_type = await get_type_user(user)
    if user_type == False:
        return {"result": False, "message": "Invalid user"}
    return {"result": True, "message": "Valid user", "type": user_type}

@app.post("/uploadfile")
async def upload_file(request: Request, file: UploadFile, user: str = Form(...)):
    files_path = os.getenv("UPLOADED_FILES_PATH")
    new_name_file = await change_filename(file.filename)
    with open(f"{files_path}{user}_{new_name_file}", "wb") as f:
        f.write(file.file.read())
    return {"message": "Archivo subido correctamente"}

@app.post("/update_token")
async def update_token(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
        auth_token = data['auth_token']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if auth_token != autentication_token:
        return {"result": False, "message": "Invalid token"}
    response = await create_user(user, token, "free")
    if response==False:
        response = await update_credentials(user, token)
    return {"result": response}

@app.post("/update_user_type")
async def update_user_type(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
        user_type = data['type']
    except:
        return {"result": False, "message": "Invalid parameters"}
    response = await update_type_user(user, token, user_type)
    return {"result": response}

@app.post("/profile")
async def get_profile(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    user_type = await get_user_data(user, token)
    if user_type == False:
        return {"result": False, "message": "Invalid user"}
    clave = 'created_at'
    if clave not in user_type.keys():
        clave = 'creation_date'
    user_data = {
        "email": user,
        "type": user_type["type_user"],
        "created_at": user_type[clave],
    }
    return {"result": True, "message": "Valid user", "data": user_data}

@app.post("/update_chat")
async def update_chat(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
        chat_id = data['chat_id']
        new_messages = data['new_messages']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    response = await update_chat_messages(user, chat_id, new_messages)
    return {"result": response}

@app.post("/delete_chat")
async def delete_chat(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
        chat_id = data['chat_id']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    response = await delete_chat(user, chat_id)
    return {"result": response}

@app.post("/get_chat_messages")
async def get_chat_messages(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
        chat_id = data['chat_id']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    response = await get_chat_messages(user, chat_id)
    return {"result": response}

@app.post("/add_chat")
async def add_new_chat(request: Request):
    data = await request.json()
    try:
        user = data['user']
        token = data['token']
        messages = data['messages']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    response = await add_chat(user, messages)
    return {"result": response}

if __name__ == "__main__":
    workers = os.getenv("AMOUNT_OF_WORKERS")
    workers = int(workers)
    asyncio.run(uvicorn.run(app, host="0.0.0.0", port=8000))