# utils/setup_weaviate_schema.py

from weaviate import Client
from weaviate.classes.config import Configure, Property, DataType
from loguru import logger
from config import CLASS_NAME

def setup_weaviate_schema(weaviate_client: Client, delete: bool = False):
    """
    Create or recreate the 'CodeChunk' collection using Weaviate's Collections API.
    """
    existing_collections = weaviate_client.collections.list_all()
    if CLASS_NAME in existing_collections:
        if delete:
            logger.info(f"Collection '{CLASS_NAME}' already exists. Deleting it for fresh setup.")
            weaviate_client.collections.delete(CLASS_NAME)
        else:
            logger.info(f"Collection '{CLASS_NAME}' already exists. Returning.")
            return
    logger.info(f"Creating collection '{CLASS_NAME}'.")
    weaviate_client.collections.create(
        name=CLASS_NAME,
        description="Store code chunks and their embeddings",
        vectorizer_config=Configure.Vectorizer.text2vec_openai(),
        properties=[
            Property(name="content", data_type=DataType.TEXT),
            Property(name="filePath", data_type=DataType.TEXT),
            Property(name="language", data_type=DataType.TEXT),
            Property(name="functionName", data_type=DataType.TEXT),
            Property(name="startLine", data_type=DataType.INT),
            Property(name="endLine", data_type=DataType.INT),
        ]
    )
    logger.info(f"Collection '{CLASS_NAME}' created successfully.")

