# database.py

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

from utils.setup_weaviate_schema import setup_weaviate_schema

@asynccontextmanager
async def lifespan(app):
    # --- Startup ---
    # Initialize MongoDB client and store in app state
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.mongo_client = mongo_client
    app.state.db = mongo_client["ai_demo_db"]
    app.state.answers_collection = app.state.db["answers"]
    app.state.chunk_hashes_collection = app.state.db["hashes"]
    await app.state.chunk_hashes_collection.create_index(
        [("filePath", 1), ("hash", 1)],
        unique=True,
        name="unique_chunk_identifier"
    )

    logger.info("MongoDB initialization completed successfully")

    # Initialize Weaviate client with original API calls
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
                """if weaviate_client.is_ready():
                    logger.info("Connected to Weaviate successfully.")
                    break
                else:
                    logger.warning("Weaviate not ready yet. Retrying in 1 second...")
                    time.sleep(1)"""
            except Exception as e:
                logger.warning(f"Caught error while connecting to Weaviate: {e}")
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

def get_db(request: Request) -> AsyncIOMotorClient:
    return request.app.state.mongo_client

