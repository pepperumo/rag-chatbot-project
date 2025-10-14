"""
Email Search Agent that uses Gmail API for searching emails with readonly permissions.
"""

import logging
from typing import Dict, Any, List

from pydantic_ai import Agent, RunContext

from clients import get_model
from .deps import AgentDependencies
from .prompts import EMAIL_SEARCH_SYSTEM_PROMPT
from tools.email_tools import search_emails_tool, get_email_content_tool

logger = logging.getLogger(__name__)


# Initialize the email search agent
email_search_agent = Agent(
    get_model(),
    deps_type=AgentDependencies,
    system_prompt=EMAIL_SEARCH_SYSTEM_PROMPT,
    instrument=True
)


@email_search_agent.tool
async def search_emails(
    ctx: RunContext[AgentDependencies],
    query: str,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Search emails using Gmail API with readonly permissions.
    
    Args:
        query: Gmail search query (supports Gmail search operators like from:, subject:, etc.)
        max_results: Maximum number of results to return (1-50)
    
    Returns:
        Dictionary with search results
    """
    try:
        # Ensure max_results is within valid range
        max_results = min(max(max_results, 1), 50)
        
        result = await search_emails_tool(
            credentials_path=ctx.deps.gmail_credentials_path,
            token_path=ctx.deps.gmail_token_path,
            query=query,
            max_results=max_results
        )
        
        if result["success"]:
            logger.info(f"Found {result['count']} emails for query: {query}")
        else:
            logger.warning(f"Email search failed: {result['error']}")
            
        return result
        
    except Exception as e:
        logger.error(f"Email search failed: {e}")
        return {
            "success": False,
            "error": f"Search failed: {str(e)}",
            "results": [],
            "count": 0
        }


@email_search_agent.tool
async def get_email_content(
    ctx: RunContext[AgentDependencies],
    message_id: str
) -> Dict[str, Any]:
    """
    Get the full content of a specific email message.
    
    Args:
        message_id: Gmail message ID
    
    Returns:
        Dictionary with email content
    """
    try:
        result = await get_email_content_tool(
            credentials_path=ctx.deps.gmail_credentials_path,
            token_path=ctx.deps.gmail_token_path,
            message_id=message_id
        )
        
        if result.get("success"):
            logger.info(f"Retrieved email content for message: {message_id}")
        else:
            logger.warning(f"Failed to get email content: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to get email content: {e}")
        return {
            "success": False,
            "error": f"Content retrieval failed: {str(e)}"
        }


@email_search_agent.tool
async def format_email_results(
    ctx: RunContext[AgentDependencies],
    search_results: List[Dict[str, Any]],
    query: str
) -> Dict[str, Any]:
    """
    Format email search results into a readable summary.
    
    Args:
        search_results: List of email search result dictionaries
        query: Original search query
    
    Returns:
        Dictionary with formatted summary
    """
    try:
        if not search_results:
            return {
                "summary": f"No emails found for query: '{query}'",
                "email_count": 0,
                "formatted_results": []
            }
        
        formatted_results = []
        for idx, email in enumerate(search_results, 1):
            formatted_email = f"""
Email {idx}:
- Subject: {email.get('subject', 'No Subject')}
- From: {email.get('from', 'Unknown')}
- Date: {email.get('date', 'Unknown')}
- Snippet: {email.get('snippet', 'No preview available')}
- Message ID: {email.get('id', 'Unknown')}
"""
            formatted_results.append(formatted_email.strip())
        
        summary = f"""
Email Search Results for: "{query}"

Found {len(search_results)} emails:

{chr(10).join(formatted_results)}
"""
        
        return {
            "summary": summary.strip(),
            "email_count": len(search_results),
            "formatted_results": formatted_results,
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Failed to format email results: {e}")
        return {
            "summary": f"Failed to format results: {str(e)}",
            "email_count": 0,
            "formatted_results": []
        }


def create_email_search_agent() -> Agent:
    """
    Create an email search agent instance.
    
    Returns:
        Configured email search agent
    """
    return email_search_agent