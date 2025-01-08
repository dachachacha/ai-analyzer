# database.py

import asyncio
import time
from contextlib import asynccontextmanager

import weaviate
from weaviate.connect import ConnectionParams
from weaviate.exceptions import WeaviateStartUpError
from motor.motor_asyncio import AsyncIOMotorClient

from config import WEAVIATE_HOST, WEAVIATE_PORT, MONGO_URL, CLASS_NAME, OPENAI_API_KEY
from logging_config import setup_logging
from loguru import logger

from fastapi import Request

from utils.collection_names import get_mongo_chunk_hashes_collection_name, get_mongo_answers_collection_name

@asynccontextmanager
async def lifespan(app):
    # --- Startup ---
    # Initialize MongoDB client and store in app state
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.mongo_client = mongo_client
    app.state.db = mongo_client["ai_demo_db"]

    # Initialize MongoDB "projects" collection
    db = app.state.db
    projects_collection = db["projects"]

    # Create "projects" collection if it doesn't exist
    collections = await db.list_collection_names()
    if "projects" not in collections:
        await db.create_collection("projects")
        logger.info("Initialized 'projects' collection in MongoDB.")
    else:
        logger.info("'projects' collection already exists in MongoDB.")

    # Create indexes for the projects collection
    await projects_collection.create_index(
        [("normalized_name", 1)],
        unique=True,
        name="unique_project_name"
    )
    logger.info("Indexes created for 'projects' collection.")
    logger.info("MongoDB initialization completed successfully.")

    # Initialize Weaviate client
    while True:
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
            },
            skip_init_checks=False
        )

    # Wait for Weaviate to be ready
        try:
            logger.info("Trying to connect to Weaviate...")
            weaviate_client.connect()  # Call blocking method in a separate thread
            if weaviate_client.is_live():
                logger.info("Connected to Weaviate successfully.")
                break
            else:
                logger.warning("Weaviate not ready yet. Retrying in 1 second...")
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Error while connecting to Weaviate: {e}")
            logger.warning("Weaviate not ready yet. Retrying in 1 second...")
            #await asyncio.sleep(1)
            time.sleep(2)

    app.state.weaviate_client = weaviate_client

    yield  # Application is running

    # --- Shutdown ---
    # Close MongoDB client
    mongo_client.close()
    logger.info("MongoDB connection closed.")

    # Close Weaviate client
    weaviate_client.close()
    logger.info("Weaviate client closed.")

def get_db(request: Request) -> AsyncIOMotorClient:
    return request.app.state.mongo_client

