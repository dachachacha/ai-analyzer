# utils/embedding.py

from typing import List
from fastapi import HTTPException
from loguru import logger
from openai import OpenAI

openai_client = OpenAI()

def get_embedding(text: str) -> List[float]:
    return [0.1,1.0]
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding for text: {text[:30]}...")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail="Embedding generation failed.")

