"""
CSV file handling utilities.
"""
import io
import csv
from typing import List, Dict, Any


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
