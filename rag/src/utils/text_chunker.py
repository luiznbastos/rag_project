"""
Text chunking utilities for processing markdown documents.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.config import settings

logger = logging.getLogger(__name__)


def chunk_markdown_files(
    docs_directory: str = "src/docs_en/docs",
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[Dict[str, Any]]:
    """
    Read all markdown files from directory and chunk them.
    
    Args:
        docs_directory: Path to directory containing .md files
        chunk_size: Size of each chunk (defaults to config value)
        chunk_overlap: Overlap between chunks (defaults to config value)
    
    Returns:
        List of dictionaries with chunk data including:
        - document_id: Base filename without extension
        - chunk_id: Sequential chunk ID within document
        - filename: Full filename with path relative to docs directory
        - chunk_text: Text content of the chunk
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = []
    docs_path = Path(docs_directory)
    
    if not docs_path.exists():
        logger.error(f"Directory not found: {docs_directory}")
        return chunks
    
    md_files = list(docs_path.rglob("*.md"))
    logger.info(f"Found {len(md_files)} markdown files to process")
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Skipping empty file: {md_file}")
                continue
            
            document_id = md_file.stem
            relative_path = md_file.relative_to(docs_path)
            filename = str(relative_path)
            
            split_texts = text_splitter.split_text(content)
            
            for idx, chunk_text in enumerate(split_texts):
                chunk_id = f"{document_id}_chunk_{idx}"
                chunks.append({
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "filename": filename,
                    "chunk_text": chunk_text
                })
            
            logger.info(f"Processed {md_file.name}: {len(split_texts)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing {md_file}: {e}")
            continue
    
    logger.info(f"Total chunks created: {len(chunks)}")
    return chunks

