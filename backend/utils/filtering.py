# utils/filtering.py

import os
from typing import List

def get_filtered_file_paths(folder_path: str) -> List[str]:
    """
    Retrieve a list of file paths within the specified folder, excluding certain directories and files.

    Args:
        folder_path (str): The root folder path to analyze.

    Returns:
        List[str]: A list of file paths that are allowed for processing.
    """
    allowed_extensions = {
        '.py', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', 
        '.txt', '.md', '.markdown', '.xml', '.json', '.yaml', '.yml'
    }
    excluded_dirs = {
        '.git', 
        'node_modules', 
        '__pycache__',
        'dist', 
        'build', 
        'out', 
        '.vscode', 
        '.idea',
        'venv',
        'env',
        'target',
        'bower_components',
    }
    excluded_files = {
        'package-lock.json', 
        'yarn.lock', 
        'pnpm-lock.yaml', 
        'npm-shrinkwrap.json',
        'dockerfile', 
        'docker-compose.yml',
        'tsconfig.json',
        'jest.config.js',
        '.eslintignore',
        '.prettierrc',
        '.DS_Store',
        'Thumbs.db',
        'desktop.ini',
        # Add more files as needed
    }

    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        # Remove excluded directories from traversal
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            # Exclude specific lock and other irrelevant files (case-insensitive)
            if file.lower() in (fname.lower() for fname in excluded_files):
                continue
            _, ext = os.path.splitext(file)
            if ext.lower() not in allowed_extensions:
                continue
            fp = os.path.join(root, file)
            file_paths.append(fp)
    return file_paths

