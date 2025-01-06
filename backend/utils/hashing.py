# utils/hashing.py

import hashlib

def calculate_hash(content: str) -> str:
    """Calculate SHA-256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

