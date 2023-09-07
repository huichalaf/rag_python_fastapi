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

async def get_all_chats(user):
    chats = Chat.objects(user=user)
    return chats

async def add_chat(user, messages):
    chat = Chat(user=user, messages=messages)
    chat.save()
    #retornamos la id del chat nuevo
    return chat.id

async def delete_chat(user, chat_id):
    chat = Chat.objects(user=user, id=chat_id).first()
    if chat:
        chat.delete()

async def update_chat_messages(user, chat_id, new_messages):
    chat = Chat.objects(user=user, id=chat_id).first()
    if chat:
        chat.update(set__messages=new_messages)

async def get_chat_messages(user, chat_id):
    chat = Chat.objects(user=user, id=chat_id).first()
    if chat:
        return chat.messages
    return None

class StatusUser(Document):
    user = StringField(required=True)
    action = StringField(required=True)
    status = StringField(required=False)

async def get_status(user, action):
    status = StatusUser.objects(user=user, action=action).first()
    if status:
        return status.status
    return None

async def update_status(user, action, status_action):
    status = StatusUser.objects(user=user, action=action).first()
    if status:
        status.update(set__status=status_action)
        return True
    else:
        status = StatusUser(user=user, action=action, status=status_action)
        status.save()
        return True

class SelectedFiles(Document):
    user = StringField(required=True)
    files = ListField(StringField())

async def get_selected_files(user):
    files = SelectedFiles.objects(user=user)
    return files

async def add_selected_files(user, files):
    selected_files = SelectedFiles(user=user, files=files)
    selected_files.save()
    return True

async def delete_all_selected_files(user):
    selected_files = SelectedFiles.objects(user=user)
    selected_files.delete()
    return True