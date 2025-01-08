from typing import List
from fastapi import APIRouter, Request, Depends, HTTPException
from loguru import logger
from datetime import datetime
from pydantic import BaseModel
from tiktoken import encoding_for_model

from models import QueryRequest
from utils import (
    get_embedding,
    summarize_interactions,
    sanitize_keys,
    get_mongo_chunk_hashes_collection_name,
    get_mongo_answers_collection_name,
    get_weaviate_class_name,
    normalize_project_name,
)
from database import get_db

from motor.motor_asyncio import AsyncIOMotorClient

from openai import OpenAI

from weaviate.classes.query import MetadataQuery

router = APIRouter()


class QueryResponse(BaseModel):
    answer: str


@router.post("/api/query", response_model=QueryResponse)
async def query_ai(
    request: Request,
    body: QueryRequest,
    db: AsyncIOMotorClient = Depends(get_db)
):
    user_query = body.query
    project = normalize_project_name(body.project)

    # Input validation
    if not user_query.strip():
        logger.warning("Empty query received.")
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not project.strip():
        logger.warning("Empty project name received.")
        raise HTTPException(status_code=400, detail="Project name cannot be empty.")

    try:
        query_emb = get_embedding(user_query)
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding for query.")

    # Database collections setup
    try:
        db = request.app.state.db
        weaviate_class_name = get_weaviate_class_name(project)
        hashes_collection_name = get_mongo_chunk_hashes_collection_name(project)
        hashes_collection = db[hashes_collection_name]
        answers_collection_name = get_mongo_answers_collection_name(project)
        answers_collection = db[answers_collection_name]
    except KeyError as e:
        logger.error(f"Invalid project setup: {str(e)}")
        raise HTTPException(status_code=400, detail="Project configuration is invalid.")

    # Query Weaviate (Unchanged)
    try:
        weaviate_client = request.app.state.weaviate_client
        chunk_collection = weaviate_client.collections.get(weaviate_class_name)
        result = chunk_collection.query.near_vector(
            near_vector=query_emb,
            limit=10,
            return_metadata=MetadataQuery(distance=True)
        )
        logger.debug("Weaviate query executed successfully.")
    except Exception as e:
        logger.error(f"Weaviate query failed: {e}")
        raise HTTPException(status_code=500, detail="Weaviate query failed.")

    # Process retrieved chunks
    retrieved_chunks = []
    try:
        for item in result.objects:
            rec = {
                "file": item.properties["filePath"],
                "lines": f"{item.properties['startLine']}-{item.properties['endLine']}",
                "content": item.properties["content"],
            }
            retrieved_chunks.append(rec)
    except KeyError as e:
        logger.warning("Unexpected response format from Weaviate.")
        raise HTTPException(status_code=500, detail="Invalid response from Weaviate.")

    if not retrieved_chunks:
        logger.info("No relevant code chunks found for the query.")
        return {"answer": "No relevant code chunks found for your query."}

    # Limit context to prevent exceeding token limits
    encoder = encoding_for_model("gpt-4")
    context = []
    token_count = 0
    max_token_length = 3000

    for chunk in retrieved_chunks:
        formatted_chunk = (
            f"File: {chunk['file']}\nLines: {chunk['lines']}\nContent:\n{chunk['content']}"
        )
        chunk_token_count = len(encoder.encode(formatted_chunk))
        if token_count + chunk_token_count <= max_token_length:
            context.append(formatted_chunk)
            token_count += chunk_token_count
        else:
            break

    summary = await summarize_interactions(answers_collection)
    context.append(summary)
    context_str = "\n---\n".join(context)
    prompt = f"Context:\n{context_str}\n\nQuestion: {user_query}\nAnswer:"

    logger.info(f"Generated prompt for AI: {prompt}")

    # Call OpenAI API (Unchanged)
    try:
        openai_client = OpenAI()
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5000
        )
        ai_answer = completion.choices[0].message.content.strip()
        logger.info("AI responded successfully.")
    except Exception as e:
        ai_answer = f"Error calling OpenAI: {e}"
        logger.error(f"OpenAI API call failed: {e}")

    # Sanitize and store the result
    doc = {
        "query": user_query,
        "answer": ai_answer,
        "timestamp": datetime.utcnow()
    }
    sanitized_doc = sanitize_keys(doc)

    try:
        await answers_collection.insert_one(sanitized_doc)
        logger.debug("Sanitized Q&A stored in MongoDB.")
    except Exception as e:
        logger.error(f"Failed to store Q&A in MongoDB: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store query and answer.")

    return {"answer": ai_answer}

