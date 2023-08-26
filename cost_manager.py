import pandas as pd
import tiktoken
from datetime import datetime, date
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

user_mongo = os.getenv("USER_MONGO")
password_mongo = os.getenv("PASSWORD_MONGO")
database_host = os.getenv("DATABASE_HOST")
client = MongoClient(f"mongodb://{database_host}:27017/")


def calculate_tokens(string: str, encoding_name="cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def create_csv_file(user):
    df = pd.DataFrame(columns=["time", "tokens", "category", "price"])
    df.to_csv(f"costs/costs_{date.today()}_{user}.csv", index=False)

def chat_gpt_cost_calculator(num_tokens):
    num_tokens /= 1000
    return num_tokens * 0.002
    
def whisper_cost_calculator(num_minutes):
    return num_minutes * 0.006

def embeddings_cost_calculator(num_tokens):
    num_tokens /= 1000
    return num_tokens * 0.0001

def ask_limit(user, type):
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

def add_daily_query_usage(user, questions):
    print("añadiendo query")
    db = client['chat']
    collection = db['querys']
    try:
        #obtenemos el numero de tokens que ha usado el usuario hoy
        query = collection.find_one({'_id': user})['query']
        collection.delete_one({'_id': user})
        query = query + 1
        collection.insert_one({'_id': user, 'query': query})
        print("añadido")
        return True
    except:
        collection.insert_one({'_id': user, 'query': 1})
        print("añadido")
        return True

def add_monthly_embeddings_usage(user, tokens):
    print("añadiendo tokens")
    db = client['embed']
    collection = db['tokens']
    try:
        tokens2 = collection.find_one({'_id': user})['tokens']
        collection.delete_one({'_id': user})
        tokens += tokens2
        collection.insert_one({'_id': user, 'tokens': tokens})
        print("añadido")
        return True
    except:
        collection.insert_one({'_id': user, 'tokens': tokens})
        print("añadido")
        return True

def add_monthly_whisper_usage(user, minutes):
    print("añadiendo minutos")
    db = client['whisper']
    collection = db['minutes']
    try:
        minutes_past = collection.find_one({'_id': user})['minutes']
        collection.delete_one({'_id': user})
        minutes = minutes_past + minutes
        collection.insert_one({'_id': user, 'minutes': minutes})
        print("añadido")
        return True
    except:
        collection.insert_one({'_id': user, 'minutes': minutes})
        print("añadido")
        return True

def get_daily_query_usage(user):
    db = client['chat']
    collection = db['querys']
    try:
        query = collection.find_one({'_id': user})['query']
        return query
    except:
        return 0
    
def get_monthly_embeddings_usage(user):
    db = client['embed']
    collection = db['tokens']
    try:
        tokens = collection.find_one({'_id': user})['tokens']
        return tokens
    except:
        return 0

def get_monthly_whisper_usage(user):
    db = client['whisper']
    collection = db['minutes']
    try:
        minutes = collection.find_one({'_id': user})['minutes']
        return minutes
    except:
        return 0

def add_cost(user, amount, category):
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