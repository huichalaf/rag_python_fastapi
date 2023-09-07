import pandas as pd
import tiktoken
from datetime import datetime, date
import os
from dotenv import load_dotenv
from pymongo import MongoClient
# Cargar las variables de entorno desde el archivo .env
load_dotenv()

database_host = os.getenv("DATABASE_HOST")
client = MongoClient(f"mongodb://{database_host}:27017/")

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

async def get_type_user(user):
    db = client["users_data"]
    collection = db["users"]
    try:
        result = collection.find_one({"_id": user})
        return result["type_user"]
    except:
        return False

async def calculate_tokens(string: str, encoding_name="cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    text = ''
    if type(string) == list:
        for i in string:
            try:
                text += i
            except:
                text += i.page_content
    else:
        text = string
    num_tokens = len(encoding.encode(text))
    return num_tokens

async def chat_gpt_cost_calculator(num_tokens):
    num_tokens /= 1000
    return num_tokens * 0.002
    
async def whisper_cost_calculator(num_minutes):
    return num_minutes * 0.006

async def embeddings_cost_calculator(num_tokens):
    num_tokens /= 1000
    return num_tokens * 0.0001

async def ask_limit(user, type):
    collection = db['chat']
    collection2 = db['whisper']
    collection3 = db['embed']
    try:
        if type=="pro":
            chat_limit = 200
            tokens_limit = 2250000
            whisper_limit = 120
        elif type=="basic":
            chat_limit = 100
            tokens_limit = 1125000
            whisper_limit = 60
        else:
            return False
        #obtenemos el numero de querys al chat que ha realizado el usuario hoy
        query = collection.find_one({'_id': user})['query']
        if query >= chat_limit:
            return False
        #obtenemos el numero de tokens que ha usado el usuario en el mes
        tokens = collection3.find_one({'_id': user})['tokens']
        if tokens >= tokens_limit:
            return False
        #obtenemos el numero de minutos que ha usado el usuario en el mes
        minutes = collection2.find_one({'_id': user})['minutes']
        if minutes >= whisper_limit:
            return False
        return True
    except:
        return False

async def ask_add(user, type, tokens):
    user_type = await get_type_user(user)
    if type == "embeddings":
        if user_type == "pro":
            limit = monthly_pro_limit
        elif user_type == "basic":
            limit = monthly_basic_limit
        else:
            limit = monthly_free_limit
        usage = await get_monthly_embeddings_usage(user)
        if usage + tokens > limit:
            return False
        else:
            return True
    elif type == "chat":
        if user_type == "pro":
            limit = pro_limit
        elif user_type == "basic":
            limit = basic_limit
        else:
            limit = free_limit
        usage = await get_daily_query_usage(user)
        if usage + tokens > limit:
            return False
        else:
            return True
    elif type == "whisper":
        if user_type == "pro":
            limit = whisper_pro_limit
        elif user_type == "basic":
            limit = whisper_basic_limit
        else:
            limit = whisper_free_limit
        usage = await get_monthly_whisper_usage(user)
        if usage + tokens > limit:
            return False
        else:
            return True

async def add_daily_query_usage(user, questions):
    db = client['chat']
    collection = db['querys']
    try:
        #obtenemos el numero de tokens que ha usado el usuario hoy
        query = collection.find_one({'_id': user})['query']
        collection.delete_one({'_id': user})
        query = query + 1
        collection.insert_one({'_id': user, 'query': query})
        return True
    except:
        collection.insert_one({'_id': user, 'query': 1})
        return True

async def add_monthly_embeddings_usage(user, tokens):
    db = client['embed']
    collection = db['tokens']
    try:
        tokens2 = collection.find_one({'_id': user})['tokens']
        collection.delete_one({'_id': user})
        tokens += tokens2
        collection.insert_one({'_id': user, 'tokens': tokens})
        return True
    except:
        collection.insert_one({'_id': user, 'tokens': tokens})
        return True

async def add_monthly_whisper_usage(user, minutes):
    db = client['whisper']
    collection = db['minutes']
    try:
        minutes_past = collection.find_one({'_id': user})['minutes']
        collection.delete_one({'_id': user})
        minutes = minutes_past + minutes
        collection.insert_one({'_id': user, 'minutes': minutes})
        return True
    except:
        collection.insert_one({'_id': user, 'minutes': minutes})
        return True

async def get_daily_query_usage(user):
    db = client['chat']
    collection = db['querys']
    try:
        query = collection.find_one({'_id': user})['query']
        return query
    except:
        return 0
    
async def get_monthly_embeddings_usage(user):
    db = client['embed']
    collection = db['tokens']
    try:
        tokens = collection.find_one({'_id': user})['tokens']
        return tokens
    except:
        return 0

async def get_monthly_whisper_usage(user):
    db = client['whisper']
    collection = db['minutes']
    try:
        minutes = collection.find_one({'_id': user})['minutes']
        return minutes
    except:
        return 0

async def add_cost(user, amount, category):
    if category == "embeddings":
        amount = embeddings_cost_calculator(amount)
    elif category == "chat":
        amount = chat_gpt_cost_calculator(amount)
    elif category == "whisper":
        amount = whisper_cost_calculator(amount)
    
    db = client['costs']
    collection = db['costs']
    try:
        cost = collection.find_one({'_id': user})['cost']
        cost += amount
        collection.delete_one({'_id': user})
        collection.insert_one({'_id': user, 'cost': cost})
        return True
    except:
        collection.insert_one({'_id': user, 'cost': amount})
        return True