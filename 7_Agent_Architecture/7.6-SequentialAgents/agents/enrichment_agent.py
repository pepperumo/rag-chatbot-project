"""
Enrichment Agent for sequential research and outreach system.

This agent enriches data by finding missing information like location, company details, education.
"""

import logging
from typing import Dict, Any, List
from pydantic_ai import Agent, RunContext

from clients import get_model
from .deps import ResearchAgentDependencies
from .prompts import ENRICHMENT_SYSTEM_PROMPT
from tools.brave_tools import search_web_tool

logger = logging.getLogger(__name__)


# Initialize the enrichment agent
enrichment_agent = Agent(
    get_model(use_smaller_model=False),
    deps_type=ResearchAgentDependencies,
    system_prompt=ENRICHMENT_SYSTEM_PROMPT,
    instrument=True
)


@enrichment_agent.tool
async def search_web(
    ctx: RunContext[ResearchAgentDependencies],
    query: str,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Search the web using Brave Search API for enrichment data.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return (1-10)
    
    Returns:
        List of search results with title, URL, description, and score
    """
    try:        
        # Ensure max_results is within valid range
        max_results = min(max(max_results, 1), 10)
        
        results = await search_web_tool(
            api_key=ctx.deps.brave_api_key,
            query=query,
            count=max_results
        )
        
        logger.info(f"Found {len(results)} enrichment results for query: {query}")
        return results
        
    except Exception as e:
        logger.error(f"Enrichment web search failed: {e}")
        return [{"error": f"Enrichment search failed: {str(e)}"}]
