# routes/health.py

from fastapi import APIRouter, Request, HTTPException
from loguru import logger

router = APIRouter()

@router.get("/health")
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

