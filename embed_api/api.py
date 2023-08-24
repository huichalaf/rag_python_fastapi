from fastapi import FastAPI, Request
#from embed import *
#from get_data import *
from cost_manager import calculate_tokens, get_monthly_embeddings_usage
from dotenv import load_dotenv
from main import *
import os
import uvicorn

app = FastAPI()
load_dotenv()
monthly_basic_limit = os.getenv("MONTHLY_EMBEDDINGS_BASIC_LIMIT")
monthly_pro_limit = os.getenv("MONTHLY_EMBEDDINGS_PRO_LIMIT")
monthly_free_limit = os.getenv("MONTHLY_EMBEDDINGS_FREE_LIMIT")
monthly_basic_limit = int(monthly_basic_limit)
monthly_pro_limit = int(monthly_pro_limit)
monthly_free_limit = int(monthly_free_limit)


@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/load_context")
async def save_context(request: Request):  # Agregar el parámetro Request
    
    data = await request.json()  # Usar await para obtener los datos del body de la solicitud
    user = data['user']
    type_user = data['type_user']

    files_prev = os.listdir("subject/pending")
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
                text = read_one_pdf("subject/pending/"+i)
                if text:
                    save_document(user, i)
    except Exception as e:
        print("error en pdf: ",e)
        return {"result": False}
    try:
        if len(files_audio) > 0:
            for i in files_audio:
                text = transcribe_audio(user, "subject/pending/"+i)
                if text:
                    save_audio(user, i, text)
    except Exception as e:
        print("error en audio: ",e)
        return {"result": False}
    try:
        if len(files_txt) > 0:
            for i in files_txt:
                text = read_one_txt("subject/pending/"+i)
                if text:
                    save_text(user, i)
    except Exception as e:
        print("error en txt: ",e)
        return {"result": False}

    #print(files_audio, files_pdf, files_txt)
    total_files = []
    total_files.extend(files_audio)
    total_files.extend(files_pdf)
    total_files.extend(files_txt)
    #print(total_files)
    if len(total_files) > 0:
        with open(f"context_selected/{user}.txt", 'a') as f:
            for i in total_files:
                #eliminamos el nombre de usuario del nombre de archivo
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
    data = await request.json()
    user = data['user']
    name_file = data['name']
    df = pd.read_csv("names.csv")
    #conseguimos el hash_name del archivo
    hash_name = df[df.name == name_file].hash_name.tolist()[0]
    #borramos el archivo
    delete_document(user, hash_name)
    try:
        os.remove("subject/pending/"+hash_name)
    except:
        os.remove("subject/embed/"+hash_name)
    embed_name = hash_name.split(".")[0:-1]
    embed_name = "".join(embed_name)
    os.remove("embeddings/"+embed_name+".csv")
    #borramos el registro del archivo
    df = df[df.name != name_file]
    df.to_csv("names.csv", index=False)
    return True

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)