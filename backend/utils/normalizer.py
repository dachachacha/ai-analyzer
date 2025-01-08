# utils/normalizer.py

import re

def normalize_project_name(name: str) -> str:
    """Normalize project name for safe use in collection names."""
    return re.sub(r'[^a-zA-Z0-9]', '_', name).lower()

