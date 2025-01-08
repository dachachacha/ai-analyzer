# routes/flush.py

from fastapi import APIRouter, Request, Body, Depends, HTTPException
from loguru import logger

from config import CLASS_NAME
from utils import (
    setup_weaviate_schema,
    get_mongo_chunk_hashes_collection_name,
    get_weaviate_class_name,
)
from utils.validators import validate_project
from database import get_db

router = APIRouter()

@router.post("/api/flush")
async def flush_databases(
    request: Request,
    project_data: dict = Depends(validate_project),
):
    """
    Remove and recreate the 'CodeChunk' collection in Weaviate.
    Drop the 'hashes' collection in MongoDB.
    """
    try:
        weaviate_class_name = get_weaviate_class_name(project_data['normalized_name'])
        weaviate_client = request.app.state.weaviate_client
        logger.debug(f"Trying to reset collection '{weaviate_class_name}'")
        if weaviate_class_name in weaviate_client.collections.list_all():
            weaviate_client.collections.delete(weaviate_class_name)
    except Exception as e:
        logger.error(f"Failed to reset Weaviate collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset Weaviate collection.")

    try:
        # Drop the 'hashes' collection in MongoDB
        chunk_hashes_collection = get_mongo_chunk_hashes_collection_name(project_data['normalized_name'])
        db = request.app.state.db
        await db[chunk_hashes_collection].drop()
        await db.create_collection(chunk_hashes_collection)
        logger.info("MongoDB 'hashes' collection dropped successfully.")
    except Exception as e:
        logger.error(f"Failed to drop 'hashes' collection in MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to drop MongoDB collection.")

    return {"message": "Weaviate and MongoDB data flushed successfully."}

