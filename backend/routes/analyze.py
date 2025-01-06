# routes/analyze.py

import glob
import os
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Request, Body, Depends, HTTPException
from loguru import logger

from models import AnalyzeRequest
from utils import (
    chunk_file,
    calculate_hash,
    looks_like_binary,
    get_embedding,
    get_filtered_file_paths
)

from database import get_db
from config import CLASS_NAME
import weaviate
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()

@router.post("/api/analyze")
async def analyze_code_folder(
    request: Request, 
    body: Optional[AnalyzeRequest] = Body(None), 
    db: AsyncIOMotorClient = Depends(get_db)
):
    folder_path = body.folderPath if body and body.folderPath else 'codebase'
    file_paths = get_filtered_file_paths(folder_path)

    chunked_files = []
    ignored_files = []
    
    if not file_paths:
        logger.warning(f"No files found in {folder_path}.")
        return {"message": f"No files found in {folder_path}."}

    # Access the hashes collection in MongoDB
    logger.info("Accessing the hashes collection in MongoDB")
    hashes_collection = request.app.state.chunk_hashes_collection
    logger.info("Hashes collection accessed successfully.")

    for fp in file_paths:
        _, ext = os.path.splitext(fp)
        if looks_like_binary(ext):
            ignored_files.append(fp)
            continue
        chunks = chunk_file(fp)
        if chunks:
            chunked_files.append(fp)
        else:
            ignored_files.append(fp)
        logger.info(f"Processing chunks for: {fp}")
        for ch in chunks:
            text = ch["content"].strip()
            logger.info(f"##### CHUNK (length: {len(text.split(chr(10)))} lines) ####")
            logger.info(text)
            logger.info("##### END CHUNK ####")
            if not text:
                continue
            content_hash = calculate_hash(text)
            logger.info(f"Content hash: {content_hash}")
            # Check if the hash exists in the database
            existing_hash = await hashes_collection.find_one({"filePath": ch["filePath"], "hash": content_hash})
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
                weaviate_client = request.app.state.weaviate_client
                chunk_collection = weaviate_client.collections.get(CLASS_NAME)
                uuid = chunk_collection.data.insert(
                    properties=data_object,
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

