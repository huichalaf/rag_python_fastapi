# Utilizamos la imagen base de Python 3.11
FROM python:3.11

#instalamos ffmpeg
# Creamos el directorio de trabajo dentro del contenedor
WORKDIR /

# Copiamos los archivos de tu API al directorio de trabajo
COPY . /

# Instalamos las dependencias de la API
RUN pip install -r requirements.txt

# Exponemos el puerto de la API
EXPOSE 5678

# Comando para iniciar la API
CMD ["python", "server.py"]
