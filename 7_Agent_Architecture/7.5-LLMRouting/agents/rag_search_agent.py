"""
RAG Search Agent that uses document search with semantic similarity.
"""

import logging
from typing import Dict, Any, Optional

from pydantic_ai import Agent, RunContext

from clients import get_model
from .deps import AgentDependencies
from .prompts import RAG_SEARCH_SYSTEM_PROMPT
from tools.rag_tools import (
    retrieve_relevant_documents_tool,
    list_documents_tool,
    get_document_content_tool
)

logger = logging.getLogger(__name__)


# Initialize the RAG search agent
rag_search_agent = Agent(
    get_model(),
    deps_type=AgentDependencies,
    system_prompt=RAG_SEARCH_SYSTEM_PROMPT,
    instrument=True
)


@rag_search_agent.tool
async def search_documents(
    ctx: RunContext[AgentDependencies],
    query: str
) -> str:
    """
    Search through indexed documents using semantic similarity.
    
    Args:
        query: Search query for finding relevant documents
    
    Returns:
        Formatted string containing relevant document chunks with citations
    """
    try:
        result = await retrieve_relevant_documents_tool(
            supabase=ctx.deps.supabase,
            embedding_client=ctx.deps.embedding_client,
            user_query=query
        )
        
        logger.info(f"Retrieved document search results for query: {query}")
        return result
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        return f"Document search failed: {str(e)}"


@rag_search_agent.tool
async def list_available_documents(
    ctx: RunContext[AgentDependencies]
) -> str:
    """
    List all available documents in the knowledge base.
    
    Returns:
        String representation of available documents with metadata
    """
    try:
        result = await list_documents_tool(
            supabase=ctx.deps.supabase
        )
        
        logger.info("Retrieved list of available documents")
        return result
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        return f"Failed to list documents: {str(e)}"


@rag_search_agent.tool
async def get_full_document(
    ctx: RunContext[AgentDependencies],
    document_id: str
) -> str:
    """
    Retrieve the full content of a specific document by ID.
    
    Args:
        document_id: The ID or file path of the document to retrieve
    
    Returns:
        Complete content of the document with all chunks combined
    """
    try:
        result = await get_document_content_tool(
            supabase=ctx.deps.supabase,
            document_id=document_id
        )
        
        logger.info(f"Retrieved full document content for: {document_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {e}")
        return f"Failed to get document {document_id}: {str(e)}"


@rag_search_agent.tool
async def analyze_search_results(
    ctx: RunContext[AgentDependencies],
    search_results: str,
    query: str,
    focus_areas: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze and summarize document search results.
    
    Args:
        search_results: Raw search results from document search
        query: Original search query
        focus_areas: Optional specific areas to focus analysis on
    
    Returns:
        Dictionary with analysis summary
    """
    try:
        if not search_results or "No relevant documents found" in search_results:
            return {
                "summary": f"No relevant documents found for query: '{query}'",
                "query": query,
                "documents_found": 0,
                "key_points": []
            }
        
        # Extract document IDs and titles from the search results
        document_info = []
        lines = search_results.split('\n')
        current_doc_id = None
        current_title = None
        
        for line in lines:
            if line.startswith('# Document ID:'):
                current_doc_id = line.replace('# Document ID:', '').strip()
            elif line.startswith('# Document Title:'):
                current_title = line.replace('# Document Title:', '').strip()
                if current_doc_id and current_title:
                    document_info.append(f"- {current_title} (ID: {current_doc_id})")
        
        focus_text = f"\nFocus areas: {focus_areas}" if focus_areas else ""
        
        summary = f"""
Document Search Analysis for: "{query}"{focus_text}

Found {len(document_info)} relevant documents:
{chr(10).join(document_info)}

The search results contain relevant information from the knowledge base. 
Review the detailed document chunks above for specific information related to your query.
"""
        
        return {
            "summary": summary.strip(),
            "query": query,
            "documents_found": len(document_info),
            "key_points": document_info,
            "focus_areas": focus_areas
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze search results: {e}")
        return {
            "summary": f"Failed to analyze results: {str(e)}",
            "query": query,
            "documents_found": 0,
            "key_points": []
        }


def create_rag_search_agent() -> Agent:
    """
    Create a RAG search agent instance.
    
    Returns:
        Configured RAG search agent
    """
    return rag_search_agent