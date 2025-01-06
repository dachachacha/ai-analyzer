# routes/query.py

from typing import List
from fastapi import APIRouter, Request, Depends, HTTPException
from loguru import logger
from datetime import datetime

from models import QueryRequest
from utils import get_embedding, summarize_interactions, sanitize_keys
from database import get_db

from weaviate import Client
from weaviate.classes.query import MetadataQuery
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()

@router.post("/api/query")
async def query_ai(
    request: Request, 
    body: QueryRequest,
    db: AsyncIOMotorClient = Depends(get_db)
):
    user_query = body.query
    if not user_query.strip():
        logger.warning("Empty query received.")
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        query_emb = get_embedding(user_query)
    except HTTPException as e:
        logger.error(f"Embedding generation failed: {e.detail}")
        raise

    # Query top 10 similar code chunks
    try:
        weaviate_client: Client = request.app.state.weaviate_client
        chunk_collection = weaviate_client.collections.get(CLASS_NAME)
        result = chunk_collection.query.near_vector(
            near_vector=query_emb,
            limit=10,
            return_metadata=MetadataQuery(distance=True)
        )
        logger.debug("Weaviate query executed successfully.")
    except Exception as e:
        logger.error(f"Weaviate query failed: {e}")
        raise HTTPException(status_code=500, detail="Weaviate query failed.")

    retrieved_chunks = []

    for item in result.objects:
        rec = {
            "file": item.properties["filePath"],
            "lines": f"{item.properties['startLine']}-{item.properties['endLine']}",
            "content": item.properties["content"],
        }
        retrieved_chunks.append(rec)

    if not retrieved_chunks:
        logger.info("No relevant code chunks found for the query.")
        return {"answer": "No relevant code chunks found for your query."}

    # Convert chunks to a formatted string
    formatted_chunks = [
        f"File: {chunk['file']}\nLines: {chunk['lines']}\nContent:\n{chunk['content']}"
        for chunk in retrieved_chunks
    ]

    # Limit context to prevent exceeding token limits
    context = []
    token_count = 0
    max_token_length = 3000

    for chunk in formatted_chunks:
        token_count += len(chunk.split())
        if token_count < max_token_length:
            context.append(chunk)
        else:
            break

    summary = await summarize_interactions(request.app.state.answers_collection)
    context.append(summary)
    context_str = "\n---\n".join(context)
    prompt = f"Context:\n{context_str}\n\nQuestion: {user_query}\nAnswer:"

    logger.info(f"Prompt: {prompt}")

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"user","content":prompt}],
            temperature=0.0,
            max_tokens=5000
        )
        ai_answer = completion.choices[0].message.content.strip()
        logger.info("AI responded successfully.")
    except Exception as e:
        ai_answer = f"Error calling OpenAI: {e}"
        logger.error(f"OpenAI API call failed: {e}")

    doc = {
        "query": user_query,
        "answer": ai_answer,
        "timestamp": datetime.utcnow()
    }

    # Sanitize the document before storing
    sanitized_doc = sanitize_keys(doc)

    try:
        # Insert the sanitized document into MongoDB
        await request.app.state.answers_collection.insert_one(sanitized_doc)
        logger.debug("Sanitized Q&A stored in MongoDB.")
    except Exception as e:
        logger.error(f"Failed to store Q&A in MongoDB: {e}")

    return {"answer": ai_answer}

