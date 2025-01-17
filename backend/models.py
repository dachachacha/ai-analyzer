# models.py

from pydantic import BaseModel, validator
from typing import Optional

class AnalyzeRequest(BaseModel):
    project: str

class QuerySettings(BaseModel):
    querySettings: dict
    historySummarizerSettings: dict

class QueryRequest(BaseModel):
    query: str
    project: str
    settings: QuerySettings

class ProjectDeleteRequest(BaseModel):
    name: str

class ProjectValidator(BaseModel):
    project: str

    @validator("project")
    def validate_project_name(cls, value):
        if not value.isidentifier():  # Ensures the project name is a valid identifier
            raise ValueError("Project name must be a valid identifier (alphanumeric and underscores).")
        if len(value) > 50:  # Example: Limit length to 50 characters
            raise ValueError("Project name must not exceed 50 characters.")
        return value
