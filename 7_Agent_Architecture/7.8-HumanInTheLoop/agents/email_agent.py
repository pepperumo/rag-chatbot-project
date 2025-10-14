"""
Email Management Agent for Human-in-the-Loop workflow.

This agent handles all email operations through Gmail API with intelligent automation
for reading and drafting, but requires explicit human approval for sending emails.
"""

from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from pydantic_ai import Agent
from pydantic_ai.tools import RunContext

from .deps import EmailAgentDependencies
from .prompts import EMAIL_MANAGEMENT_PROMPT
from clients import get_model
from tools.gmail_tools import (
    read_inbox_emails_tool,
    create_email_draft_tool,
    list_email_drafts_tool
)


class EmailAgentDecision(TypedDict, total=False):
    """Structured output for email agent with human-in-the-loop approval"""
    message: Optional[str]  # Conversational response (streamed)
    # Email approval request fields (when requesting send)
    recipients: Optional[List[str]]
    subject: Optional[str]
    body: Optional[str]
    request_send: bool  # True when requesting approval to send


async def read_inbox_emails(
    ctx: RunContext[EmailAgentDependencies],
    max_results: int = 10,
    query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Read emails from Gmail inbox with optional filtering.
    
    Args:
        max_results: Maximum number of emails to return
        query: Optional Gmail search query (e.g., "is:unread", "from:example@email.com")
        
    Returns:
        Dictionary with email list and metadata
    """
    try:
        result = await read_inbox_emails_tool(
            credentials_path=ctx.deps.gmail_credentials_path,
            token_path=ctx.deps.gmail_token_path,
            max_results=max_results,
            query=query
        )
        
        # Ensure result is properly formatted
        if not isinstance(result, dict):
            raise ValueError(f"Gmail tool returned invalid result type: {type(result)}")
        
        # Ensure required fields exist
        if "success" not in result:
            result["success"] = True
        if "emails" not in result:
            result["emails"] = []
        if "count" not in result:
            result["count"] = len(result.get("emails", []))
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read inbox emails: {str(e)}",
            "emails": [],
            "count": 0
        }


async def create_email_draft(
    ctx: RunContext[EmailAgentDependencies],
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a Gmail draft email.
    
    Args:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        
    Returns:
        Dictionary with draft creation results
    """
    try:
        result = await create_email_draft_tool(
            credentials_path=ctx.deps.gmail_credentials_path,
            token_path=ctx.deps.gmail_token_path,
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc
        )
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create email draft: {str(e)}",
            "draft_id": None
        }


async def list_email_drafts(
    ctx: RunContext[EmailAgentDependencies],
    max_results: int = 10
) -> Dict[str, Any]:
    """
    List Gmail draft emails.
    
    Args:
        max_results: Maximum number of drafts to return
        
    Returns:
        Dictionary with draft list
    """
    try:
        result = await list_email_drafts_tool(
            credentials_path=ctx.deps.gmail_credentials_path,
            token_path=ctx.deps.gmail_token_path,
            max_results=max_results
        )
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list email drafts: {str(e)}",
            "drafts": [],
            "count": 0
        }


# Create the email agent with structured output and tools
email_agent = Agent(
    model=get_model(),
    deps_type=EmailAgentDependencies,
    output_type=EmailAgentDecision,
    system_prompt=EMAIL_MANAGEMENT_PROMPT,
    tools=[
        read_inbox_emails,
        create_email_draft,
        list_email_drafts
    ],
    instrument=True
)