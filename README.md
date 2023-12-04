# FastAPI Documentation

This documentation outlines the available routes in the FastAPI. Ensure you have access to the proper documentation to understand how to use each route.

## Root Route
### `GET /`
- **Description:** Verify the status of the API.
- **Parameters:**
  - None.
- **Example Response:**
  ```json
  {"Status": "Running", "IP": "192.168.1.1"}
  ```

## Load Context
### `POST /load_context`
- **Description:** Loads documents and context for a user.
- **Request Parameters:**
  - `user` (string): The username.
- **Example Response:**
  ```json
  {"result": true, "message": "Documents loaded successfully"}
  ```

## Get Context
### `POST /context`
- **Description:** Obtains context for a user based on a request.
- **Request Parameters:**
  - `user` (string): The username.
  - `text` (string): The text of the request.
  - `token` (string): Authentication token.
- **Example Response:**
  ```json
  {"result": true, "message": "Context text obtained successfully"}
  ```

## Delete File
### `POST /delete_file`
- **Description:** Deletes a file uploaded by a user.
- **Request Parameters:**
  - `user` (string): The username.
  - `file` (string): Name of the file to delete.
  - `token` (string): Authentication token.
- **Example Response:**
  ```json
  true
  ```

## Upload File
### `POST /uploadfile`
- **Description:** Uploads a file to the system.
- **Request Parameters:**
  - `user` (string): The username.
  - `file` (file): File to upload.
- **Example Response:**
  ```json
  {"message": "File uploaded successfully"}
  ```

## Run the API
The FastAPI runs on port 8000. Ensure you start the API to use the routes described above.

```
uvicorn main:app --host 0.0.0.0 --port 8000
```
