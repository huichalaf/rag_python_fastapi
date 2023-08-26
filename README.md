# Servers de python y comunicacion con openai api del proyecto learnyourown
### uso del puerto 8000 para comunicacion
## Endpoint: `/`

Descripción: Este endpoint devuelve un mensaje indicando que el servidor está en funcionamiento.

Método: GET

Parámetros de entrada: Ninguno

Respuesta exitosa:
```json
{
    "Status": "Running"
}
```

## Endpoint: `/load_context`

Descripción: Este endpoint procesa y carga el contexto de archivos de un usuario.

Método: POST

Parámetros de entrada:
- `user` (str): Nombre de usuario.
- `type_user` (str): Tipo de usuario.
- Datos JSON con información de los archivos pendientes a procesar.

Respuesta exitosa:
```json
{
    "result": true
}
```

## Endpoint: `/context`

Descripción: Este endpoint devuelve el contexto relacionado con un texto de entrada para un usuario.

Método: POST

Parámetros de entrada:
- `user` (str): Nombre de usuario.
- Datos JSON con el texto de entrada (`text`).

Respuesta exitosa:
Texto del contexto generado.

## Endpoint: `/get_name`

Descripción: Este endpoint obtiene el nombre asociado a un usuario.

Método: POST

Parámetros de entrada:
- `user` (str): Nombre de usuario.

Respuesta exitosa:
```json
{
    "result": ["Nombre"]
}
```

## Endpoint: `/get_documents`

Descripción: Este endpoint obtiene los documentos asociados a un usuario.

Método: POST

Parámetros de entrada:
- `user` (str): Nombre de usuario.

Respuesta exitosa:
```json
{
    "result": ["documento1.pdf", "documento2.txt"]
}
```

## Endpoint: `/delete_name`

Descripción: Este endpoint elimina un nombre asociado a un usuario y sus archivos relacionados.

Método: POST

Parámetros de entrada:
- `user` (str): Nombre de usuario.
- `name` (str): Nombre a eliminar.

Respuesta exitosa:
```json
true
```

## Endpoint: `/usage`

Descripción: Este endpoint devuelve el uso diario de consultas para un usuario.

Método: POST

Parámetros de entrada:
- Datos JSON con información del usuario y el token.

Respuesta exitosa:
```json
{
    "usage": 5
}
```

## Endpoint: `/chat`

Descripción: Este endpoint permite una conversación en tiempo real con el modelo de chat.

Método: POST

Parámetros de entrada:
- Datos JSON con información del usuario, token, tipo de usuario, texto, temperatura y límite de tokens.

Respuesta exitosa:
Texto de respuesta del modelo de chat.

## Endpoint: `/create_exam`

Descripción: Este endpoint crea un examen con las preguntas proporcionadas.

Método: POST

Parámetros de entrada:
- Datos JSON con información del usuario, token, tipo de usuario, asignatura, preguntas, dificultad y pistas.

Respuesta exitosa:
```json
{
    "result": true,
    "message": "Exam created successfully",
    "title": "Nombre del examen"
}
```

## Endpoint: `/get_exam`

Descripción: Este endpoint obtiene un examen en formato PDF.

Método: POST

Parámetros de entrada:
- Datos JSON con información del usuario, token y título del examen.

Respuesta exitosa:
```json
{
    "result": true,
    "message": "Exam retrieved successfully",
    "pdf": "Base64 encoded PDF"
}
```