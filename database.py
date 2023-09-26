import pymongo
import sys
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

db_user = os.getenv("MONGODB_USER")
db_password = os.getenv("MONGODB_PASSWORD")
base_token = os.getenv("TOKEN_CONTEXT")

try:
    client = pymongo.MongoClient(f"mongodb+srv://{db_user}:{db_password}@serverlessinstance0.oo6ew3r.mongodb.net/?retryWrites=true&w=majority&appName=AtlasApp")
except pymongo.errors.ConfigurationError:
    print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
    sys.exit(1)

db = client.test
collection1 = os.getenv("MONGODB_COLLECTION1")
collection2 = os.getenv("MONGODB_COLLECTION2")
collection3 = os.getenv("MONGODB_COLLECTION3")
collection4 = os.getenv("MONGODB_COLLECTION4")
collection5 = os.getenv("MONGODB_COLLECTION5")
collection6 = os.getenv("MONGODB_COLLECTION6")
tokens = db[collection1]
stats = db[collection2]
status = db[collection3]
chats = db[collection4]
files = db[collection5]
documents = db[collection6]

#--------------------auth-------------------------#
async def auth_user(user, token):
    global tokens
    if (token == base_token):
        return True
    response = tokens.find_one({"email": user})
    if response == None:
        return False
    if response['token'] != token:
        return False
    return True

#----------------stats------------------------#
async def get_stats(user):
    global stats
    response = stats.find_one({"email": user})
    if response == None:
        return False
    return response

async def add_tokens_usage(user, tokens_usage):
    global stats
    response = stats.find_one({"email": user})
    if response == None:
        return False
    stats.update_one({"email": user}, {"$set": {"a_tokens": tokens_usage}})
    return True

async def get_a_tokens(user):
    global stats
    response = stats.find_one({"email": user})
    if response == None:
        return False
    return response['a_tokens']

#------------------status-------------------#
async def get_status(user):
    global status
    status_r = status.find_one({"user": user})
    print(status_r)
    if status_r == None:
        status.insert_one({"user": user, "action": "inactive"})
        return "inactive"
    return status_r

async def update_status(user, action):
    global status
    status_r = status.update_one({"user": user}, {"$set": {"action": action}})
    if status_r == None:
        status.insert_one({"user": user, "action": action})
        return True
    return True

#-------------------chat----------------------------#
async def get_chats(user):
    global chats
    chats_response = chats.find_one({"user": user})
    if chats_response == None:
        return False
    return chats_response

async def update_chats(user):
    global chats
    chats_response = chats.find_one({"user": user})
    if chats_response == None:
        return False
    chats.update_one({"user": user}, {"$set": {"messages": []}})
    return True

async def add_chat(user, message):
    global chats
    chats_response = chats.find_one({"user": user})
    if chats_response == None:
        chats.insert_one({"user": user, "messages": [message]})
        return True
    chats.update_one({"user": user}, {"$push": {"messages": message}})
    return True

async def delete_chat(user, chat_id):
    global chats
    chats_response = chats.find_one({"user": user})
    if chats_response == None:
        return False
    chats.update_one({"user": user}, {"$pull": {"messages": {"id": chat_id}}})
    return True

async def get_chat(user, chat_id):
    global chats
    chats_response = chats.find_one({"user": user})
    if chats_response == None:
        return False
    for chat in chats_response['messages']:
        if chat['id'] == chat_id:
            return chat
    return False

#-----------------------selected files-----------------------#
async def get_files(user):
    global files
    files_response = files.find_one({"user": user})
    print(files_response)
    if files_response == None:
        return False
    lista = files_response["files"]
    for i in range(len(lista)):
        lista[i][0] = user+lista[i][0]
    return lista

async def get_selected_files(user):
    global files
    files_response = files.find_one({"user": user})
    if files_response == None:
        return False
    lista = files_response["files"]
    lista = [i for i in lista if i[2] == 1]
    for i in range(len(lista)):
        lista[i][0] = user+lista[i][0]
    return lista

async def add_file(user, file, hash, status):
    global files
    files_response = files.find_one({"user": user})
    if files_response == None:
        files.insert_one({"user": user, "files": [[file, hash, status]]})
        return True
    files.update_one({"user": user}, {"$push": {"files": [file, hash, status]}})
    return True