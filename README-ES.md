
# Documentación de la API de FastAPI

Esta documentación describe las rutas disponibles en la API de FastAPI. Asegúrate de tener acceso a la documentación adecuada para comprender cómo utilizar cada ruta.

## Ruta Raíz
### `GET /`
- **Descripción:** Verificar el estado de la API.
- **Parámetros:**
  - Ninguno.
- **Respuesta de Ejemplo:**
  ```json
  {"Status": "Running", "IP": "192.168.1.1"}
  ```

## Cargar Contexto
### `POST /load_context`
- **Descripción:** Carga documentos y contexto para un usuario.
- **Parámetros de Solicitud:**
  - `user` (cadena): El nombre de usuario.
- **Respuesta de Ejemplo:**
  ```json
  {"result": true, "message": "Documentos cargados correctamente"}
  ```

## Obtener Contexto
### `POST /context`
- **Descripción:** Obtiene contexto para un usuario basado en una solicitud.
- **Parámetros de Solicitud:**
  - `user` (cadena): El nombre de usuario.
  - `text` (cadena): El texto de la solicitud.
  - `token` (cadena): Token de autenticación.
- **Respuesta de Ejemplo:**
  ```json
  {"result": true, "message": "Texto de contexto obtenido correctamente"}
  ```

## Eliminar Archivo
### `POST /delete_file`
- **Descripción:** Elimina un archivo cargado por un usuario.
- **Parámetros de Solicitud:**
  - `user` (cadena): El nombre de usuario.
  - `file` (cadena): Nombre del archivo a eliminar.
  - `token` (cadena): Token de autenticación.
- **Respuesta de Ejemplo:**
  ```json
  true
  ```

## Subir Archivo
### `POST /uploadfile`
- **Descripción:** Sube un archivo al sistema.
- **Parámetros de Solicitud:**
  - `user` (cadena): El nombre de usuario.
  - `file` (archivo): Archivo a cargar.
- **Respuesta de Ejemplo:**
  ```json
  {"message": "Archivo subido correctamente"}
  ```

## Ejecutar la API
La API FastAPI se ejecuta en el puerto 8000. Asegúrate de iniciar la API para utilizar las rutas descritas anteriormente.

```
uvicorn main:app --host 0.0.0.0 --port 8000
```
