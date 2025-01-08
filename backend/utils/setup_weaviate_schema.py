# utils/setup_weaviate_schema.py

from weaviate import Client
from weaviate.classes.config import Configure, Property, DataType
from loguru import logger
#from config import CLASSNAME
from utils.collection_names import (
    get_weaviate_class_name,
)


def setup_weaviate_schema(weaviate_client: Client, project: str, delete: bool = False):
    """
    Create or recreate the 'CodeChunk' collection using Weaviate's Collections API.
    """
    existing_collections = weaviate_client.collections.list_all()
    class_name = get_weaviate_class_name(project)
    if class_name in existing_collections:
        if delete:
            logger.info(f"Collection '{class_name}' already exists. Deleting it for fresh setup.")
            weaviate_client.collections.delete(class_name)
        else:
            logger.info(f"Collection '{class_name}' already exists. Returning.")
            return
    logger.info(f"Creating collection '{class_name}'.")
    weaviate_client.collections.create(
        name=class_name,
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
    logger.info(f"Collection '{class_name}' created successfully.")

