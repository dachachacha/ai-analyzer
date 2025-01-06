# utils/sanitizer.py

def sanitize_keys(data):
    """Recursively sanitize keys in a dictionary to remove MongoDB reserved characters."""
    if isinstance(data, dict):
        return {key.replace('.', '_').replace('$', '_'): sanitize_keys(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_keys(item) for item in data]
    return data

