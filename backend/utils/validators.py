from fastapi import HTTPException, Depends, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from loguru import logger

from database import get_db
from utils.normalizer import normalize_project_name
from models import ProjectValidator, AnalyzeRequest

async def validate_project(
    request: Request,
    analyze_request: AnalyzeRequest,
    db: AsyncIOMotorClient = Depends(get_db)
) -> dict:
    """
    Validates the project parameter by checking its syntax and ensuring it exists in the database.

    Args:
        analyze_request (AnalyzeRequest): The request body containing the project name.
        db (AsyncIOMotorClient): The MongoDB client instance.

    Returns:
        dict: The full project metadata if valid.

    Raises:
        HTTPException: If the project is invalid or does not exist.
    """
    project = analyze_request.project
    logger.debug(f"Starting project validation for project: '{project}'")

    # Database validation
    try:
        logger.debug(f"Normalizing project name: '{project}'")
        normalized_name = normalize_project_name(project)
        logger.debug(f"Normalized project name: '{normalized_name}'")

        db = request.app.state.db
        projects_collection = db["projects"]
        logger.debug(f"Querying the database for project with normalized name: '{normalized_name}'")
        project_data = await projects_collection.find_one({"normalized_name": normalized_name})

        if not project_data:
            logger.warning(f"Project '{project}' not found in the database.")
            raise HTTPException(
                status_code=404, 
                detail=f"Project '{project}' not found."
            )
        
        logger.debug(f"Project '{project}' found in the database.")
        return project_data

    except HTTPException as he:
        # Re-raise HTTPExceptions to be handled by FastAPI
        logger.warning(f"HTTPException during database validation: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unexpected error during database validation for project '{project}': {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error during project validation."
        )

