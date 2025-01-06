# utils/__init__.py

from .hashing import calculate_hash
from .setup_weaviate_schema import setup_weaviate_schema
from .chunking import chunk_file, looks_like_binary
from .embedding import get_embedding
from .sanitizer import sanitize_keys
from .summarizer import summarize_interactions
from .filtering import get_filtered_file_paths
from .secrets import load_file_secret

__all__ = [
    'calculate_hash',
    'chunk_file',
    'setup_weaviate_schema',
    'looks_like_binary',
    'get_embedding',
    'sanitize_keys',
    'summarize_interactions',
    'get_filtered_file_paths',  # Exposed the filtering function
    'load_file_secret',
]

