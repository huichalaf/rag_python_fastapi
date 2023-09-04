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
    user = data['user']
    user = get_user(user)

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
                text = read_one_pdf(f"{files_path}subject/pending/"+i)
                if text:
                    save_document(user, i)
    except Exception as e:
        print("error en pdf: ",e)
        return {"result": False}
    try:
        if len(files_audio) > 0:
            for i in files_audio:
                text = transcribe_audio(user, f"{files_path}subject/pending/"+i)
                if text:
                    save_audio(user, i, text)
    except Exception as e:
        print("error en audio: ",e)
        return {"result": False}
    try:
        if len(files_txt) > 0:
            for i in files_txt:
                text = read_one_txt(f"{files_path}subject/pending/"+i)
                if text:
                    save_text(user, i)
    except Exception as e:
        print("error en txt: ",e)
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
    user = data['user']
    prompt = data['text']
    try:
        closer = get_closer(user, prompt, number=10)
    except Exception as e:
        print(e)
        return "Answer this question: "
    if type(closer) == bool:
        return "Answer this question: "
    context = closer['text'].tolist()
    plain_text = " ".join(context)
    return plain_text

@app.post("/update_context_files")
async def update_context_files(request: Request):
    data = await request.json()
    user = data['user']
    files = data['files']
    context_selected_path = os.getenv("CONTEXT_SELECTED_PATH")
    with open(f"{context_selected_path}{user}.txt", 'w') as f:
        try:
            for i in files:
                f.write(i+"\n")
        except:
            return False
    return True

@app.post("/get_name")
async def get_name(request: Request):  # Agregar el parámetro Request
    data = await request.json()
    user = data['user']
    df = pd.read_csv("names.csv")
    df = df[df.user == user]
    #print(df.name.tolist())
    return {'result': df.name.tolist()}

@app.post("/get_documents")
async def get_documents(request: Request):
    data = await request.json()
    user = data['user']
    token = data['token']
    if not auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    documentos = documents_user(user)
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
    user = data['user']
    name_file = data['name']
    df = pd.read_csv("names.csv")
    #conseguimos el hash_name del archivo
    hash_name = df[df.name == name_file].hash_name.tolist()[0]
    #borramos el archivo
    delete_document(user, hash_name)
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

@app.post("/usage")
async def get_usage(request: Request):
    data = await request.json()
    user = data['user']
    token = data['token']
    if not auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    usage_resume = {
        "query": get_daily_query_usage(user),
        "embeddings": get_monthly_embeddings_usage(user),
        "audio": get_monthly_whisper_usage(user)
    }
    return {"usage": usage_resume}

@app.post("/chat")
async def chat_endpoint(request: Request):
    message = await request.json()
    user = message['user']
    token = message['token']
    type_user = get_type_user(user)
    text = message['message']
    temperature = message['temperature']
    max_tokens = message['max_tokens']

    print("question of user: ", user)

    # Check user authentication and usage limits
    if not auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    
    daily_query_usage = get_daily_query_usage(user)
    if daily_query_usage >= free_limit and type_user == "free":
        return {"user": user, "message": "Exceeded daily query limit for free user", "image": None}
    if daily_query_usage >= basic_limit and type_user == "basic":
        return {"user": user, "message": "Exceeded daily query limit for basic user", "image": None}
    if daily_query_usage >= pro_limit and type_user == "pro":
        return {"user": user, "message": "Exceeded daily query limit for pro user", "image": None}

    try:
        print(f"User: {user}, Text: {text}, Temperature: {temperature}, Max tokens: {max_tokens}")
        response = chat(user, text, temperature, max_tokens)
        add_daily_query_usage(user, 1)
    except Exception as e:
        return {"user": user, "message": "Error in chat"}

    state_chart = response[1]
    response_text = response[0]
    
    if state_chart:
        try:
            print("imagen en la respuesta")
            imagen = imagen_a_bytesio(f"{files_path}images/{user}.png")
            imagen_base64 = base64.b64encode(imagen).decode("utf-8")
            print("imagen codificada")
        except Exception as e:
            return {"user": user, "message": response_text, "image": None}
        return {"user": user, "message": response_text, "image": imagen_base64}
        
    else:
        return {"user": user, "message": response_text, "image": None}

@app.post("/create_exam")
async def create_exam(request: Request):
    data = await request.json()
    user = data['user']
    token = data['token']
    type_user = data['type_user']
    subject = data['subject']
    questions = data['questions']
    difficulty = data['difficulty']
    hints = data['hints']
    print("questions: ", questions)
    if not auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    result = await qg.main(subject, questions, difficulty, hints, user)
    if result:
        add_daily_query_usage(user, 1)
        return {"result": True, "message": "Exam created successfully", "title": result}
    else:
        return {"result": False, "message": "Error creating exam", "title": None}

@app.post("/get_exam")
async def get_exam(request: Request):
    data = await request.json()
    user = data['user']
    token = data['token']
    title = data['title']
    if not auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    try:
        print("title: ", title)
        with open(title, "rb") as f:
            print("abriendo pdf")
            pdf = f.read()
        print("pdf leido")
        pdf_base64 = base64.b64encode(pdf).decode("utf-8")
        print("pdf codificado")
        return {"result": True, "message": "Exam retrieved successfully", "pdf": pdf_base64}
    except:
        return {"result": False, "message": "Error retrieving exam", "pdf": None}
    
@app.post("/auth_user")
async def auth0(request: Request):
    data = await request.json()
    user = data['user']
    token = data['token']
    if not auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    return {"result": True, "message": "Valid token"}

@app.post("/get_user_type")
async def get_user_type(request: Request):
    data = await request.json()
    user = data['user']
    token = data['token']
    user_type = get_type_user(user)
    if user_type == False:
        return {"result": False, "message": "Invalid user"}
    return {"result": True, "message": "Valid user", "type": user_type}

@app.post("/uploadfile")
async def upload_file(request: Request, file: UploadFile, user: str = Form(...)):
    files_path = os.getenv("UPLOADED_FILES_PATH")
    with open(f"{files_path}{user}_{change_filename(file.filename)}", "wb") as f:
        f.write(file.file.read())
    return {"message": "Archivo subido correctamente"}

@app.post("/update_token")
async def update_token(request: Request):
    data = await request.json()
    user = data['user']
    token = data['token']
    response = update_credentials(user, token)
    if response==False:
        response = create_user(user, token, "free")
    return {"result": response}

@app.post("/update_user_type")
async def update_user_type(request: Request):
    data = await request.json()
    user = data['user']
    token = data['token']
    user_type = data['type']
    response = update_type_user(user, token, user_type)
    return {"result": response}

@app.post("/profile")
async def get_profile(request: Request):
    data = await request.json()
    user = data['user']
    token = data['token']
    if not auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    user_type = get_user_data(user, token)
    if user_type == False:
        print("invalid user")
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

if __name__ == "__main__":
    workers = os.getenv("AMOUNT_OF_WORKERS")
    workers = int(workers)
    uvicorn.run(app, host="0.0.0.0", port=8000)