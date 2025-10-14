"""
Email agent for handoff system.

This agent handles email-related tasks when handed off from the research agent.
It reuses the existing email tools but is designed to be called directly
rather than as a subagent.
"""

from dataclasses import dataclass
from typing import Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName

from agents_delegation.providers import get_llm_model
from agents_delegation.tools import create_email_draft_tool, list_email_drafts_tool
from agents_delegation.models import EmailDraftResponse


@dataclass
class EmailAgentDependencies:
    """Dependencies for the email agent."""
    
    gmail_credentials_path: str
    gmail_token_path: str
    session_id: Optional[str] = None


# Email agent for handoff
email_agent = Agent(
    model=get_llm_model(),
    deps_type=EmailAgentDependencies,
    output_type=str,
    system_prompt=(
        "You are an email drafting specialist. Your role is to create professional, "
        "clear, and well-structured emails based on the provided context and research. "
        "When creating emails:\n"
        "1. Use a professional but friendly tone\n"
        "2. Structure the email with clear sections\n"
        "3. Include relevant research findings when provided\n"
        "4. Ensure the subject line is descriptive and engaging\n"
        "5. Try to create a Gmail draft when possible, but if that fails, provide the email content\n"
        "6. Provide a brief confirmation of what was created\n\n"
        "You have access to Gmail tools to create and manage email drafts."
    ),
)


@email_agent.tool
async def create_gmail_draft(
    ctx: RunContext[EmailAgentDependencies],
    recipient_email: str,
    subject: str,
    body: str,
) -> dict:
    """
    Create a Gmail draft email.

    Args:
        ctx: Runtime context with dependencies
        recipient_email: Email address of the recipient
        subject: Email subject line
        body: Email body content

    Returns:
        dict: Information about the created draft
    """
    try:
        result = await create_email_draft_tool(
            credentials_path=ctx.deps.gmail_credentials_path,
            token_path=ctx.deps.gmail_token_path,
            to=[recipient_email],  # Fix: pass as list, correct parameter name
            subject=subject,
            body=body,
        )
        
        return {
            "success": True,
            "draft_id": result.get("draft_id"),
            "message": result.get("message", "Email draft created successfully"),
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to create email draft: {str(e)}",
        }


@email_agent.tool
async def list_gmail_drafts(
    ctx: RunContext[EmailAgentDependencies],
    max_results: int = 10,
) -> dict:
    """
    List existing Gmail drafts.

    Args:
        ctx: Runtime context with dependencies
        max_results: Maximum number of drafts to return

    Returns:
        dict: List of existing drafts
    """
    try:
        result = await list_email_drafts_tool(
            credentials_path=ctx.deps.gmail_credentials_path,
            token_path=ctx.deps.gmail_token_path,
            max_results=max_results,
        )
        return result
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to list drafts: {str(e)}",
        }