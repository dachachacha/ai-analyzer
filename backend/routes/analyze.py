# routes/analyze.py

import glob
import os
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Request, Body, Depends, HTTPException
from loguru import logger

from models import AnalyzeRequest, ProjectValidator
from utils import (
    chunk_file,
    calculate_hash,
    looks_like_binary,
    get_embedding,
    get_filtered_file_paths,
    get_mongo_chunk_hashes_collection_name,
    get_weaviate_class_name,
)
from utils.validators import validate_project


from database import get_db
from config import CLASS_NAME
import weaviate
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()

@router.post("/api/analyze")
async def analyze_code(
    request: Request,
    analyze_request: AnalyzeRequest = Body(...),
    project_data: dict = Depends(validate_project),
):
    base_folder = "codebase"
    folder_path = os.path.join(base_folder, project_data["folder"])

    logger.debug(f"Received request to analyze code for project: {project_data}")
    logger.debug(f"Using folder path: {folder_path}")

    db = request.app.state.db

    if not os.path.exists(folder_path):
        logger.error(f"Folder path '{folder_path}' does not exist.")
        raise HTTPException(status_code=400, detail=f"Folder path '{folder_path}' does not exist.")

    chunk_hashes_collection = get_mongo_chunk_hashes_collection_name(project_data['normalized_name'])
    weaviate_class_name = get_weaviate_class_name(project_data['normalized_name'])
    hashes_collection = db[chunk_hashes_collection]

    logger.debug(f"MongoDB chunk hashes collection: {chunk_hashes_collection}")
    logger.debug(f"Weaviate class name: {weaviate_class_name}")

    file_paths = get_filtered_file_paths(folder_path)
    logger.debug(f"Filtered file paths: {file_paths}")

    chunked_files = []
    ignored_files = []

    if not file_paths:
        logger.warning(f"No files found in {folder_path}.")
        return {"message": f"No files found in {folder_path}."}

    for fp in file_paths:
        logger.debug(f"Processing file: {fp}")
        try:
            _, ext = os.path.splitext(fp)
            if looks_like_binary(ext):
                logger.debug(f"File '{fp}' identified as binary and will be ignored.")
                ignored_files.append(fp)
                continue

            chunks = chunk_file(fp)
            logger.debug(f"Number of chunks generated for file '{fp}': {len(chunks)}")
            if not chunks:
                logger.debug(f"No chunks generated for file '{fp}'")
                ignored_files.append(fp)
                continue

            # Check for changes in chunk hashes
            file_changed = False
            for ch in chunks:
                text = ch["content"].strip()
                if not text:
                    logger.debug(f"Skipping empty chunk in file '{fp}'")
                    continue

                content_hash = calculate_hash(text)
                existing_hash = await hashes_collection.find_one({"filePath": ch["filePath"], "hash": content_hash})
                if not existing_hash:
                    file_changed = True
                    break

            if file_changed:
                # Delete all chunks for this file in Weaviate and MongoDB
                weaviate_client = request.app.state.weaviate_client
                chunk_collection = weaviate_client.collections.get(weaviate_class_name)

                logger.debug(f"Executing deletion for file '{fp}'.")
                response = chunk_collection.data.delete_many(
                    where=Filter.by_property(name="filePath").equal(fp)
                )
                await hashes_collection.delete_many({"filePath": fp})

                # Re-chunk the file and insert new chunks
                for ch in chunks:
                    text = ch["content"].strip()
                    if not text:
                        continue

                    content_hash = calculate_hash(text)
                    embedding = get_embedding(text)
                    logger.debug(f"Generated embedding for chunk in file '{fp}'")

                    data_object = {
                        "content": ch["content"],
                        "filePath": ch["filePath"],
                        "language": ch["language"],
                        "functionName": ch["functionName"],
                        "startLine": ch["startLine"],
                        "endLine": ch["endLine"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    chunk_collection.data.insert(properties=data_object, vector=embedding)
                    logger.debug(f"Inserted chunk into Weaviate for file '{fp}'")

                    await hashes_collection.update_one(
                        {"filePath": ch["filePath"], "hash": content_hash},
                        {"$set": {"hash": content_hash}},
                        upsert=True
                    )
                    logger.debug(f"Updated MongoDB for chunk in file '{fp}'")

                chunked_files.append(fp)
            else:
                logger.debug(f"No changes detected for file '{fp}'. Skipping re-chunking.")
                chunked_files.append(fp)

        except Exception as e:
            logger.error(f"Failed to process file '{fp}': {e}")
            ignored_files.append(fp)
            continue

    logger.info(f"Code analysis completed for project: {project_data['name']}")
    return {
        "message": "Code analysis completed.",
        "total_files": len(file_paths),
        "chunked_files": len(chunked_files),
        "ignored_files": len(ignored_files),
        "details": {"chunked": chunked_files, "ignored": ignored_files},
    }

