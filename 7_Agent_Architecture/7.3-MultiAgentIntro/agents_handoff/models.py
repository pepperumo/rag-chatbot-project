"""
Data models for agent handoff system.

This module defines the Pydantic models used for structured outputs
in the agent handoff pattern, where agents can either respond directly
or hand off to another agent.
"""

from typing import Optional, Union, Literal
from pydantic import BaseModel, Field

# Re-export the original models for reuse
from agents_delegation.models import (
    ResearchQuery,
    BraveSearchResult,
    EmailDraft,
    EmailDraftResponse,
    ResearchEmailRequest,
    ResearchResponse,
    AgentResponse,
    ChatMessage,
    SessionState,
)


class DirectResponse(BaseModel):
    """Direct response from the current agent."""
    
    response_type: Literal["direct"] = "direct"
    message: str = Field(..., description="The direct response message to the user")


class EmailHandoff(BaseModel):
    """Request to hand off to the email agent."""
    
    response_type: Literal["email_handoff"] = "email_handoff"
    recipient_email: str = Field(..., description="Email address of the recipient")
    subject: str = Field(..., description="Subject line for the email")
    context: str = Field(..., description="Context or instructions for the email")
    research_summary: Optional[str] = Field(None, description="Research summary to include in email")


# Union type for the research agent's structured output
ResearchAgentOutput = Union[DirectResponse, EmailHandoff]


class HandoffResult(BaseModel):
    """Result from an agent handoff operation."""
    
    success: bool = Field(..., description="Whether the handoff was successful")
    final_response: str = Field(..., description="The final response to the user")
    agent_used: str = Field(..., description="Name of the agent that provided the final response")
    error_message: Optional[str] = Field(None, description="Error message if handoff failed")