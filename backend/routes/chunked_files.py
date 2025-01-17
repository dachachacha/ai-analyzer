# routes/chunked_files.py

from fastapi import APIRouter, Request, HTTPException
from loguru import logger
from utils import get_weaviate_class_name, normalize_project_name, get_mongo_chunk_hashes_collection_name
from weaviate.classes.query import Filter
from pydantic import BaseModel

router = APIRouter()

class FileDeleteRequest(BaseModel):
    project: str
    filePath: str

@router.get("/api/chunked-files")
async def get_chunked_files(request: Request, projectName: str):
    logger.debug(f"Received request to get chunked files for project: {projectName}")

    if not projectName or projectName == "undefined":
        logger.error("Project name is required but not provided.")
        raise HTTPException(status_code=400, detail="Project name is required.")

    try:
        project = normalize_project_name(projectName)
        logger.debug(f"Normalized project name: {project}")

        weaviate_class_name = get_weaviate_class_name(project)
        weaviate_client = request.app.state.weaviate_client
        chunk_collection = weaviate_client.collections.get(weaviate_class_name)

        # Query with grouping
        query = chunk_collection.aggregate.over_all(
            group_by="filePath",
            total_count=True
        )

        # Process results
        #logger.debug(f'query: {query}')
        grouped_results = query.groups

        # Prepare the list of files with their chunk counts
        files = [
            {
                "filePath": group.grouped_by.value,
                "chunkCount": group.total_count
            }
            for group in grouped_results
        ]

        #logger.debug(f"Retrieved chunked files: {files}")
        return {"files": files}

    except Exception as e:
        logger.error(f"Error retrieving chunked files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chunked files: {str(e)}")

@router.post("/api/delete-chunked-file")
async def delete_chunked_file(request: Request, data: FileDeleteRequest):
    project = data.project
    filePath = data.filePath
    logger.debug(f"Received request to delete chunked file: {filePath} for project: {project}")

    if not project or not filePath:
        logger.error("Project name and file path are required but not provided.")
        raise HTTPException(status_code=400, detail="Project name and file path are required.")

    try:
        project = normalize_project_name(project)
        file_path = filePath
        logger.debug(f"Normalized project name: {project}, file path: {file_path}")

        db = request.app.state.db

        hashes_collection_name = get_mongo_chunk_hashes_collection_name(project)
        hashes_collection = db[hashes_collection_name]

        weaviate_class_name = get_weaviate_class_name(project)
        logger.debug("Weaviate class name: " + weaviate_class_name)
        weaviate_client = request.app.state.weaviate_client
        chunk_collection = weaviate_client.collections.get(weaviate_class_name)

        logger.debug(f"Executing deletion.")
        response = chunk_collection.data.delete_many(
            where=Filter.by_property(name="filePath").equal(file_path)
        )

        await hashes_collection.delete_many({"filePath": filePath})

        logger.debug(response)
        message = f"Delete operation completed:\n" \
              f"- Found {response.matches} matching objects\n" \
              f"- Successfully deleted {response.successful} objects"
    
        if response.failed > 0:
            message += f"\n- Failed to delete {response.failed} objects"
        logger.debug(message)
        return {"message": message}

    except Exception as e:
        logger.error(f"Error during deletion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chunks: {str(e)}")
