from typing import List
from supabase import Client
from openai import AsyncOpenAI
import re

from .rag_tools import get_document_content_tool, get_embedding

def extract_google_drive_urls(text: str) -> List[str]:
    """
    Extract Google Drive document URLs from text using regex.
    
    Args:
        text: Text containing potential Google Drive URLs
        
    Returns:
        List[str]: List of extracted Google Drive URLs
    """
    pattern = r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)/'
    matches = re.findall(pattern, text)
    return [f"https://docs.google.com/document/d/{file_id}/" for file_id in matches]

def extract_file_ids_from_urls(urls: List[str]) -> List[str]:
    """
    Extract file IDs from Google Drive URLs.
    
    Args:
        urls: List of Google Drive URLs
        
    Returns:
        List[str]: List of extracted file IDs
    """
    pattern = r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)/'
    file_ids = []
    for url in urls:
        match = re.search(pattern, url)
        if match:
            file_ids.append(match.group(1))
    return file_ids

async def validate_citation_exists(supabase: Client, file_id: str) -> bool:
    """
    Validate that a cited document exists in the knowledge base.
    
    Args:
        supabase: Supabase client
        file_id: The file ID to validate
        
    Returns:
        bool: True if document exists, False otherwise
    """
    try:
        result = supabase.from_('document_metadata') \
            .select('id, title') \
            .eq('id', file_id) \
            .limit(1) \
            .execute()
        
        return len(result.data) > 0
    except Exception as e:
        print(f"Error validating citation existence: {e}")
        return False

async def validate_citation_relevance(
    supabase: Client, 
    embedding_client: AsyncOpenAI,
    file_id: str, 
    query: str, 
    response_content: str
) -> bool:
    """
    Validate that a cited document is relevant to the query and response.
    
    Args:
        supabase: Supabase client
        embedding_client: OpenAI embedding client
        file_id: The file ID to validate
        query: Original user query
        response_content: The content claiming to be from this document
        
    Returns:
        bool: True if document is relevant, False otherwise
    """
    try:
        # Get the document content
        document_content = await get_document_content_tool(supabase, file_id)
        
        if "No content found" in document_content or "Error" in document_content:
            return False
        
        # Get embeddings for query, response, and document
        query_embedding = await get_embedding(query, embedding_client)
        response_embedding = await get_embedding(response_content, embedding_client)
        document_embedding = await get_embedding(document_content[:2000], embedding_client)  # Limit for embedding
        
        # Calculate similarity (simple dot product for now)
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            if len(a) != len(b):
                return 0.0
            dot_product = sum(x * y for x, y in zip(a, b))
            magnitude_a = sum(x ** 2 for x in a) ** 0.5
            magnitude_b = sum(x ** 2 for x in b) ** 0.5
            if magnitude_a == 0 or magnitude_b == 0:
                return 0.0
            return dot_product / (magnitude_a * magnitude_b)
        
        # Check if document is relevant to query
        query_doc_similarity = cosine_similarity(query_embedding, document_embedding)
        
        # Check if response content is reasonably related to document
        response_doc_similarity = cosine_similarity(response_embedding, document_embedding)
        
        # Threshold for relevance (can be adjusted)
        relevance_threshold = 0.6
        
        return query_doc_similarity > relevance_threshold and response_doc_similarity > relevance_threshold
        
    except Exception as e:
        print(f"Error validating citation relevance: {e}")
        return False

async def validate_all_citations(
    supabase: Client,
    embedding_client: AsyncOpenAI,
    response_text: str,
    original_query: str
) -> dict:
    """
    Validate all citations in a response text.
    
    Args:
        supabase: Supabase client
        embedding_client: OpenAI embedding client
        response_text: The response text containing citations
        original_query: The original user query
        
    Returns:
        dict: Validation results with status and feedback
    """
    try:
        # Extract URLs and file IDs
        urls = extract_google_drive_urls(response_text)
        file_ids = extract_file_ids_from_urls(urls)
        
        if not urls:
            return {
                "status": "invalid",
                "feedback": "No Google Drive citations found in response. Please include proper citations in the format: https://docs.google.com/document/d/[file_id]/"
            }
        
        validation_results = []
        
        for file_id in file_ids:
            # Check if document exists
            exists = await validate_citation_exists(supabase, file_id)
            if not exists:
                validation_results.append({
                    "file_id": file_id,
                    "status": "invalid",
                    "reason": "Document not found in knowledge base"
                })
                continue
            
            # Check if citation is relevant
            relevant = await validate_citation_relevance(
                supabase, embedding_client, file_id, original_query, response_text
            )
            if not relevant:
                validation_results.append({
                    "file_id": file_id,
                    "status": "invalid",
                    "reason": "Document not relevant to query or response content"
                })
                continue
            
            validation_results.append({
                "file_id": file_id,
                "status": "valid",
                "reason": "Citation is valid and relevant"
            })
        
        # Check if all citations are valid
        invalid_citations = [r for r in validation_results if r["status"] == "invalid"]
        
        if invalid_citations:
            feedback_parts = []
            for invalid in invalid_citations:
                feedback_parts.append(f"File ID {invalid['file_id']}: {invalid['reason']}")
            
            return {
                "status": "invalid",
                "feedback": f"Invalid citations found: {'; '.join(feedback_parts)}. Please provide accurate citations from the knowledge base."
            }
        
        return {
            "status": "valid",
            "feedback": "All citations are valid and relevant"
        }
        
    except Exception as e:
        print(f"Error validating citations: {e}")
        return {
            "status": "invalid",
            "feedback": f"Error during validation: {str(e)}"
        }