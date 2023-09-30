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
import document_generator as q
from database import *

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
files_path = os.getenv("FILES_PATH")
monthly_basic_limit = os.getenv("MONTHLY_EMBEDDINGS_BASIC_LIMIT")
monthly_pro_limit = os.getenv("MONTHLY_EMBEDDINGS_PRO_LIMIT")
monthly_free_limit = os.getenv("MONTHLY_EMBEDDINGS_FREE_LIMIT")
embeddings_folder = os.getenv("EMBEDDINGS_FOLDER")
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
autentication_token = os.getenv("AUTENTICATION_TOKEN")
uploaded_files_folder = os.getenv("UPLOADED_FILES_PATH")
images_path = os.getenv("IMAGES_PATH")
costs_path = os.getenv("COSTS_PATH")

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
    return {"Status": "Running", "IP": client_ip}

@app.post("/load_context")
async def save_context(request: Request):  # Agregar el parámetro Request
    global files_path
    data = await request.json()  # Usar await para obtener los datos del body de la solicitud
    try:
        user = data['user']
    except:
        return {"result": False, "message": "Invalid parameters"}
    user = await get_user(user)
    if await get_status(user) == "active":
        print("already loading")
        return {"result": False, "message": "Loading documents"}
    updated_status = await update_status(user, "active")
    hash_names=[]
    files_prev = os.listdir(f"{files_path}subject/pending")
    files = []
    print(user)
    for i in files_prev:
        if user in i:
            files.append(i)
    files_pdf = [i for i in files if i.split(".")[-1] == "pdf"]
    files_txt = [i for i in files if i.split(".")[-1] == "txt"]
    try:
        if len(files_pdf) > 0:
            for i in files_pdf:
                text = await read_one_pdf(f"{files_path}subject/pending/"+i)
                if text:
                    response_save = await save_document(user, i)
                    try:
                        if response_save == False:
                            await update_status(user, "inactive")
                            return {"result": False, "message": "Exceed monthly embeddings limit"}
                        else:
                            hash_names.append(response_save[-1])
                    except:
                        hash_names.append(response_save[-1])
    except Exception as e:
        print("\033[91merror en pdf: \033[0m",e)
        await update_status(user, "inactive")
        return {"result": False}
    try:
        if len(files_txt) > 0:
            for i in files_txt:
                text = await read_one_txt(f"{files_path}subject/pending/"+i)
                if text:
                    response_save = await save_text(user, i, text)
                    try:
                        if response_save == False:
                            await update_status(user, "inactive")
                            return {"result": False, "message": "Exceed monthly embeddings limit"}
                        else:
                            hash_names.append(response_save[-1])
                    except:
                        hash_names.append(response_save[-1])
    except Exception as e:
        print("\033[91merror en txt: \033[0m",e)
        await update_status(user, "inactive")
        return {"result": False}

    total_files = []
    total_files.extend(files_pdf)
    total_files.extend(files_txt)
    print(total_files, hash_names)
    if len(total_files) > 0:
        try:
            for f in total_files:
                f_name = f.replace(user, "")
                await add_file(user, f_name, hash_names[total_files.index(f)], 1)
        except Exception as e:
            print(f"\033{e}\033[0m")
    await update_status(user, "inactive")
    return {"result": True, "message": "Documents loaded successfully"}
        
@app.post("/context")
async def get_context(request: Request):  # Agregar el parámetro Request
    data = await request.json()
    try:
        user = data['user']
        prompt = data['text']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}
#    if not await auth_user(user, token):
#        return {"result": False, "message": "Invalid token"}
    try:
        closer = await get_closer(user, prompt, number=5)
    except Exception as e:
        print(f"\033[91m{e}\033[0m")
        return "Answer this question: "
    if type(closer) == bool:
        return "Answer this question: "
    context = closer['text'].tolist()
    plain_text = " ".join(context)
    return plain_text


@app.post("/delete_file")
async def delete_name(request: Request):  # Agregar el parámetro Request
    global files_path
    data = await request.json()
    file_name = ""
    embed_name = ""
    try:
        user = data['user']
        name_file = data['file']
        token = data['token']
        hash_name = data['hash_name']
        status = int(data['status'])
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        return {"result": False, "message": "Invalid token"}
    try:
        print(user, name_file, hash_name, status)
        if '.' in hash_name:
            embed_name = hash_name.split(".")[0:-1]
            embed_name = "".join(embed_name)
            file_name = "".join(embed_name)
        else:
            file_name = hash_name
            embed_name = hash_name
    except:
        return {"result": False, "message": "Invalid parameters"}
    try:
        os.remove(f"{files_path}subject/pending/"+file_name+".pdf")
        os.remove(f"{files_path}subject/pending/"+file_name+".txt")
        os.remove(embeddings_folder+embed_name+".csv")
    except:
        try:
            os.remove(f"{files_path}subject/embed/"+file_name+".pdf")
            os.remove(f"{files_path}subject/embed/"+file_name+".txt")
            os.remove(embeddings_folder+embed_name+".csv")
        except:
            pass
    response = await delete_files(user, file_name, name_file, status)
    if response:
        return True
    return False

@app.post("/uploadfile")
async def upload_file(request: Request, file: UploadFile, user: str = Form(...)):
    files_path = os.getenv("UPLOADED_FILES_PATH")
    new_name_file = await change_filename(file.filename)
    with open(f"{files_path}{user}_{new_name_file}", "wb") as f:
        f.write(file.file.read())
    return {"message": "Archivo subido correctamente"}

if __name__ == "__main__":
    asyncio.run(uvicorn.run(app, host="0.0.0.0", port=8000))