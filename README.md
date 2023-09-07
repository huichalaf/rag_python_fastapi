# FastAPI Application Endpoints Documentation

This documentation provides information about the endpoints available in the FastAPI application. Below, you will find details about each endpoint, including their purpose and expected input/output.

### Root Endpoint

- **HTTP Method:** GET
- **Endpoint:** `/`

#### Description

This endpoint returns information about the status of the FastAPI application and the client's IP address.

#### Request Parameters

- None

#### Response

- **Status:** Running
- **IP:** [Client IP Address]

### Load Context Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/load_context`

#### Description

This endpoint is used to load context data. It processes various types of documents (PDFs, audio files, and text files) associated with a user and stores them in the application.

#### Request Parameters

- **user:** User identifier
- **Request Body:** JSON data containing the user and document information

#### Response

- **result:** True if documents are loaded successfully; False otherwise
- **message:** Error message if the result is False

### Context Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/context`

#### Description

This endpoint retrieves context data based on a user's input prompt. It uses the input text to generate context and returns it as plain text.

#### Request Parameters

- **user:** User identifier
- **text:** Input text for generating context
- **token:** Authentication token

#### Response

- Plain text containing the generated context

### Update Context Files Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/update_context_files`

#### Description

This endpoint allows users to update their context files. It replaces the current selection of files with the provided list of files.

#### Request Parameters

- **user:** User identifier
- **files:** List of files to update

#### Response

- True if the files are updated successfully

### Get Documents Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/get_documents`

#### Description

This endpoint retrieves a list of documents associated with a user. It also removes any email addresses from the document names.

#### Request Parameters

- **user:** User identifier
- **token:** Authentication token

#### Response

- List of document names without email addresses

### Delete Name Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/delete_name`

#### Description

This endpoint allows users to delete a specific name record and associated files. It requires authentication to ensure the user has the necessary permissions to delete the record.

#### Request Parameters

- **user:** User identifier
- **name:** Name of the record to delete
- **token:** Authentication token

#### Response

- True if the record is deleted successfully

### Get Chats Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/get_chats`

#### Description

This endpoint retrieves a list of chats associated with a user. It requires authentication to ensure the user has the necessary permissions to access the chat data.

#### Request Parameters

- **user:** User identifier
- **token:** Authentication token

#### Response

- **result:** True if the chats are retrieved successfully; False otherwise
- **message:** Error message if the result is False
- **chats:** JSON representation of chat data

### Usage Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/usage`

#### Description

This endpoint provides information about the usage statistics for a user, including daily query usage, monthly Whisper usage, and monthly embeddings usage. Usage data is transformed into percentages based on the user's subscription type (free, basic, pro).

#### Request Parameters

- **user:** User identifier
- **token:** Authentication token

#### Response

- Usage data in percentage format for query, Whisper, and embeddings

### Chat Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/chat`

#### Description

This endpoint allows users to engage in a chat conversation. Users can send messages, and the system responds with generated text. The endpoint checks daily query limits and user subscriptions to manage usage.

#### Request Parameters

- **user:** User identifier
- **token:** Authentication token
- **message:** User's message
- **temperature:** Chat generation temperature
- **max_tokens:** Maximum tokens for the response

#### Response

- **user:** User identifier
- **message:** Chat response message
- **image:** Base64-encoded image (if available)

### Create Exam Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/create_exam`

#### Description

This endpoint allows users to create an exam with specified parameters such as subject, number of questions, difficulty, and hints. It requires authentication to ensure the user has the necessary permissions to create an exam.

#### Request Parameters

- **user:** User identifier
- **token:** Authentication token
- **type_user:** User type (e.g., free, basic, pro)
- **subject:** Exam subject
- **questions:** Number of questions in the exam
- **difficulty:** Exam difficulty level
- **hints:** Whether hints are allowed

#### Response

- **result:** True if the exam is created successfully; False otherwise
- **message:** Message indicating the result of the exam creation
- **title:** Title of the created exam (if successful)

### Get Exam Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/get_exam`

#### Description

This endpoint allows users to retrieve a previously created exam. Users must provide the title of the exam to retrieve it. Authentication is required to ensure the user has access to the exam.

#### Request Parameters

- **user:** User identifier
- **token:** Authentication token
- **title:** Title of the exam to retrieve

#### Response

- **result:** True if the exam is retrieved successfully; False otherwise
- **message:** Message indicating the result of the exam retrieval
- **pdf:** Base64-encoded PDF of the exam (if successful)

## `/auth_user` Endpoint

- **HTTP Method:** POST
- **Endpoint:** `/auth_user`

#### Description

This endpoint allows users to authenticate themselves by verifying their user identifier and authentication token. It checks whether the provided token is valid for the given user. If the authentication is successful, the endpoint returns a valid token message.

#### Request Parameters

- **user:** User identifier
- **token:** Authentication token

#### Response

- **result:** True if the authentication is successful; False otherwise
- **message:** Message indicating the result of the authentication
  - If authentication is successful, the message is "Valid token."
  - If authentication fails due to invalid parameters, the message is "Invalid parameters."
  - If authentication fails due to an invalid token, the message is "Invalid token."

#### Example Request

```json
POST /auth_user
{
  "user": "example_user",
  "token": "example_token"
}
```
# User Type API

This API endpoint allows you to retrieve the type of a user based on their input.

## Endpoint Details

- **URL:** `/get_user_type`
- **Method:** POST
- **Content-Type:** application/json

### Request Body

The request must include a JSON object with the following parameters:

- `user` (string, required): The user for whom you want to retrieve the type.
- `token` (string, required): Authentication token for accessing the API.

Example Request Body:

```json
{
  "user": "example_user",
  "token": "your_authentication_token"
}
```

# File Upload API

This API endpoint allows you to upload a file to the server, associating it with a user.

## Endpoint Details

- **URL:** `/uploadfile`
- **Method:** POST
- **Content-Type:** multipart/form-data

### Request Parameters

The request must include the following parameters:

- `file` (file, required): The file to be uploaded.
- `user` (string, required): The user associated with the uploaded file.

### Response

The API response is a JSON object with the following field:

- `message` (string): A message indicating the success of the file upload.

Example Response:

```json
{
  "message": "Archivo subido correctamente"
}
```
# Token Update API

This API endpoint allows you to update a user's token or credentials based on provided authentication.

## Endpoint Details

- **URL:** `/update_token`
- **Method:** POST
- **Content-Type:** application/json

### Request Body

The request must include a JSON object with the following parameters:

- `user` (string, required): The user for whom you want to update the token or credentials.
- `token` (string, required): The new token to be assigned to the user.
- `auth_token` (string, required): Authentication token for authorizing the update operation.

Example Request Body:

```json
{
  "user": "example_user",
  "token": "new_token_value",
  "auth_token": "your_authentication_token"
}```

