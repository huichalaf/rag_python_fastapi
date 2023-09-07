import dotenv
import json
import os
from pymongo import MongoClient
from functions import auth_user

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

database_host = os.getenv("DATABASE_HOST")
client = MongoClient(f"mongodb://{database_host}:27017/")

async def get_all_chats(user, token):
    if not auth_user(user, token):
        return False
    
    chats = []
    db = client.chats
    chats_collection = db.chats
    chats_cursor = chats_collection.findOne({'_id': user})
    for chat in chats_cursor:
        chats.append(chat)
    return chats