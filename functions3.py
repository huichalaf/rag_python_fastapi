import os
from mongoengine import connect, Document, StringField, ListField
import dotenv
dotenv.load_dotenv()
host = os.getenv("DATABASE_HOST")
database = os.getenv("DATABASE_CHATS_NAME")
connect(database, host=host, port=27017)

class Chat(Document):
    user = StringField(required=True)
    messages = ListField(StringField())

def get_all_chats(user):
    chats = Chat.objects(user=user)
    return chats

def add_chat(user, messages):
    chat = Chat(user=user, messages=messages)
    chat.save()
    #retornamos la id del chat nuevo
    return chat.id

def delete_chat(user, chat_id):
    chat = Chat.objects(user=user, id=chat_id).first()
    if chat:
        chat.delete()

def update_chat_messages(user, chat_id, new_messages):
    chat = Chat.objects(user=user, id=chat_id).first()
    if chat:
        chat.update(set__messages=new_messages)

def get_chat_messages(user, chat_id):
    chat = Chat.objects(user=user, id=chat_id).first()
    if chat:
        return chat.messages
    return None

class StatusUser(Document):
    user = StringField(required=True)
    action = StringField(required=True)
    status = StringField(required=True)

def get_status(user, action):
    status = StatusUser.objects(user=user, action=action).first()
    if status:
        return status.status
    return None

def update_status(user, action, status):
    status = StatusUser.objects(user=user, action=action).first()
    if status:
        status.update(set__status=status)
    else:
        status = StatusUser(user=user, action=action, status=status)
        status.save()