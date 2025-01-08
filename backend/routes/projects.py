from fastapi import APIRouter, Request, HTTPException, Body
from typing import List
from loguru import logger
from utils.collection_names import (
    get_mongo_chunk_hashes_collection_name,
    get_mongo_answers_collection_name,
    get_weaviate_class_name,
    normalize_project_name,
)
from utils.setup_weaviate_schema import setup_weaviate_schema
from models import ProjectDeleteRequest

router = APIRouter()

@router.get("/api/projects")
async def get_projects(request: Request):
    """Fetch all projects."""
    try:
        logger.debug("Fetching all projects.")
        db = request.app.state.db
        projects_collection = db["projects"]

        # Fetch all projects from the "projects" collection
        projects = await projects_collection.find({}, {"_id": 0}).to_list(length=None)
        logger.debug(f"Fetched projects: {projects}")

        return {"projects": projects}
    except Exception as e:
        logger.error(f"Failed to fetch projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch projects.")


@router.post("/api/projects")
async def create_project(
    request: Request, 
    name: str = Body(...), 
    folder: str = Body(...)
):
    """Create a new project."""
    try:
        logger.debug(f"Creating project with name: {name} and folder: {folder}")
        normalized_name = normalize_project_name(name)
        chunk_hashes_collection = get_mongo_chunk_hashes_collection_name(normalized_name)
        answers_collection = get_mongo_answers_collection_name(normalized_name)
        weaviate_class_name = get_weaviate_class_name(normalized_name)

        db = request.app.state.db
        collections = await db.list_collection_names()
        logger.debug(f"Existing MongoDB collections: {collections}")

        # Check if the project already exists in the "projects" collection
        projects_collection = db["projects"]
        existing_project = await projects_collection.find_one({"normalized_name": normalized_name})
        if existing_project:
            logger.warning(f"Project '{name}' already exists.")
            raise HTTPException(status_code=400, detail="Project already exists.")

        # Handle inconsistent state where collections exist but the project is not recorded
        if chunk_hashes_collection in collections or answers_collection in collections:
            logger.warning(f"Inconsistent state detected: Collections for project '{name}' exist, "
                           f"but the project is not recorded in 'projects'. Cleaning up.")
            await db[chunk_hashes_collection].drop()
            await db[answers_collection].drop()
            logger.info(f"Existing collections for project '{name}' have been cleaned up.")

        # Create the MongoDB collections for the project
        await db.create_collection(chunk_hashes_collection)
        await db.create_collection(answers_collection)
        logger.debug(f"MongoDB collections created for project '{name}'.")

        # Initialize the Weaviate schema for the project
        weaviate_client = request.app.state.weaviate_client
        setup_weaviate_schema(weaviate_client, project=normalized_name, delete=False)
        logger.info(f"Weaviate schema initialized for project '{name}'.")

        # Store the project in the "projects" collection
        project_data = {
            "name": name,
            "normalized_name": normalized_name,
            "folder": folder,
        }
        await projects_collection.insert_one(project_data)
        logger.info(f"Project '{name}' successfully created.")

        return {"message": f"Project '{name}' created successfully."}
    except Exception as e:
        print(e)
        logger.error(f"Failed to create project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create project.")


@router.delete("/api/projects")
async def delete_project(request: Request, name: str = Body(..., embed=True)):
    """Delete a project."""
    try:
        logger.debug(f"Deleting project with name: {name}")
        normalized_name = normalize_project_name(name)
        chunk_hashes_collection = get_mongo_chunk_hashes_collection_name(normalized_name)
        answers_collection = get_mongo_answers_collection_name(normalized_name)
        weaviate_class_name = get_weaviate_class_name(normalized_name)

        db = request.app.state.db

        # Drop the collections for the project
        await db[chunk_hashes_collection].drop()
        await db[answers_collection].drop()
        logger.debug(f"MongoDB collections dropped for project '{name}'.")

        # Delete the Weaviate collection for the project
        weaviate_client = request.app.state.weaviate_client
        existing_classes = weaviate_client.collections.list_all()
        if weaviate_class_name in existing_classes:
            weaviate_client.collections.delete(weaviate_class_name)
            logger.info(f"Weaviate collection '{weaviate_class_name}' deleted.")

        # Remove the project from the "projects" collection
        projects_collection = db["projects"]
        delete_result = await projects_collection.delete_one({"normalized_name": normalized_name})
        if delete_result.deleted_count == 0:
            logger.warning(f"Project '{name}' not found.")
            raise HTTPException(status_code=404, detail="Project not found.")

        logger.info(f"Project '{name}' successfully deleted.")
        return {"message": f"Project '{name}' deleted successfully."}
    except Exception as e:
        logger.error(f"Failed to delete project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete project.")


@router.delete("/api/projects/all")
async def delete_all_projects(request: Request):
    """Delete all projects."""
    try:
        logger.debug("Deleting all projects and their resources.")
        db = request.app.state.db
        projects_collection = db["projects"]

        # Fetch all projects from the "projects" collection
        projects = await projects_collection.find({}, {"normalized_name": 1}).to_list(length=None)
        logger.debug(f"Projects to delete: {projects}")

        if not projects:
            logger.info("No projects to delete.")
            return {"message": "No projects to delete."}

        # Iterate through all projects and delete their resources
        weaviate_client = request.app.state.weaviate_client
        for project in projects:
            normalized_name = project["normalized_name"]
            chunk_hashes_collection = get_mongo_chunk_hashes_collection_name(normalized_name)
            answers_collection = get_mongo_answers_collection_name(normalized_name)
            weaviate_class_name = get_weaviate_class_name(normalized_name)

            # Drop MongoDB collections
            await db[chunk_hashes_collection].drop()
            await db[answers_collection].drop()
            logger.debug(f"Dropped MongoDB collections for project '{normalized_name}'.")

            # Delete Weaviate collection
            existing_classes = weaviate_client.collections.list_all()
            if weaviate_class_name in existing_classes:
                weaviate_client.collections.delete(weaviate_class_name)
                logger.info(f"Weaviate collection '{weaviate_class_name}' deleted.")

        # Clear the "projects" collection
        await projects_collection.delete_many({})
        logger.info("All projects and their resources have been deleted.")
        return {"message": "All projects and their resources have been deleted."}
    except Exception as e:
        logger.error(f"Failed to delete all projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete all projects.")

