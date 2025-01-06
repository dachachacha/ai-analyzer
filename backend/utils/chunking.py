# utils/chunking.py

import os
import re
from typing import List, Dict
from loguru import logger
from config import BINARY_EXTS, CLASS_NAME
from typing import List, Optional, Any
import mimetypes


def looks_like_binary(ext: str) -> bool:
    return ext.lower() in BINARY_EXTS

def looks_like_binary_with_mime(fp: str) -> bool:
    mime, _ = mimetypes.guess_type(fp)
    if mime is None:
        return True  # Unknown types are treated as binary
    return not mime.startswith('text')

def parse_python_functions(content: str) -> List[Dict[str, Any]]:
    """
    Parses Python functions from the content and returns a list of dictionaries
    with function details.
    This is a simplistic parser; consider using ast or other parsing libraries for robustness.
    """
    function_pattern = re.compile(r'^def\s+(\w+)\s*\(.*?\):', re.MULTILINE)
    functions = []
    for match in function_pattern.finditer(content):
        func_name = match.group(1)
        start = match.start()
        start_line = content.count('\n', 0, start)
        # Attempt to find the end of the function by indentation
        lines = content[start:].split('\n')
        func_body = [lines[0]]
        for line in lines[1:]:
            if line.startswith((' ', '\t')):
                func_body.append(line)
            else:
                break
        end_line = start_line + len(func_body) - 1
        functions.append({
            "function_name": func_name,
            "chunk_text": "\n".join(func_body),
            "start_line": start_line,
            "end_line": end_line
        })
    return functions

def chunk_markdown(lines: List[str], language_label: str, file_path: str, max_lines=200, min_lines=50) -> List[Dict[str, Any]]:
    chunks = []
    current_chunk = []
    start_line = 0

    for i, line in enumerate(lines):
        if re.match(r"^#{1,6} ", line):  # Match Markdown headings
            if current_chunk and len(current_chunk) >= min_lines:
                chunks.append({
                    "content": "\n".join(current_chunk),
                    "functionName": None,
                    "startLine": start_line,
                    "endLine": i - 1,
                    "filePath": file_path,
                    "language": language_label
                })
                current_chunk = [line]
                start_line = i
            else:
                current_chunk.append(line)
        else:
            current_chunk.append(line)

        # Check max lines for the current chunk
        if len(current_chunk) >= max_lines:
            chunks.append({
                "content": "\n".join(current_chunk),
                "functionName": None,
                "startLine": start_line,
                "endLine": i,
                "filePath": file_path,
                "language": language_label
            })
            current_chunk = []
            start_line = i + 1

    # Add the final chunk
    if current_chunk:
        chunks.append({
            "content": "\n".join(current_chunk),
            "functionName": None,
            "startLine": start_line,
            "endLine": len(lines) - 1,
            "filePath": file_path,
            "language": language_label
        })

    return chunks

def chunk_python_file(content: str, file_path: str, language_label: str, max_lines=200, min_lines=50) -> List[Dict[str, Any]]:
    function_chunks = parse_python_functions(content)
    if not function_chunks:
        logger.info(f"No Python functions found in {file_path}. Using line-based chunking.")
        return chunk_by_lines(content.split("\n"), max_lines, language_label, file_path)
    
    chunks = []
    current_chunk = []
    start_line = 0

    for fc in function_chunks:
        func_lines = fc["chunk_text"].split("\n")
        if current_chunk and (len(current_chunk) + len(func_lines)) > max_lines:
            chunks.append({
                "content": "\n".join(current_chunk),
                "functionName": None,
                "startLine": start_line,
                "endLine": fc["start_line"] - 1,
                "filePath": file_path,
                "language": language_label
            })
            current_chunk = []
            start_line = fc["start_line"]

        current_chunk.extend(func_lines)

    if current_chunk:
        chunks.append({
            "content": "\n".join(current_chunk),
            "functionName": None,
            "startLine": start_line,
            "endLine": function_chunks[-1]["end_line"],
            "filePath": file_path,
            "language": language_label
        })

    return chunks

def chunk_code_file(content: str, file_path: str, language_label: str, max_lines=200, min_lines=50) -> List[Dict[str, Any]]:
    lines = content.split("\n")
    return chunk_by_lines(lines, max_lines, language_label, file_path, min_lines=min_lines)

def chunk_by_lines(lines: List[str], max_lines: int, language_label: str, file_path: str, min_lines: int =50) -> List[Dict[str, Any]]:
    chunks = []
    current_chunk = []
    start_line = 0

    for i, line in enumerate(lines):
        current_chunk.append(line)

        if len(current_chunk) >= max_lines:
            chunks.append({
                "content": "\n".join(current_chunk),
                "functionName": None,
                "startLine": start_line,
                "endLine": i,
                "filePath": file_path,
                "language": language_label
            })
            current_chunk = []
            start_line = i + 1

    # Handle remaining lines
    if current_chunk:
        if len(current_chunk) >= min_lines or not chunks:
            chunks.append({
                "content": "\n".join(current_chunk),
                "functionName": None,
                "startLine": start_line,
                "endLine": len(lines) - 1,
                "filePath": file_path,
                "language": language_label
            })
        else:
            if chunks:
                # Merge with the previous chunk if too small
                chunks[-1]["content"] += "\n" + "\n".join(current_chunk)
                chunks[-1]["endLine"] = len(lines) - 1
            else:
                chunks.append({
                    "content": "\n".join(current_chunk),
                    "functionName": None,
                    "startLine": start_line,
                    "endLine": len(lines) - 1,
                    "filePath": file_path,
                    "language": language_label
                })

    return chunks

def chunk_file(file_path: str) -> List[Dict[str, Any]]:
    _, ext = os.path.splitext(file_path)

    if looks_like_binary(ext):
        logger.info(f"Skipping binary file: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

    lines = content.split("\n")
    language_label = (
        "Markdown" if ext == ".md" else
        "Python" if ext == ".py" else
        "JavaScript" if ext in (".js", ".jsx", ".mjs", ".ts", ".cjs") else
        ext[1:].lower() or "unknown"
    )

    if ext == ".md":
        return chunk_markdown(lines, language_label, file_path)
    elif ext == ".py":
        return chunk_python_file(content, file_path, language_label)
    elif ext in (".js", ".jsx", ".mjs", ".cjs", ".ts"):
        return chunk_code_file(content, file_path, language_label)
    else:
        return chunk_by_lines(lines, 200, language_label, file_path)  # Increased max_lines for other file types

