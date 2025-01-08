# routes/history.py

from fastapi import APIRouter, Request, HTTPException
from typing import List
from loguru import logger
from datetime import datetime
from utils import (
    get_mongo_answers_collection_name,
)


router = APIRouter()

@router.get("/api/history")
async def get_query_history(request: Request, project: str, limit: int = 10, skip: int = 0):
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
        answers_collection = get_mongo_answers_collection_name(project)
        collection = request.app.state.db[answers_collection]
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
        logger.error(f"Failed to fetch query history: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

