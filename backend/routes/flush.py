# routes/flush.py

from fastapi import APIRouter, Request, HTTPException
from loguru import logger

from config import CLASS_NAME
from utils.setup_weaviate_schema import setup_weaviate_schema
from database import get_db

router = APIRouter()

@router.post("/api/flush")
async def flush_databases(request: Request):
    """
    Remove and recreate the 'CodeChunk' collection in Weaviate.
    Drop the 'hashes' collection in MongoDB.
    """
    try:
        weaviate_client = request.app.state.weaviate_client
        existing_collections = weaviate_client.collections.list_all()
        if CLASS_NAME in existing_collections:
            setup_weaviate_schema(weaviate_client, delete=True)
    except Exception as e:
        logger.error(f"Failed to reset Weaviate collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset Weaviate collection.")

    try:
        # Drop the 'hashes' collection in MongoDB
        await request.app.state.chunk_hashes_collection.drop()
        logger.info("MongoDB 'hashes' collection dropped successfully.")
    except Exception as e:
        logger.error(f"Failed to drop 'hashes' collection in MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to drop MongoDB collection.")

    return {"message": "Weaviate and MongoDB data flushed successfully."}

