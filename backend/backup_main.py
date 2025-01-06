import os
import sys
import re
import glob
import ast
import openai
import json
import hashlib
from datetime import datetime
from bson import ObjectId
from typing import List, Optional, Any
from openai import OpenAI
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time

import weaviate
from weaviate.connect import ConnectionParams
from weaviate.exceptions import WeaviateStartUpError
#from weaviate.collections import CollectionConfig
from weaviate.classes.config import Configure, Property, DataType

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection

from fastapi.middleware.cors import CORSMiddleware

from weaviate.classes.query import MetadataQuery

from loguru import logger
import sys
from contextlib import asynccontextmanager

from fastapi import Body


openai_client = OpenAI()
# --- Logging Configuration ---
logger.remove()  # Remove default handlers
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")

# --- Environment / Config ---
WEAVIATE_HOST = os.environ.get("WEAVIATE_HOST", "localhost")
WEAVIATE_PORT = os.environ.get("WEAVIATE_PORT", "8080")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY env var not found. Cannot proceed.")

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

class CustomJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(content, cls=JSONEncoder).encode('utf-8')

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Initialize MongoDB client and store in app state
    mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://mongo:27017"))
    app.state.mongo_client = mongo_client
    app.state.db = mongo_client["ai_demo_db"]
    app.state.answers_collection = app.state.db["answers"]
    app.state.chunk_hashes_collection = app.state.db["hashes"]
    await app.state.chunk_hashes_collection.create_index(
            [ ("filePath", 1), ("hash", 1) ],
            unique=True,
            name="unique_chunk_identifier"
        )

    logger.info("MongoDB initialization completed successfully")

    # Initialize Weaviate client
    try:
        weaviate_client = weaviate.WeaviateClient(
            connection_params=ConnectionParams.from_params(
                http_host=WEAVIATE_HOST,
                http_port=WEAVIATE_PORT,
                http_secure=False,
                grpc_host=WEAVIATE_HOST,
                grpc_port=50051,
                grpc_secure=False,
            ),
            additional_headers={
                "X-OpenAI-Api-Key": OPENAI_API_KEY
            }
        )
        # Attempt connecting in a loop until successful
        while True:
            try:
                logger.info("Trying to connect to Weaviate...")
                weaviate_client.connect()
                break
                '''if weaviate_client.is_ready():
                    logger.info("Connected to Weaviate successfully.")
                    break
                else:
                    time.sleep(1)
                    continue'''
            except Exception as e:
                logger.warning("caught error" + str(e))
                logger.warning("Weaviate not ready yet. Retrying in 1 second...")
                time.sleep(1)
        app.state.weaviate_client = weaviate_client
    except WeaviateStartUpError as e:
        logger.error(f"Error starting Weaviate client: {e}")
        raise

    # Initialize Weaviate schema
    try:
        setup_weaviate_schema(app.state.weaviate_client, delete=False)
    except Exception as e:
        logger.error(f"Failed to set up Weaviate schema: {e}")
        raise

    yield  # Application is running

    # --- Shutdown ---
    # Close MongoDB client
    mongo_client.close()
    logger.info("MongoDB connection closed.")

    # Close Weaviate client
    weaviate_client.close()
    logger.info("Weaviate client closed.")

# --- FastAPI Initialization with Lifespan ---
app = FastAPI(lifespan=lifespan, default_response_class=CustomJSONResponse)

# --- CORS Configuration ---
origins = [
    "http://localhost:13000",  # Frontend URL
    "http://127.0.0.1:13000",
    # Add other origins if necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],              # Allows all HTTP methods
    allow_headers=["*"],              # Allows all headers
)

# --- Pydantic Models ---
class AnalyzeRequest(BaseModel):
    folderPath: Optional[str] = None

class QueryRequest(BaseModel):
    query: str

# --- Hashing Helper ---
def calculate_hash(content: str) -> str:
    """Calculate SHA-256 hash of a string."""
    import hashlib
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

# --- Embedding Helper ---
def get_embedding(text: str) -> List[float]:
    #logger.info("getting embedding for: " + text)
    return [1.0,0.1]
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )

        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding for text: {text[:30]}...")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail="Embedding generation failed.")

# --- Binary File Check ---
BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".ico", ".gif", ".pdf", ".zip",
    ".pyc", ".pkl", ".ds_store", ".exe", ".dll", ".so", ".docx"
}

def chunk_file(file_path: str):
    _, ext = os.path.splitext(file_path)

    if looks_like_binary(ext):
        logger.info(f"Skipping binary file: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

    lines = content.split("\n")
    language_label = (
        "Markdown" if ext == ".md" else
        "Python" if ext == ".py" else
        "JavaScript" if ext in (".js", ".jsx", ".mjs", ".ts", ".cjs") else
        ext[1:].lower() or "unknown"
    )

    if ext == ".md":
        return chunk_markdown(lines, language_label, file_path)
    elif ext == ".py":
        return chunk_python_file(content, file_path, language_label)
    elif ext in (".js", ".jsx", ".mjs", ".cjs", ".ts"):
        return chunk_code_file(content, file_path, language_label)
    else:
        return chunk_by_lines(lines, 200, language_label, file_path)  # Increased max_lines for other file types

def chunk_markdown(lines, language_label, file_path, max_lines=200, min_lines=50):
    chunks = []
    current_chunk = []
    start_line = 0

    for i, line in enumerate(lines):
        if re.match(r"^#{1,6} ", line):  # Match Markdown headings
            if current_chunk and len(current_chunk) >= min_lines:
                chunks.append({
                    "content": "\n".join(current_chunk),
                    "functionName": None,
                    "startLine": start_line,
                    "endLine": i - 1,
                    "filePath": file_path,
                    "language": language_label
                })
                current_chunk = [line]
                start_line = i
            else:
                current_chunk.append(line)
        else:
            current_chunk.append(line)

        # Check max lines for the current chunk
        if len(current_chunk) >= max_lines:
            chunks.append({
                "content": "\n".join(current_chunk),
                "functionName": None,
                "startLine": start_line,
                "endLine": i,
                "filePath": file_path,
                "language": language_label
            })
            current_chunk = []
            start_line = i + 1

    # Add the final chunk
    if current_chunk:
        chunks.append({
            "content": "\n".join(current_chunk),
            "functionName": None,
            "startLine": start_line,
            "endLine": len(lines) - 1,
            "filePath": file_path,
            "language": language_label
        })

    return chunks

def chunk_python_file(content, file_path, language_label, max_lines=200, min_lines=50):
    function_chunks = parse_python_functions(content)
    if not function_chunks:
        logger.info(f"No Python functions found in {file_path}. Using line-based chunking.")
        return chunk_by_lines(content.split("\n"), max_lines, language_label, file_path)

    chunks = []
    current_chunk = []
    start_line = 0

    for fc in function_chunks:
        func_lines = fc["chunk_text"].split("\n")
        if current_chunk and (len(current_chunk) + len(func_lines)) > max_lines:
            chunks.append({
                "content": "\n".join(current_chunk),
                "functionName": None,
                "startLine": start_line,
                "endLine": fc["start_line"] - 1,
                "filePath": file_path,
                "language": language_label
            })
            current_chunk = []
            start_line = fc["start_line"]

        current_chunk.extend(func_lines)

    if current_chunk:
        chunks.append({
            "content": "\n".join(current_chunk),
            "functionName": None,
            "startLine": start_line,
            "endLine": function_chunks[-1]["end_line"],
            "filePath": file_path,
            "language": language_label
        })

    return chunks

def chunk_code_file(content, file_path, language_label, max_lines=200, min_lines=50):
    lines = content.split("\n")
    return chunk_by_lines(lines, max_lines, language_label, file_path, min_lines=min_lines)

def chunk_by_lines(lines, max_lines, language_label, file_path, min_lines=50):
    chunks = []
    current_chunk = []
    start_line = 0

    for i, line in enumerate(lines):
        current_chunk.append(line)

        if len(current_chunk) >= max_lines:
            chunks.append({
                "content": "\n".join(current_chunk),
                "functionName": None,
                "startLine": start_line,
                "endLine": i,
                "filePath": file_path,
                "language": language_label
            })
            current_chunk = []
            start_line = i + 1

    # Handle remaining lines
    if current_chunk:
        if len(current_chunk) >= min_lines or not chunks:
            chunks.append({
                "content": "\n".join(current_chunk),
                "functionName": None,
                "startLine": start_line,
                "endLine": len(lines) - 1,
                "filePath": file_path,
                "language": language_label
            })
        else:
            if chunks:
                # Merge with the previous chunk if too small
                chunks[-1]["content"] += "\n" + "\n".join(current_chunk)
                chunks[-1]["endLine"] = len(lines) - 1
            else:
                chunks.append({
                    "content": "\n".join(current_chunk),
                    "functionName": None,
                    "startLine": start_line,
                    "endLine": len(lines) - 1,
                    "filePath": file_path,
                    "language": language_label
                })

    return chunks

def looks_like_binary(ext):
    binary_extensions = {'.exe', '.bin', '.dll', '.so', '.jpg', '.png', '.gif', '.pdf', '.zip'}
    return ext.lower() in binary_extensions

def parse_python_functions(content):
    """
    Parses Python functions from the content and returns a list of dictionaries
    with function details.
    This is a simplistic parser; consider using ast or other parsing libraries for robustness.
    """
    function_pattern = re.compile(r'^def\s+(\w+)\s*\(.*?\):', re.MULTILINE)
    functions = []
    for match in function_pattern.finditer(content):
        func_name = match.group(1)
        start = match.start()
        start_line = content.count('\n', 0, start)
        # Attempt to find the end of the function by indentation
        lines = content[start:].split('\n')
        func_body = [lines[0]]
        for line in lines[1:]:
            if line.startswith((' ', '\t')):
                func_body.append(line)
            else:
                break
        end_line = start_line + len(func_body) - 1
        functions.append({
            "function_name": func_name,
            "chunk_text": "\n".join(func_body),
            "start_line": start_line,
            "end_line": end_line
        })
    return functions

# --- Weaviate Schema Setup ---
CLASS_NAME = "CodeChunk"

def setup_weaviate_schema(weaviate_client: weaviate.Client, delete = False):
    """
    Create or recreate the 'CodeChunk' collection using Weaviate's Collections API.
    """
    existing_collections = weaviate_client.collections.list_all()
    if CLASS_NAME in existing_collections:
        if delete:
            logger.info(f"Collection '{CLASS_NAME}' already exists. Deleting it for fresh setup.")
            weaviate_client.collections.delete(CLASS_NAME)
        else:
            logger.info(f"Collection '{CLASS_NAME}' already exists. Returning.")
            return
    logger.info(f"Creating collection '{CLASS_NAME}'.")
    weaviate_client.collections.create(
        name=CLASS_NAME,
        description="Store code chunks and their embeddings",
        vectorizer_config=Configure.Vectorizer.text2vec_openai(),
        properties=[
            Property(name="content", data_type=DataType.TEXT),
            Property(name="filePath", data_type=DataType.TEXT),
            Property(name="language", data_type=DataType.TEXT),
            Property(name="functionName", data_type=DataType.TEXT),
            Property(name="startLine", data_type=DataType.INT),
            Property(name="endLine", data_type=DataType.INT),
        ]
    )
    logger.info(f"Collection '{CLASS_NAME}' created successfully.")

# --- Dependency Injection for MongoDB ---
def get_db(request: Request) -> AsyncIOMotorClient:
    return request.app.state.mongo_client

def get_answers_collection(request: Request):
    return request.app.state.answers_collection

async def is_hash_stored(collection, file_path: str, chunk_hash: str) -> bool:
    result = await collection.find_one({"file_path": file_path, "hash": chunk_hash})
    return result is not None

# --- FastAPI Routes ---
@app.post("/api/analyze")
async def analyze_code_folder(
    request: Request, 
    body: Optional[AnalyzeRequest] = Body(None), 
    db: AsyncIOMotorClient = Depends(get_db)
):
    folder_path = 'codebase'
    file_paths = [
        fp for fp in glob.glob(os.path.join(folder_path, "**/*.*"), recursive=True)
        if os.path.isfile(fp)
    ]
    chunked_files = []
    ignored_files = []
    
    hashes = []

    if not file_paths:
        logger.warning(f"No files found in {folder_path}.")
        return {"message": f"No files found in {folder_path}."}

    # Access the hashes collection in MongoDB
    logger.info("opening the hashes db")
    hashes_collection = app.state.chunk_hashes_collection
    logger.info("opening the hashes db: " + str(hashes_collection))


    for fp in file_paths:
        #fp = os.path.abspath(fp)
        _, ext = os.path.splitext(fp)
        if looks_like_binary(ext):
            ignored_files.append(fp)
            continue
        chunks = chunk_file(fp)
        if chunks:
            chunked_files.append(fp)
        else:
            ignored_files.append(fp)
        logger.info("processing chunks for: " + fp)
        for ch in chunks:
            text = ch["content"].strip()
            logger.info("##### CHUNK (length: {}) ####".format(len(text.split("\n"))))
            logger.info(text)
            logger.info("##### END CHUNK ####")
            if not text:
                continue
            content_hash = calculate_hash(text)
            if content_hash in hashes:
                logger.error("Found a hash duplicate for file: " + fp)
            #logger.info("file path: " + ch["filePath"])
            logger.info("content hash: " + str(content_hash))
            # Check if the hash exists in the database
            existing_hash = await hashes_collection.find_one({"filePath": ch["filePath"], "hash": content_hash})
            #existing_hash = await hashes_collection.find_one({"filePath": ch["filePath"], "hash": content_hash})
            logger.info(f"Query result for {ch['filePath']}: {existing_hash}")
            if existing_hash:
                logger.info(f"Skipping unchanged chunk: {ch['filePath']}")
                continue
            embedding = get_embedding(text)
            data_object = {
                "content": ch["content"],
                "filePath": ch["filePath"],
                "language": ch["language"],
                "functionName": ch["functionName"],
                "startLine": ch["startLine"],
                "endLine": ch["endLine"],
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                logger.info(f"Saving chunk for {ch['filePath']}")
                chunk_collection = request.app.state.weaviate_client.collections.get(CLASS_NAME)
                uuid = chunk_collection.data.insert(
                        properties = data_object,
                        vector=embedding
                    )
                logger.info(f"Hash inserted/updated for {ch['filePath']}")
                # Update MongoDB with the new hash
                await hashes_collection.update_one(
                    {"filePath": ch["filePath"], "hash": content_hash},
                    {"$set": {"hash": content_hash}},
                    upsert=True
                )
                logger.debug(f"Stored chunk in Weaviate and updated hash: {ch['filePath']}")
            except Exception as e:
                logger.error(f"Failed to store chunk in Weaviate: {e}")

    logger.info("Code analysis completed.")
    return {"message": "Code analysis completed.", "chunked": chunked_files, "ignored": ignored_files}

def sanitize_keys(data):
    """Recursively sanitize keys in a dictionary to remove MongoDB reserved characters."""
    if isinstance(data, dict):
        return {key.replace('.', '_').replace('$', '_'): sanitize_keys(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_keys(item) for item in data]
    return data


async def summarize_interactions(collection, max_literal=2, max_total=10):
    """
    Summarize the last `max_total` interactions, keeping the last `max_literal`
    interactions literal and summarizing the rest.

    Args:
        collection: The MongoDB collection containing the query history.
        max_literal: Number of most recent interactions to include as-is.
        max_total: Total number of interactions to process.

    Returns:
        A formatted string with the last `max_literal` interactions literal
        and earlier interactions summarized.
    """
    # Fetch the last `max_total` interactions
    recent_history = await collection.find(
        {},
        {"_id": 0, "query": 1, "answer": 1}
    ).sort("timestamp", -1).limit(max_total).to_list(length=max_total)

    if not recent_history:
        return "No previous interactions available."

    # Split history into literal and to summarize
    literal_history = recent_history[:max_literal]
    to_summarize = recent_history[max_literal:]

    # Format the literal history
    literal_formatted = "\n".join(
        [f"{i + 1}. Query: {entry['query']}\n   Answer: {entry['answer']}" for i, entry in enumerate(literal_history)]
    )

    # Summarize the rest using OpenAI
    if to_summarize:
        summarize_prompt = "\n".join(
            [f"Query: {entry['query']}\nAnswer: {entry['answer']}" for entry in to_summarize]
        )
        try:
            summary_response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Summarize these interactions:\n{summarize_prompt}"}],
                temperature=0.0,
                max_tokens=400
            )
            summary = summary_response.choices[0].message["content"].strip()
        except Exception as e:
            summary = f"Error summarizing interactions: {e}"
    else:
        summary = "No earlier interactions available."

    # Combine literal and summarized history
    combined_history = f"""
Previous Interactions:

Literal History:
{literal_formatted}

Summarized History:
{summary}
    """
    return combined_history

@app.post("/api/query")
async def query_ai(
    request: Request, 
    body: QueryRequest,
    db: AsyncIOMotorClient = Depends(get_db)
):
    user_query = body.query
    if not user_query.strip():
        logger.warning("Empty query received.")
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        query_emb = get_embedding(user_query)
    except HTTPException as e:
        logger.error(f"Embedding generation failed: {e.detail}")
        raise

    # Query top 5 similar code chunks
    try:
        chunk_collection = request.app.state.weaviate_client.collections.get(CLASS_NAME)
        result = chunk_collection.query.near_vector (
                near_vector = query_emb,
                limit = 10,
                return_metadata=MetadataQuery(distance=True)
            )
        logger.debug("Weaviate query executed successfully.")
    except Exception as e:
        logger.error(f"Weaviate query failed: {e}")
        raise HTTPException(status_code=500, detail="Weaviate query failed.")

    retrieved_chunks = []

    for item in result.objects:
        rec = {
            "file": item.properties["filePath"],
            "lines": f"{item.properties['startLine']}-{item.properties['endLine']}",
            "content": item.properties["content"],
        }
        retrieved_chunks.append(rec)

    if not retrieved_chunks:
        logger.info("No relevant code chunks found for the query.")
        return {"answer": "No relevant code chunks found for your query."}

    # Convert chunks to a formatted string
    formatted_chunks = [
        f"File: {chunk['file']}\nLines: {chunk['lines']}\nContent:\n{chunk['content']}"
        for chunk in retrieved_chunks
    ]

    # Limit context to prevent exceeding token limits
    context = []
    token_count = 0
    max_token_length = 3000

    for chunk in formatted_chunks:
        token_count += len(chunk.split())
        if token_count < max_token_length:
            context.append(chunk)
        else:
            break

    summary = await summarize_interactions(request.app.state.answers_collection)
    context.append(summary)
    context_str = "\n---\n".join(context)
    prompt = f"Context:\n{context_str}\n\nQuestion: {user_query}\nAnswer:"

    logger.info("prompt: " + prompt)

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"user","content":prompt}],
            temperature=0.0,
            max_tokens=5000
        )
        ai_answer = completion.choices[0].message.content.strip()
        logger.info("AI responded successfully.")
    except Exception as e:
        ai_answer = f"Error calling OpenAI: {e}"
        logger.error(f"OpenAI API call failed: {e}")

    doc = {
        "query": user_query,
        "answer": ai_answer,
        "timestamp": datetime.utcnow()
    }

    # Sanitize the document before storing
    sanitized_doc = sanitize_keys(doc)

    try:
        # Insert the sanitized document into MongoDB
        await request.app.state.answers_collection.insert_one(sanitized_doc)
        logger.debug("Sanitized Q&A stored in MongoDB.")
    except Exception as e:
        logger.error(f"Failed to store Q&A in MongoDB: {e}")

    return {"answer": ai_answer}


@app.post("/api/flush")
async def flush_databases(request: Request):
    """
    Remove and recreate the 'CodeChunk' collection in Weaviate.
    Drop the 'answers' collection in MongoDB.
    """
    try:
        existing_collections = request.app.state.weaviate_client.collections.list_all()
        if CLASS_NAME in existing_collections:
            setup_weaviate_schema(request.app.state.weaviate_client, delete=True)

    except Exception as e:
        logger.error(f"Failed to reset Weaviate collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset Weaviate collection.")

    try:
        #await request.app.state.answers_collection.drop()
        await request.app.state.chunk_hashes_collection.drop()
        logger.info("MongoDB 'hashes' collection dropped successfully.")
    except Exception as e:
        logger.error(f"Failed to drop 'hashes' collection in MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to drop MongoDB collection.")
    return {"message": "Weaviate and MongoDB data flushed successfully."}

@app.get("/health")
async def health_check(request: Request):
    try:
        weaviate_client = request.app.state.weaviate_client
        weaviate_client.ping()
        answers_collection = request.app.state.answers_collection
        await answers_collection.estimated_document_count()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy.")


@app.get("/api/hashes")
async def list_stored_hashes(request: Request):
    try:
        # Count the total number of documents in the collection
        total_count = await request.app.state.chunk_hashes_collection.count_documents({})
        logger.info(f"Total number of records in the hashes collection: {total_count}")

        # Retrieve hashes from the collection
        hashes = await request.app.state.chunk_hashes_collection.find().to_list(length=1000)
        
        # Convert ObjectId to string for each document
        for hash_doc in hashes:
            if '_id' in hash_doc and isinstance(hash_doc['_id'], ObjectId):
                hash_doc['_id'] = str(hash_doc['_id'])
        
        logger.debug(f"Retrieved hashes: {len(hashes)} items")
        return {"hashes": hashes}
    except Exception as e:
        logger.error(f"Failed to list hashes: {e}")
        raise HTTPException(status_code=500, detail="Failed to list hashes.")

@app.get("/api/history")
async def get_query_history(request: Request, limit: int = 10, skip: int = 0):
    """
    Fetch query history from the database with optional pagination.

    Args:
        request: FastAPI request object.
        limit (int): The maximum number of records to return. Default is 10.
        skip (int): The number of records to skip for pagination. Default is 0.

    Returns:
        List[dict]: A list of query history records.
    """
    try:
        # Access the MongoDB collection
        collection = request.app.state.answers_collection

        # Query the collection with pagination
        cursor = collection.find().sort("timestamp", -1).skip(skip).limit(limit)
        history = await cursor.to_list(length=limit)

        # Format the records to ensure JSON serialization compatibility
        formatted_history = [
            {
                "query": record.get("query"),
                "answer": record.get("answer"),
                "timestamp": record.get("timestamp").isoformat() if record.get("timestamp") else None,
            }
            for record in history
        ]

        return formatted_history

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
