# main.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from config import CORS_ORIGINS, WEAVIATE_HOST, WEAVIATE_PORT, MONGO_URL, OPENAI_API_KEY
from logging_config import setup_logging
from database import lifespan
from routes import include_routers
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import json
from bson import ObjectId
from typing import Any

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

class CustomJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(content, cls=JSONEncoder).encode('utf-8')

# Load the OpenAI API key from file at startup
app = FastAPI(
    lifespan=lifespan,
    default_response_class=CustomJSONResponse
)

# Setup Logging
setup_logging()

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,            # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],                   # Allows all HTTP methods
    allow_headers=["*"],                   # Allows all headers
)

# Include Routers
include_routers(app)

