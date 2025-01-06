import os
from pathlib import Path
from typing import Optional
from loguru import logger

def load_file_secret(secret_file_env_var: str, target_env_var: str) -> Optional[str]:
    """
    Load a secret from a file specified by an environment variable and set it as another environment variable.
    
    Args:
        secret_file_env_var: Name of environment variable containing the path to the secret file
        target_env_var: Name of the environment variable to set with the secret value
    
    Returns:
        The value of the secret if successfully loaded, None otherwise
    
    Example:
        load_file_secret('OPENAI_API_KEY_FILE', 'OPENAI_API_KEY')
    """
    logger.info(f"loading key file: {secret_file_env_var}")
    print(f"loading key file: {secret_file_env_var}")

    secret_file = os.getenv(secret_file_env_var)
    if not secret_file:
        return None
        
    try:
        secret_path = Path(secret_file)
        if not secret_path.exists():
            return None
            
        secret = secret_path.read_text().strip()
        os.environ[target_env_var] = secret
        return secret
        
    except Exception as e:
        print(f"Error loading secret from {secret_file}: {e}")
        return None
