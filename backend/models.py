# models.py

from pydantic import BaseModel
from typing import Optional

class AnalyzeRequest(BaseModel):
    folderPath: Optional[str] = None

class QueryRequest(BaseModel):
    query: str

