"""
Main text processing module - orchestrates all text processing operations.
This is the main entry point that imports and re-exports all functionality.
"""
import os
import io
import csv
import tempfile
from typing import List, Dict, Any
import pypdf
from dotenv import load_dotenv
from pathlib import Path

# Import from specialized modules
from .text_chunker import chunk_text
from .ocr_extractor import extract_text_from_pdf as extract_text_from_pdf_ocr, extract_text_with_ocr
from .embeddings import create_embeddings

# Check if we're in production
is_production = os.getenv("ENVIRONMENT") == "production"

if not is_production:
    # Development: prioritize .env file
    project_root = Path(__file__).resolve().parent.parent
    dotenv_path = project_root / '.env'
    load_dotenv(dotenv_path, override=True)
else:
    # Production: use cloud platform env vars only
    load_dotenv()

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

def extract_text_from_pdf(file_content: bytes, file_name: str = "document.pdf") -> str:
    """
    Extract text from a PDF file using Mistral OCR API.
    Falls back to pypdf if OCR is not configured.
    
    Args:
        file_content: Binary content of the PDF file
        file_name: Name of the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    # Check if Mistral OCR is configured
    if os.getenv('LLM_OCR_API_KEY'):
        # Use Mistral OCR for better text extraction
        return extract_text_from_pdf_ocr(file_content, file_name)
    
    # Fallback to pypdf for basic extraction
    # Create a temporary file to store the PDF content
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name
    
    try:
        # Open the PDF file
        with open(temp_file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            text = ""
            
            # Extract text from each page
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        
        return text
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

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
    
    if 'application/pdf' in mime_type:
        return extract_text_from_pdf(file_content, file_name)
    elif mime_type.startswith('image/') and mime_type in ['image/png', 'image/jpg', 'image/jpeg', 'image/svg', 'image/svg+xml']:
        # Use OCR for images if configured
        if os.getenv('LLM_OCR_API_KEY'):
            print(f"Processing image {file_name} with Mistral OCR")
            return extract_text_with_ocr(file_content, file_name, mime_type)
        else:
            # Fallback to filename if OCR not configured
            return file_name
    elif mime_type.startswith('image'):
        # For other image types, return filename
        return file_name
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

def extract_schema_from_csv(file_content: bytes) -> List[str]:
    """
    Extract column names from a CSV file.
    
    Args:
        file_content: The binary content of the CSV file
        
    Returns:
        List[str]: List of column names
    """
    try:
        # Decode the CSV content
        text_content = file_content.decode('utf-8', errors='replace')
        csv_reader = csv.reader(io.StringIO(text_content))
        # Get the header row (first row)
        header = next(csv_reader)
        return header
    except Exception as e:
        print(f"Error extracting schema from CSV: {e}")
        return []

def extract_rows_from_csv(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Extract rows from a CSV file as a list of dictionaries.
    
    Args:
        file_content: The binary content of the CSV file
        
    Returns:
        List[Dict[str, Any]]: List of row data as dictionaries
    """
    try:
        # Decode the CSV content
        text_content = file_content.decode('utf-8', errors='replace')
        csv_reader = csv.DictReader(io.StringIO(text_content))
        return list(csv_reader)
    except Exception as e:
        print(f"Error extracting rows from CSV: {e}")
        return []    
