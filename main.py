from langchain.embeddings.openai import OpenAIEmbeddings
import openai 
import os, sys
import pandas as pd
import asyncio
import numpy as np
import PyPDF2
import concurrent.futures
import dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from functions import *
from database import get_files, get_selected_files
dotenv.load_dotenv()
files_path = os.getenv("FILES_PATH")
embeddings_path = os.getenv("EMBEDDINGS_FOLDER")
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
    global embeddings_path
    if '.' in file_name:
        file_name = file_name.split(".")[0:-1]
        file_name = "".join(file_name)
    new_file_name = embeddings_path+file_name+".csv"
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
    global embeddings_path
    try:
        text = await read_one_pdf(f"{files_path}subject/pending/"+path)
        posible=True
        if not posible:
            #eliminamos el archivo
            os.remove(f"{files_path}subject/pending/"+path)
            return False
        embeddings = await get_embeddings(text)
        name = await rename_by_hash(path, text, user)
        df = pd.DataFrame({'text': text, 'embedding': embeddings})
        file_name = name.split(".")[0:-1]
        file_name = "".join(file_name)
        df.to_csv(embeddings_path+file_name+".csv")
        return embeddings, text, file_name
    except Exception as e:
        print(f"\033[91m{e}\033[0m")
        return False

async def save_text(user, path, text):
    global embeddings_path
    try:
        posible=True
        if not posible:
            os.remove(f"{files_path}subject/pending/"+path)
            return False
        embeddings = await get_embeddings(text)
        name = await rename_by_hash(path, text, user)
        df = pd.DataFrame({'text': text, 'embedding': embeddings})
        file_name = name.split(".")[0:-1]
        file_name = "".join(file_name)
        df.to_csv(embeddings_path+file_name+".csv")
        return embeddings, text, file_name
    except Exception as e:
        print(f"\033[91m{e}\033[0m")
        return False

async def load_embeddings(user):
    global files_path
    documentos = await get_selected_files(user)
    documentos_name = [i[0] for i in documentos]
    documentos_hash = [i[1] for i in documentos]
    if type(documentos) == bool:
        return False
    embeddings_df = {}
    for i in documentos_hash:
        embeddings_df[i] = await open_embeddings(i)
    return embeddings_df

async def get_closer(user, prompt, number=5):
    try:
        prompt = await get_embedding(prompt)
        data = await load_embeddings(user)
        print("data: ",data)
        if len(data) == 0:
            return False
        claves = list(data.keys())
        for i in claves:
            data[i]['similarity'] = data[i]['embedding'].apply(calculate_similarity, prompt=prompt)
        df = pd.concat([data[i] for i in claves])
        df = df.sort_values(by=['similarity'], ascending=False)
        return df.head(number)
    except Exception as e:
        print(f"\033[91m{e}\033[0m")
        return False