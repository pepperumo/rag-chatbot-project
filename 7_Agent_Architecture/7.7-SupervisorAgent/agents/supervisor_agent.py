"""
Supervisor Agent for intelligent coordination and delegation in multi-agent workflow.

This agent serves as the central coordinator, making intelligent decisions about task delegation
and providing final responses with streaming structured output support.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from pydantic_ai import Agent

from clients import get_model
from .prompts import SUPERVISOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class SupervisorDecision(TypedDict, total=False):
    """Structured output for supervisor agent decisions with streaming support"""
    messages: Optional[str] = Field(
        None, 
        description="Streamed response to user - only populate if providing final response"
    )
    delegate_to: Optional[str] = Field(
        None,
        description="Agent to delegate to next: 'web_research', 'task_management', 'email_draft', or None for final response"
    )
    reasoning: str = Field(
        description="Reasoning for this decision - why delegating or providing final response"
    )
    final_response: bool = Field(
        default=False,
        description="True if this is the final response to user, False if delegating"
    )


@dataclass
class SupervisorAgentDependencies:
    """Dependencies for the supervisor agent - session management and configuration."""
    session_id: Optional[str] = None




# Initialize the supervisor agent with structured output streaming
supervisor_agent = Agent(
    get_model(),
    deps_type=SupervisorAgentDependencies,
    output_type=SupervisorDecision,
    system_prompt=SUPERVISOR_SYSTEM_PROMPT,
    instrument=True
)


# Convenience function to create supervisor agent with dependencies
def create_supervisor_agent(session_id: Optional[str] = None) -> Agent:
    """
    Create a supervisor agent with specified dependencies.
    
    Args:
        session_id: Optional session identifier for tracking
        
    Returns:
        Configured supervisor agent
    """
    return supervisor_agent