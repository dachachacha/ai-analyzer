# utils/collection_names.py

from config import CLASS_NAME
from utils.normalizer import normalize_project_name

def get_mongo_chunk_hashes_collection_name(project: str) -> str:
    """Generate the MongoDB chunk hashes collection name for a project."""
    normalized_name = normalize_project_name(project)
    return f"project_{normalized_name}_chunk_hashes"

def get_mongo_answers_collection_name(project: str) -> str:
    """Generate the MongoDB answers collection name for a project."""
    normalized_name = normalize_project_name(project)
    return f"project_{normalized_name}_answers"

def get_weaviate_class_name(project: str) -> str:
    """Generate the Weaviate class name for a project."""
    normalized_name = normalize_project_name(project)
    return f"{CLASS_NAME}_{normalized_name}"

