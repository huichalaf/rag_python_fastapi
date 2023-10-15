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
from functions import calculate_tokens

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
autentication_token = os.getenv("AUTENTICATION_TOKEN")
uploaded_files_folder = os.getenv("UPLOADED_FILES_PATH")
costs_path = os.getenv("COSTS_PATH")
price_context = float(os.getenv("PRICE_CONTEXT"))

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
    if not await check_tokens(user):
        print("error tokens")
        return {"result": False, "message": "You don't have tokens"}

    updated_status = await update_status(user, "active")
    hash_names=[]
    files_path = os.getenv("FILES_PATH")
    print(files_path)
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
                text_string = " ".join(text)
                total_tokens = await calculate_tokens(text_string)
                await add_tokens_embeddings(user, total_tokens)
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
                text_string = " ".join(text)
                total_tokens = await calculate_tokens(text_string)
                await add_tokens_embeddings(user, total_tokens)
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
                os.system(f"rm {files_path}subject/pending/{f}")
        except Exception as e:
            print(f"\033{e}\033[0m")
    await update_status(user, "inactive")
    return {"result": True, "message": "Documents loaded successfully"}
        
@app.post("/context")
async def get_context(request: Request):  # Agregar el parámetro Request
    data = await request.json()
    global price_context
    try:
        user = data['user']
        prompt = data['text']
        token = data['token']
    except:
        return {"result": False, "message": "Invalid parameters"}
    if not await auth_user(user, token):
        print("error auth")
        return {"result": False, "message": "Invalid token"}
    if not await check_tokens(user):
        print("error tokens")
        return {"result": False, "message": "You don't have tokens"}
    try:
        closer = await get_closer(user, prompt, number=5)
    except Exception as e:
        await add_tokens_usage(user, price_context)
        print(f"\033[91mError: {e}\033[0m")
        return "Answer this question: "
    if type(closer) == bool:
        await add_tokens_usage(user, price_context)
        return "Answer this question: "
    context = closer['text'].tolist()
    plain_text = " ".join(context)
    await add_tokens_usage(user, price_context)
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
        os.remove(embeddings_folder+embed_name+".csv")
    except:
        print("the embedd does not exists")
    try:
        try:
            os.remove(f"{files_path}subject/pending/"+file_name+".pdf")
        except:
            os.remove(f"{files_path}subject/pending/"+file_name+".txt")
    except:
        try:
            try:
                os.remove(f"{files_path}subject/embed/"+file_name+".pdf")
            except:
                os.remove(f"{files_path}subject/embed/"+file_name+".txt")
        except:
            print("error deleting from both paths, the file probably does not exists")
    response = await delete_files(user, file_name, name_file, status)
    if response:
        return True
    return False

@app.post("/uploadfile")
async def upload_file(request: Request, file: UploadFile, user: str = Form(...)):
    global files_path
    files_path = os.getenv("UPLOADED_FILES_PATH")
    new_name_file = await change_filename(file.filename)
    files_user = await get_files(user)
    if len(files_user) >= 10:
        return {"message": "Exceed files limit"}
    a_tokens = await get_a_tokens(user)
    if a_tokens <= 0:
        return {"message": "You don't have tokens"}
    with open(f"{files_path}{user}_{new_name_file}", "wb") as f:
        f.write(file.file.read())
    return {"message": "Archivo subido correctamente"}

if __name__ == "__main__":
    asyncio.run(uvicorn.run(app, host="0.0.0.0", port=8000))