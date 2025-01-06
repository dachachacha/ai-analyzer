# config.py

import os
from pathlib import Path
from typing import Optional
from loguru import logger

WEAVIATE_HOST = os.environ.get("WEAVIATE_HOST", "localhost")
WEAVIATE_PORT = os.environ.get("WEAVIATE_PORT", "8080")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")

BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".ico", ".gif", ".pdf", ".zip",
    ".pyc", ".pkl", ".ds_store", ".exe", ".dll", ".so", ".docx"
}

CLASS_NAME = "CodeChunk"

# CORS Origins
CORS_ORIGINS = [
    "http://localhost:13000",
    "http://127.0.0.1:13000",
    # Add other origins if necessary
]


logger.info(f"loading key file: OPENAI_API_KEY_FILE")

secret_file = os.getenv("OPENAI_API_KEY_FILE")
if not secret_file:
    raise("OPENAI_API_KEY_FILE environment not found. Aborting.")
    
try:
    secret_path = Path(secret_file)
    if not secret_path.exists():
        raise(f"secret file {secret_file} doesn't exist. Aborting.")
        
    secret = secret_path.read_text().strip()
    OPENAI_API_KEY = secret
    os.environ["OPENAI_API_KEY"] = secret
    
except Exception as e:
    print(f"Error loading secret from {secret_file}: {e}")
