"""
Web search agent package.

This package contains the implementation of a web search agent using Pydantic AI.
The agent can search the web using either Brave Search API or SearXNG based on
environment configuration.
"""

from .agent import run_web_search_agent, agent, get_model, AgentDeps
from .tools import web_search_tool

__all__ = [
    "agent",
    "get_model",
    "AgentDeps",
    "run_web_search_agent",
    "web_search_tool",
]
