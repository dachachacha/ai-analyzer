# utils/summarizer.py

from typing import Any
from datetime import datetime
from fastapi import HTTPException
from loguru import logger
from openai import OpenAI

openai_client = OpenAI()

async def summarize_interactions(collection, max_literal=2, max_total=10) -> str:
    """
    Summarize the last `max_total` interactions, keeping the last `max_literal`
    interactions literal and summarizing the rest.

    Args:
        collection: The MongoDB collection containing the query history.
        max_literal: Number of most recent interactions to include as-is.
        max_total: Total number of interactions to process.

    Returns:
        A formatted string with the last `max_literal` interactions literal
        and earlier interactions summarized.
    """
    # Fetch the last `max_total` interactions
    recent_history = await collection.find(
        {},
        {"_id": 0, "query": 1, "answer": 1}
    ).sort("timestamp", -1).limit(max_total).to_list(length=max_total)

    if not recent_history:
        return "No previous interactions available."

    # Split history into literal and to summarize
    literal_history = recent_history[:max_literal]
    to_summarize = recent_history[max_literal:]

    # Format the literal history
    literal_formatted = "\n".join(
        [f"{i + 1}. Query: {entry['query']}\n   Answer: {entry['answer']}" for i, entry in enumerate(literal_history)]
    )

    # Summarize the rest using OpenAI
    if to_summarize:
        summarize_prompt = "\n".join(
            [f"Query: {entry['query']}\nAnswer: {entry['answer']}" for entry in to_summarize]
        )
        try:
            summary_response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Summarize these interactions:\n{summarize_prompt}"}],
                temperature=0.0,
                max_tokens=400
            )
            summary = summary_response.choices[0].message["content"].strip()
        except Exception as e:
            summary = f"Error summarizing interactions: {e}"
    else:
        summary = "No earlier interactions available."

    # Combine literal and summarized history
    combined_history = f"""
Previous Interactions:

Literal History:
{literal_formatted}

Summarized History:
{summary}
    """
    return combined_history

