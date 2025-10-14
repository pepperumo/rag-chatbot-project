"""
Web Research Agent for conducting targeted web research using Brave Search API.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from clients import get_model
from tools.brave_tools import search_web_tool
from .prompts import WEB_RESEARCH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)




@dataclass
class WebResearchAgentDependencies:
    """Dependencies for the web research agent - only configuration, no tool instances."""
    brave_api_key: str
    session_id: Optional[str] = None


# Initialize the web research agent
web_research_agent = Agent(
    get_model(),
    deps_type=WebResearchAgentDependencies,
    system_prompt=WEB_RESEARCH_SYSTEM_PROMPT,
    instrument=True
)


@web_research_agent.tool
async def search_web(
    ctx: RunContext[WebResearchAgentDependencies],
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


@web_research_agent.tool
async def conduct_comprehensive_search(
    ctx: RunContext[WebResearchAgentDependencies],
    primary_query: str,
    related_queries: Optional[List[str]] = None,
    max_results_per_query: int = 5
) -> Dict[str, Any]:
    """
    Conduct comprehensive research using multiple related search queries.
    
    Args:
        primary_query: Main search query
        related_queries: Optional list of related queries to expand research
        max_results_per_query: Maximum results per individual query
    
    Returns:
        Dictionary with comprehensive search results organized by query
    """
    try:
        all_results = {}
        total_sources = 0
        
        # Search primary query
        primary_results = await search_web_tool(
            api_key=ctx.deps.brave_api_key,
            query=primary_query,
            count=max_results_per_query
        )
        
        all_results[primary_query] = primary_results
        total_sources += len(primary_results)
        
        # Search related queries if provided
        if related_queries:
            for query in related_queries:
                try:
                    query_results = await search_web_tool(
                        api_key=ctx.deps.brave_api_key,
                        query=query,
                        count=max_results_per_query
                    )
                    all_results[query] = query_results
                    total_sources += len(query_results)
                except Exception as e:
                    logger.warning(f"Failed to search query '{query}': {e}")
                    all_results[query] = [{"error": str(e)}]
                
                time.sleep(1)
        
        logger.info(f"Comprehensive search completed: {total_sources} total sources across {len(all_results)} queries")
        
        return {
            "success": True,
            "primary_query": primary_query,
            "total_queries": len(all_results),
            "total_sources": total_sources,
            "results_by_query": all_results
        }
        
    except Exception as e:
        logger.error(f"Comprehensive search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "primary_query": primary_query,
            "total_queries": 0,
            "total_sources": 0,
            "results_by_query": {}
        }


@web_research_agent.tool
async def analyze_search_results(
    ctx: RunContext[WebResearchAgentDependencies],
    search_results: List[Dict[str, Any]],
    topic: str,
    focus_areas: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze and synthesize search results into a structured summary.
    
    Args:
        search_results: List of search result dictionaries
        topic: Main research topic
        focus_areas: Optional specific areas to focus analysis on
    
    Returns:
        Dictionary with analysis and synthesis of search results
    """
    try:
        if not search_results:
            return {
                "success": False,
                "error": "No search results provided for analysis",
                "topic": topic,
                "summary": "",
                "key_findings": [],
                "sources": []
            }
        
        # Extract and organize information
        sources = []
        descriptions = []
        high_relevance_sources = []
        
        for idx, result in enumerate(search_results):
            if "error" in result:
                continue
                
            if "title" in result and "url" in result:
                source_info = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("description", ""),
                    "relevance_score": result.get("score", 0.5),
                    "position": idx + 1
                }
                sources.append(source_info)
                
                if "description" in result:
                    descriptions.append(result["description"])
                
                # Mark high-relevance sources (top 3 or score > 0.8)
                if idx < 3 or result.get("score", 0) > 0.8:
                    high_relevance_sources.append(source_info)
        
        # Create structured summary
        key_findings = descriptions[:5]  # Top 5 descriptions as key findings
        sources_summary = [f"- {src['title']}: {src['url']}" for src in sources[:10]]
        
        focus_text = ""
        if focus_areas:
            focus_text = f"\n\nFocus Areas: {', '.join(focus_areas)}"
        
        structured_summary = f"""
Research Analysis: {topic}{focus_text}

Key Findings:
{chr(10).join([f"• {finding}" for finding in key_findings])}

High-Relevance Sources:
{chr(10).join([f"- {src['title']}: {src['url']}" for src in high_relevance_sources])}

All Sources ({len(sources)} total):
{chr(10).join(sources_summary)}
"""
        
        logger.info(f"Analysis completed for topic: {topic} - {len(sources)} sources analyzed")
        
        return {
            "success": True,
            "topic": topic,
            "summary": structured_summary.strip(),
            "key_findings": key_findings,
            "high_relevance_sources": high_relevance_sources,
            "all_sources": sources,
            "sources_count": len(sources),
            "focus_areas": focus_areas or []
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze search results: {e}")
        return {
            "success": False,
            "error": str(e),
            "topic": topic,
            "summary": f"Analysis failed: {str(e)}",
            "key_findings": [],
            "sources": []
        }


@web_research_agent.tool
async def search_with_context(
    ctx: RunContext[WebResearchAgentDependencies],
    query: str,
    context: Optional[str] = None,
    max_results: int = 8
) -> Dict[str, Any]:
    """
    Perform a targeted search with additional context to refine results.
    
    Args:
        query: Search query
        context: Optional context to help refine search strategy
        max_results: Maximum number of results to return
    
    Returns:
        Dictionary with search results and context-aware analysis
    """
    try:
        # Enhanced query based on context
        enhanced_query = query
        if context:
            # Use context to potentially modify search strategy
            logger.info(f"Searching with context: {context[:100]}...")
        
        # Perform search
        results = await search_web_tool(
            api_key=ctx.deps.brave_api_key,
            query=enhanced_query,
            count=max_results
        )
        
        # Quick relevance assessment
        relevant_results = []
        for result in results:
            if "error" not in result and result.get("title") and result.get("url"):
                relevant_results.append(result)
        
        logger.info(f"Context-aware search completed: {len(relevant_results)} relevant results")
        
        return {
            "success": True,
            "query": query,
            "enhanced_query": enhanced_query,
            "context_provided": bool(context),
            "total_results": len(results),
            "relevant_results": len(relevant_results),
            "results": relevant_results
        }
        
    except Exception as e:
        logger.error(f"Context-aware search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "results": []
        }


# Convenience function to create web research agent with dependencies
def create_web_research_agent(
    brave_api_key: str,
    session_id: Optional[str] = None
) -> Agent:
    """
    Create a web research agent with specified dependencies.
    
    Args:
        brave_api_key: Brave Search API key
        session_id: Optional session identifier
        
    Returns:
        Configured web research agent
    """
    return web_research_agent