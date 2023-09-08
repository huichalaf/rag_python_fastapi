from langchain.embeddings.openai import OpenAIEmbeddings
import openai 
import os, sys
import pandas as pd
import asyncio
import numpy as np
import PyPDF2
import concurrent.futures
import dotenv
from functions2 import add_document, delete_document, documents_user, rename_by_hash, cosine_similarity, get_all_embeddings, get_all_text, transcribe_audio
from langchain.text_splitter import RecursiveCharacterTextSplitter
from cost_manager import add_monthly_embeddings_usage, calculate_tokens, add_daily_query_usage, ask_add
from functions3 import get_selected_files
dotenv.load_dotenv()
files_path = os.getenv("FILES_PATH")
openai.api_key = os.getenv("OPENAI_API_KEY")

async def divide_text_pdf_str(text):
    text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
    chunk_size = 512,
    chunk_overlap  = 20,
    length_function = len)
    texts = text_splitter.create_documents([text])
    text_return = []
    for i in range(len(texts)):
        text_return.append(texts[i].page_content)
    return text_return

def divide_text_pdf_str_sync(text):
    text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
    chunk_size = 512,
    chunk_overlap  = 20,
    length_function = len)
    texts = text_splitter.create_documents([text])
    text_return = []
    for i in range(len(texts)):
        text_return.append(texts[i].page_content)
    return text_return

async def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    result = await openai.Embedding.acreate(input=[text], model=model)    
    result_data = result['data'][0]['embedding']
    return result_data

async def get_embeddings(text):
    model = OpenAIEmbeddings()
    embeddings = await model.aembed_documents(text)
    return embeddings

async def open_embeddings(file_name):
    global files_path
    file_name = file_name.split(".")[0:-1]
    file_name = "".join(file_name)
    new_file_name = f"{files_path}embeddings/"+file_name+".csv"
    df = pd.read_csv(new_file_name)
    df['embedding'] = df.embedding.apply(eval).apply(np.array)
    return df

async def read_one_txt(path):
    def read_txt_in_thread(path):
        try:
            with open(path, 'r') as file:
                text = file.read()
                return text
        except Exception as e:
            print(f"\033[91mLeyendo txt: {e}\033[0m")
            return False

    with concurrent.futures.ThreadPoolExecutor() as executor:
        return await asyncio.to_thread(read_txt_in_thread, path)

async def read_one_pdf(path):
    def read_pdf_in_thread(path):
        try:
            with open(path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                document = ''
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    document += page.extract_text()
                
                document_parsed = divide_text_pdf_str_sync(document)
                document_parsed_str = []
                for i in document_parsed:
                    try:
                        document_parsed_str.append(str(i.page_content))
                    except:
                        document_parsed_str.append(str(i))
                return document_parsed_str
        except Exception as e:
            print(f"\033[91m{e}\033[0m")
            return False

    with concurrent.futures.ThreadPoolExecutor() as executor:
        return await asyncio.to_thread(read_pdf_in_thread, path)

async def save_document(user, path):
    global files_path
    try:
        text = await read_one_pdf(f"{files_path}subject/pending/"+path)
        total_tokens = await calculate_tokens(text)
        posible = await ask_add(user, "embeddings", total_tokens)
        if not posible:
            #eliminamos el archivo
            os.remove(f"{files_path}subject/pending/"+path)
            return False
        await add_monthly_embeddings_usage(user, total_tokens)
        embeddings = await get_embeddings(text)
        name = await rename_by_hash(path, text, user)
        await add_document(user, name)
        df = pd.DataFrame({'text': text, 'embedding': embeddings})
        file_name = name.split(".")[0:-1]
        file_name = "".join(file_name)
        df.to_csv(f"{files_path}embeddings/"+file_name+".csv")
        return embeddings, text
    except Exception as e:
        print(f"\033[91m{e}\033[0m")
        return False

async def save_audio(user, path, text):
    global files_path
    try:
        total_tokens = await calculate_tokens(text)
        posible = await ask_add(user, "embeddings", total_tokens)
        if not posible:
            os.remove(f"{files_path}subject/pending/"+path)
            return False
        await add_monthly_embeddings_usage(user, total_tokens)
        embeddings = await get_embeddings(text)
        name = await rename_by_hash(path, text, user)
        await add_document(user, name)
        df = pd.DataFrame({'text': text, 'embedding': embeddings})
        file_name = name.split(".")[0:-1]
        file_name = "".join(file_name)
        df.to_csv(f"{files_path}embeddings/"+file_name+".csv")
        return embeddings, text
    except Exception as e:
        print(f"\033[91m{e}\033[0m")
        return False

async def save_text(user, path, text):
    global files_path
    try:
        total_tokens = await calculate_tokens(text)
        posible = await ask_add(user, "embeddings", total_tokens)
        if not posible:
            os.remove(f"{files_path}subject/pending/"+path)
            return False
        await add_monthly_embeddings_usage(user, total_tokens)
        embeddings = await get_embeddings(text)
        name = await rename_by_hash(path, text, user)
        await add_document(user, name)
        df = pd.DataFrame({'text': text, 'embedding': embeddings})
        file_name = name.split(".")[0:-1]
        file_name = "".join(file_name)
        df.to_csv(f"{files_path}embeddings/"+file_name+".csv")
        return embeddings, text
    except Exception as e:
        print(f"\033[91m{e}\033[0m")
        return False

async def load_embeddings(user):
    global files_path
    documentos = await documents_user(user)
    df = pd.read_csv("names.csv")
    try:
        documentos_hash = [df[df.hash_name == i].hash_name.tolist()[0] for i in documentos]
        documentos = [df[df.hash_name == i].name.tolist()[0] for i in documentos]
    except:
        documentos = []
        documentos_hash = []
    dominio = '@gmail.com'
    for i in range(len(documentos)):
        if "@" in documentos[i]:
            #identificamos el correo
            correo = documentos[i].split("@")[0]
            correo = correo + dominio
            documentos[i] = documentos[i].replace(correo, "")
    documentos_selected = await get_selected_files(user)
    try:
        documentos_selected = documentos_selected[0].files
    except:
        documentos_selected = []
    indices = []
    for i in documentos_selected:
        if i in documentos:
            indices.append(documentos.index(i))
    documentos_name = [documentos[i] for i in indices]
    documentos = [documentos_hash[i] for i in indices]
    if type(documentos) == bool:
        return {}
    embeddings_df = {}
    for i in documentos:
        embeddings_df[i] = await open_embeddings(i)
    return embeddings_df

async def get_closer(user, prompt, number=5):
    try:
        prompt = await get_embedding(prompt)
        data = await load_embeddings(user)
        if len(data) == 0:
            return False
        claves = list(data.keys())
        for i in claves:
            data[i]['similarity'] = data[i]['embedding'].apply(lambda x: cosine_similarity(x, prompt))
        df = pd.concat([data[i] for i in claves])
        df = df.sort_values(by=['similarity'], ascending=False)
        return df.head(number)
    except Exception as e:
        print(f"\033[91m{e}\033[0m")
        return False