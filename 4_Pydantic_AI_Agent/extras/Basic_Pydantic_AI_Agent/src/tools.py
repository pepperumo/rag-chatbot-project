"""
Web search tools for the Pydantic AI agent.

This module contains the tools for searching the web using either Brave Search API or SearXNG.
"""

from httpx import AsyncClient, HTTPError
from typing import Optional, List


async def brave_web_search(query: str, http_client: AsyncClient, brave_api_key: str) -> str:
    """
    Helper function for web_search_tool - searches the web with the Brave API
    and returns a summary of all the top search results.

    Args are the same as the parent function except without the SearXNG base url.
    """
    headers = {
        'X-Subscription-Token': brave_api_key,
        'Accept': 'application/json',
    }
    
    try:
        response = await http_client.get(
            'https://api.search.brave.com/res/v1/web/search',
            params={
                'q': query,
                'count': 5,
                'text_decorations': True,
                'search_lang': 'en'
            },
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return f"Error searching the web with Brave: {str(e)}"

    results = []
    
    # Add web results in a nice formatted way
    web_results = data.get('web', {}).get('results', [])
    for item in web_results[:3]:
        title = item.get('title', '')
        description = item.get('description', '')
        url = item.get('url', '')
        if title and description:
            results.append(f"Title: {title}\nSummary: {description}\nSource: {url}\n")

    return "\n".join(results) if results else "No results found for the query."


async def searxng_web_search(query: str, http_client: AsyncClient, searxng_base_url: str) -> str:
    """
    Helper function for web_search_tool - searches the web with SearXNG
    and returns a list of the top search results with the most relevant snippet from each page.

    Args are the same as the parent function except without the Brave API key.
    """
    # Prepare the parameters for the request
    params = {'q': query, 'format': 'json'}
    
    try:
        response = await http_client.get(f"{searxng_base_url}/search", params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except Exception as e:
        return f"Error searching the web with SearXNG: {str(e)}"
    
    try:
        data = response.json()
    except Exception as e:
        return f"Error parsing the response from SearXNG: {str(e)}"
    
    results = ""
    for i, page in enumerate(data.get('results', []), 1):
        if i > 10:  # Limiting to the top 10 results, could make this a parameter for the function too
            break

        results += f"{i}. {page.get('title', 'No title')}"
        results += f"   URL: {page.get('url', 'No URL')}"
        results += f"   Content: {page.get('content', 'No content')[:300]}...\n\n"

    return results if results else "No results found for the query."


async def web_search_tool(query: str, http_client: AsyncClient, brave_api_key: str, searxng_base_url: str) -> str:
    """
    Search the web with a specific query and get a summary of the top search results.
    
    Args:
        query: The query for the web search
        http_client: The client for making HTTP requests to Brave or SearXNG
        brave_api_key: The optional key for Brave (will use SearXNG if this isn't defined)
        searxng_base_url: The optional base URL for SearXNG (will use Brave if this isn't defined)
        
    Returns:
        A summary of the web search.
        For Brave, this is a single paragraph.
        For SearXNG, this is a list of the top search results including the most relevant snippet from the page.
    """
    try:
        if brave_api_key:
            return await brave_web_search(query, http_client, brave_api_key)
        elif searxng_base_url:
            return await searxng_web_search(query, http_client, searxng_base_url)
        else:
            return "No search provider configured. Please set either BRAVE_API_KEY or SEARXNG_BASE_URL environment variable."
    except Exception as e:
        print(f"Exception during websearch: {e}")
        return str(e)
