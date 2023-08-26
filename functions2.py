import dotenv
import os, sys
from pymongo import MongoClient
from hashlib import sha256
import numpy as np
from pydub import AudioSegment
from cost_manager import add_monthly_whisper_usage
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import date
dotenv.load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
user_mongo = os.getenv("USER_MONGO")
password_mongo = os.getenv("PASSWORD_MONGO")

#print(user_mongo, password_mongo)
database_host = os.getenv("DATABASE_HOST")
client = MongoClient(f"mongodb://{database_host}:27017/")

def get_audio_duration(ruta_archivo):
    try:
        audio = AudioSegment.from_file(ruta_archivo)
        duracion_segundos = len(audio) / 1000.0  # Convertir a segundos
        return duracion_segundos
    except Exception as e:
        print(f"Error al obtener la duración del audio: {e}")
        return None

def add_document(user, name):
    try:
        db = client['embeddings']
        collection = db["users"]
        try:
            document = collection.find_one({"_id": user})
            documents = document["documents"]
            dates = document["dates"]
            print(name, documents)
            if name not in documents:
                documents.append(name)
                dates.append(str(date.today()))
                collection.update_one({"_id": user}, {"$set": {"documents": documents}})
                collection.update_one({"_id": user}, {"$set": {"dates": dates}})
            return True
        except:
            collection.insert_one({"_id": user, "documents": [name], "dates": [str(date.today())]})
            return True
    except:
        return False

def delete_document(user,name):
    try:
        db = client['embeddings']
        collection = db["users"]
        try:
            document = collection.find_one({"_id": user})
            documents = document["documents"]
            dates = document["dates"]
            indice = documents.index(name)
            documents.remove(name)
            dates.pop(indice)
            collection.update_one({"_id": user}, {"$set": {"documents": documents, "dates": dates}})
            return True
        except:
            return False
    except:
        return False

def documents_user(user):
    try:
        db = client['embeddings']
        collection = db["users"]
        try:
            document = collection.find_one({"_id": user})
            documents = document["documents"]
            return documents
        except:
            return False
    except:
        return False

def rename_by_hash(path, text, user):
    files_path = os.getenv("FILES_PATH")
    extension = path.split(".")[-1]
    if type(text) == list:
        text = " ".join(text)
    hash_object = sha256(text.encode())
    hex_dig = hash_object.hexdigest()
    new_name = hex_dig+"."+extension
    with open('names.csv', 'a') as f:
        f.write(f"{new_name},{path},{user}\n")
    os.rename(f"{files_path}subject/pending/"+path, f"{files_path}subject/embed/"+new_name)
    #os.remove("subject/"+path)
    return new_name

def get_all_text(data):
    keys = list(data.keys())
    text = []
    for i in keys:
        text.extend(data[i]['text'].tolist())
    return text

def get_all_embeddings(data):
    keys = list(data.keys())
    embeddings = []
    for i in keys:
        embeddings.extend(data[i]['embedding'].tolist())
    return embeddings

def cosine_similarity(a, b):
    return np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))

def divide_text_str(text):
    print("dividiendo texto")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=256,
        chunk_overlap=20,
        length_function=len,
    )
    text_pre_pure = text_splitter.create_documents([text])
    text_pure = text_splitter.split_text(text)
    return text_pure

def transcribe_audio(user, file):

    audio_file = open(file, "rb")
    file1 = file
    file = file.split('.')[:-1]
    file = '.'.join(file)
    #calculamos el tiempo del audio
    duration = get_audio_duration(file1)
    add_monthly_whisper_usage(user, duration)
    os.system(f"mkdir {file}")
    os.system(f"ffmpeg -i {file1} -f segment -segment_time 60 -c copy {file}/out%03d.wav")
    total_text = ''
    base_path = file+"/"

    for file in os.listdir(f"{file}"):
        if file.endswith(".wav"):
            print(base_path+file)
            file_audio = open(base_path+file, "rb")
            transcript = openai.Audio.transcribe("whisper-1", file_audio)
            total_text += transcript["text"]

    text = divide_text_str(total_text)
    text_return = []

    for part in text:
        temporal = ''
        for i in range(len(part)):
            temporal += part[i]
        text_return.append(temporal)

    print("eliminando ", base_path)
    os.system(f"rm -r {base_path}")
    return text_return

def download_music_mp3(link):
    #aca descargamos el audio del video en formato mp3
    yt = YouTube(link)
    yt.streams.filter(only_audio=True).first().download()
    #aca cambiamos el nombre del archivo descargado
    for file in os.listdir():
        if file.endswith(".mp4"):
            os.rename(file, "music.mp3")
    #aca cambiamos el formato del archivo descargado
    subprocess.call(['ffmpeg', '-i', 'music.mp3', 'music.wav'])
    #aca borramos el archivo descargado en formato mp3
    os.remove("music.mp3")
    #aca cambiamos el nombre del archivo descargado
    name = link.split('=')[-1]+".wav"
    for file in os.listdir():
        if file.endswith(".wav"):
            os.rename(file, name)
    return name