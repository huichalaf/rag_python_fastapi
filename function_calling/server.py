import os
import json
import base64
import asyncio
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from functions import auth_user, imagen_a_bytesio
from cost_manager import add_daily_query_usage, get_daily_query_usage, get_monthly_embeddings_usage, get_monthly_whisper_usage
from function_callin import chat

basic_limit = os.getenv("DAILY_QUERYS_BASIC_LIMIT")
pro_limit = os.getenv("DAILY_QUERYS_PRO_LIMIT")
free_limit = os.getenv("DAILY_QUERYS_FREE_LIMIT")
basic_limit = int(basic_limit)
pro_limit = int(pro_limit)
free_limit = int(free_limit)

app = FastAPI()

class Message(BaseModel):
    user: str
    token: str
    type_user: str
    text: str
    temperature: int
    max_tokens: int

@app.get("/")
async def read_root():
    return {"Status": "running"}

@app.post("/usage")
async def get_usage(message: Message):
    user = message.user
    token = message.token
    if not auth_user(user, token):
        raise HTTPException(status_code=401, detail="Invalid token")
    usage_resume = {
        "query": get_daily_query_usage(user),
        "embeddings": get_monthly_embeddings_usage(user),
        "audio": get_monthly_whisper_usage(user)
    }
    return {"usage": get_daily_query_usage(user)}

@app.post("/chat")
async def chat_endpoint(message: Message):
    user = message.user
    token = message.token
    type_user = message.type_user
    text = message.text
    temperature = message.temperature/100
    max_tokens = message.max_tokens
    print("question of user: ", user)

    # Check user authentication and usage limits
    if not auth_user(user, token):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    daily_query_usage = get_daily_query_usage(user)
    if daily_query_usage >= free_limit and type_user == "free":
        raise HTTPException(status_code=429, detail="Exceeded daily query limit for free user")
    if daily_query_usage >= basic_limit and type_user == "basic":
        raise HTTPException(status_code=429, detail="Exceeded daily query limit for basic user")
    if daily_query_usage >= pro_limit and type_user == "pro":
        raise HTTPException(status_code=429, detail="Exceeded daily query limit for pro user")

    try:
        print(f"User: {user}, Text: {text}, Temperature: {temperature}, Max tokens: {max_tokens}")
        response = chat(user, text, temperature, max_tokens)
        add_daily_query_usage(user, 1)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error during chat")

    state_chart = response[1]
    response_text = response[0]
    
    if state_chart:
        try:
            print("imagen en la respuesta")
            imagen = imagen_a_bytesio(f"images/{user}.png")
            imagen_base64 = base64.b64encode(imagen).decode("utf-8")
            print("imagen codificada")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error encoding image")
        return {"user": user, "message": response_text, "image": imagen_base64}
    else:
        return {"user": user, "message": response_text, "image": None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5678)
