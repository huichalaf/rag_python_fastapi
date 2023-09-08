# Utilizamos la imagen base de Python 3.11
FROM python:3.11

#instalamos ffmpeg
RUN apt-get update && apt-get install -y ffmpeg
RUN apt update && \
    apt install -y texlive-base texlive-extra-utils && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Creamos el directorio de trabajo dentro del contenedor
WORKDIR /

# Copiamos los archivos de tu API al directorio de trabajo
COPY . /

# Instalamos las dependencias de la API
RUN pip install -r requirements.txt

# Exponemos el puerto de la API
EXPOSE 8000

# Comando para iniciar la API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers" ,"4", "--loop", "asyncio"]