"""
Router Agent for LLM routing multi-agent system.

This lightweight agent determines which specialized agent should handle user requests.
"""

import logging
from typing import Literal
from dataclasses import dataclass

from pydantic_ai import Agent

from clients import get_model
from .deps import RouterDependencies
from .prompts import ROUTER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


@dataclass 
class RouterResponse:
    """Structured router decision for Pydantic AI output_type"""
    decision: Literal["web_search", "email_search", "rag_search", "fallback"]


# Initialize the router agent with smaller model for fast decisions
router_agent = Agent(
    get_model(use_smaller_model=True),
    output_type=RouterResponse,
    deps_type=RouterDependencies,
    system_prompt=ROUTER_SYSTEM_PROMPT,
    instrument=True
)


def create_router_agent() -> Agent:
    """
    Create a router agent instance.
    
    Returns:
        Configured router agent
    """
    return router_agent