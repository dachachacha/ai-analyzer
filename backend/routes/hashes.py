# routes/hashes.py

from fastapi import APIRouter, Request, HTTPException
from loguru import logger
from bson import ObjectId

router = APIRouter()

@router.get("/api/hashes")
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

