"""
Main text processing module - orchestrates all text processing operations.
This is the main entry point that imports and re-exports all functionality.
"""
from typing import List, Dict, Any

# Import from specialized modules
from .text_chunker import chunk_text
from .ocr_extractor import extract_text_from_pdf, extract_text_with_ocr
from .csv_handler import extract_schema_from_csv, extract_rows_from_csv
from .embeddings import create_embeddings

# Re-export all functions for backward compatibility
__all__ = [
    'chunk_text',
    'extract_text_from_pdf',
    'extract_text_with_ocr',
    'extract_text_from_file',
    'create_embeddings',
    'is_tabular_file',
    'extract_schema_from_csv',
    'extract_rows_from_csv',
]


def extract_text_from_file(file_content: bytes, mime_type: str, file_name: str, config: Dict[str, Any] = None) -> str:
    """
    Extract text from a file based on its MIME type.
    
    Args:
        file_content: Binary content of the file
        mime_type: MIME type of the file
        file_name: Name of the file
        config: Configuration dictionary with supported_mime_types
        
    Returns:
        Extracted text from the file
    """
    supported_mime_types = []
    if config and 'supported_mime_types' in config:
        supported_mime_types = config['supported_mime_types']
    
    # Use Mistral OCR for PDFs and images
    if 'application/pdf' in mime_type:
        return extract_text_from_pdf(file_content, file_name)
    elif mime_type.startswith('image/') and mime_type in ['image/png', 'image/jpg', 'image/jpeg', 'image/svg', 'image/svg+xml']:
        # Use OCR for images
        print(f"Processing image {file_name} with Mistral OCR")
        return extract_text_with_ocr(file_content, file_name, mime_type)
    elif config and any(mime_type.startswith(t) for t in supported_mime_types):
        return file_content.decode('utf-8', errors='replace')
    else:
        # For unsupported file types, just try to extract the text
        return file_content.decode('utf-8', errors='replace')


def is_tabular_file(mime_type: str, config: Dict[str, Any] = None) -> bool:
    """
    Check if a file is tabular based on its MIME type.
    
    Args:
        mime_type: The MIME type of the file
        config: Optional configuration dictionary
        
    Returns:
        bool: True if the file is tabular (CSV or Excel), False otherwise
    """
    # Default tabular MIME types if config is not provided
    tabular_mime_types = [
        'csv',
        'xlsx',
        'text/csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.google-apps.spreadsheet'
    ]
    
    # Use tabular_mime_types from config if available
    if config and 'tabular_mime_types' in config:
        tabular_mime_types = config['tabular_mime_types']
    
    return any(mime_type.startswith(t) for t in tabular_mime_types)
