"""
Web Search Agent that uses Brave Search API for current information retrieval.
"""

import logging
from typing import Dict, Any, List, Optional

from pydantic_ai import Agent, RunContext

from clients import get_model
from .deps import AgentDependencies
from .prompts import WEB_SEARCH_SYSTEM_PROMPT
from tools.web_tools import search_web_tool

logger = logging.getLogger(__name__)


# Initialize the web search agent
web_search_agent = Agent(
    get_model(),
    deps_type=AgentDependencies,
    system_prompt=WEB_SEARCH_SYSTEM_PROMPT,
    instrument=True
)


@web_search_agent.tool
async def search_web(
    ctx: RunContext[AgentDependencies],
    query: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search the web using Brave Search API.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return (1-20)
    
    Returns:
        List of search results with title, URL, description, and score
    """
    try:        
        # Ensure max_results is within valid range
        max_results = min(max(max_results, 1), 20)
        
        results = await search_web_tool(
            api_key=ctx.deps.brave_api_key,
            query=query,
            count=max_results
        )
        
        logger.info(f"Found {len(results)} results for query: {query}")
        return results
        
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return [{"error": f"Search failed: {str(e)}"}]


@web_search_agent.tool
async def summarize_search_results(
    ctx: RunContext[AgentDependencies],
    search_results: List[Dict[str, Any]],
    topic: str,
    focus_areas: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a comprehensive summary of web search findings.
    
    Args:
        search_results: List of search result dictionaries
        topic: Main research topic
        focus_areas: Optional specific areas to focus on
    
    Returns:
        Dictionary with research summary
    """
    try:
        if not search_results:
            return {
                "summary": "No search results provided for summarization.",
                "key_points": [],
                "sources_count": 0
            }
        
        # Extract key information
        sources = []
        descriptions = []
        
        for result in search_results:
            if "title" in result and "url" in result:
                sources.append(f"- {result['title']}: {result['url']}")
                if "description" in result:
                    descriptions.append(result["description"])
        
        # Create summary content
        content_summary = "\n".join(descriptions[:5])  # Limit to top 5 descriptions
        sources_list = "\n".join(sources[:10])  # Limit to top 10 sources
        
        focus_text = f"\nSpecific focus areas: {focus_areas}" if focus_areas else ""
        
        summary = f"""
Research Summary: {topic}{focus_text}

Key Findings:
{content_summary}

Sources:
{sources_list}
"""
        
        return {
            "summary": summary,
            "topic": topic,
            "sources_count": len(sources),
            "key_points": descriptions[:5]
        }
        
    except Exception as e:
        logger.error(f"Failed to summarize research: {e}")
        return {
            "summary": f"Failed to summarize research: {str(e)}",
            "key_points": [],
            "sources": []
        }


def create_web_search_agent() -> Agent:
    """
    Create a web search agent instance.
    
    Returns:
        Configured web search agent
    """
    return web_search_agent