from langchain.embeddings.openai import OpenAIEmbeddings
import openai 
import os, sys
import pandas as pd
import numpy as np
import PyPDF2
import dotenv
from functions2 import add_document, delete_document, documents_user, rename_by_hash, cosine_similarity, get_all_embeddings, get_all_text, transcribe_audio
from langchain.text_splitter import RecursiveCharacterTextSplitter
from cost_manager import add_monthly_embeddings_usage, calculate_tokens, add_daily_query_usage
dotenv.load_dotenv()
files_path = os.getenv("FILES_PATH")
openai.api_key = os.getenv("OPENAI_API_KEY")

def divide_text_pdf_str(text):
    text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
    chunk_size = 256,
    chunk_overlap  = 20,
    length_function = len)
    texts = text_splitter.create_documents([text])
    text_return = []
    for i in range(len(texts)):
        text_return.append(texts[i].page_content)
    return text_return

def get_embedding(user, text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    #tokens = calculate_tokens(text)
    #add_monthly_embeddings_usage(user, tokens)
    return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']

def get_embeddings(text):
    model = OpenAIEmbeddings()
    embeddings = model.embed_documents(text)
    return embeddings

def open_embeddings(file_name):
    global files_path
    file_name = file_name.split(".")[0:-1]
    file_name = "".join(file_name)
    new_file_name = f"{files_path}embeddings/"+file_name+".csv"
    df = pd.read_csv(new_file_name)
    df['embedding'] = df.embedding.apply(eval).apply(np.array)
    return df

def read_one_pdf(path):
    try:
        with open(path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            document = ''
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                document += page.extract_text()
            
            document_parsed = divide_text_pdf_str(document)
            document_parsed_str = []
            for i in document_parsed:
                try:
                    document_parsed_str.append(str(i.page_content))
                except:
                    document_parsed_str.append(str(i))
            return document_parsed_str
    except Exception as e:
        print(e)
        return False

def save_document(user, path):
    print("save_document: ",user)
    global files_path
    text = read_one_pdf(f"{files_path}subject/pending/"+path)
    print("antes", type(text))
    total_tokens = calculate_tokens(text)
    print("total_tokens: ",total_tokens)
    add_monthly_embeddings_usage(user, total_tokens)
    embeddings = get_embeddings(text)
    name = rename_by_hash(path, text, user)
    print(name)
    print(add_document(user, name))
    print(len(text), len(embeddings))
    df = pd.DataFrame({'text': text, 'embedding': embeddings})
    file_name = name.split(".")[0:-1]
    file_name = "".join(file_name)
    df.to_csv(f"{files_path}embeddings/"+file_name+".csv")
    print(f"saved {path}")
    return embeddings, text

def save_audio(user, path, text):
    global files_path
    total_tokens = calculate_tokens(text)
    add_monthly_embeddings_usage(user, total_tokens)
    embeddings = get_embeddings(text)
    name = rename_by_hash(path, text, user)
    add_document(user, name)
    print(len(text), len(embeddings))
    df = pd.DataFrame({'text': text, 'embedding': embeddings})
    file_name = name.split(".")[0:-1]
    file_name = "".join(file_name)
    df.to_csv(f"{files_path}embeddings/"+file_name+".csv")
    print(f"saved {path}")
    return embeddings, text

def save_text(user, path):
    global files_path
    test = open(path, "r")
    text = test.read()
    total_tokens = calculate_tokens(text)
    add_monthly_embeddings_usage(user, total_tokens)
    embeddings = get_embeddings(text)
    name = rename_by_hash(path, text, user)
    add_document(user, name)
    print(len(text), len(embeddings))
    df = pd.DataFrame({'text': text, 'embedding': embeddings})
    file_name = name.split(".")[0:-1]
    file_name = "".join(file_name)
    df.to_csv(f"{files_path}embeddings/"+file_name+".csv")
    print(f"saved {path}")
    return embeddings, text


def load_embeddings(user):
    global files_path
    documentos = documents_user(user)
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
    documentos_selected = []
    with open(f'{files_path}context_selected/{user}.txt', 'r') as file:
        for line in file:
            documentos_selected.append(line.strip())
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
        embeddings_df[i] = open_embeddings(i)
    return embeddings_df

def get_closer(user, prompt, number=5):
    prompt = get_embedding(user, prompt)
    data = load_embeddings(user)
    if len(data) == 0:
        return False
    claves = list(data.keys())
    for i in claves:
        data[i]['similarity'] = data[i]['embedding'].apply(lambda x: cosine_similarity(x, prompt))
    df = pd.concat([data[i] for i in claves])
    df = df.sort_values(by=['similarity'], ascending=False)
    return df.head(number)