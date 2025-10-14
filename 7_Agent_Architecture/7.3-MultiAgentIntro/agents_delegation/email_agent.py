"""
Email Draft Agent for creating Gmail drafts.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from .providers import get_llm_model
from .tools import create_email_draft_tool, list_email_drafts_tool

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an expert email writer. Your job is to create professional, clear, and contextually appropriate emails based on the user's request.

Guidelines:
- Always write professional but friendly emails
- Use clear, concise language
- Include appropriate greetings and closings
- Match the tone to the context provided
- If research content is provided, summarize key points professionally
- Always include a proper subject line if not provided
- Format emails with proper paragraphs and spacing

When creating emails:
1. Start with an appropriate greeting
2. Provide clear context or purpose
3. Include the main content/message
4. End with an appropriate closing
5. Use professional but warm tone
"""


@dataclass
class EmailAgentDependencies:
    """Dependencies for the email agent - only configuration, no tool instances."""
    gmail_credentials_path: str
    gmail_token_path: str
    session_id: Optional[str] = None


# Initialize the email agent
email_agent = Agent(
    get_llm_model(),
    deps_type=EmailAgentDependencies,
    system_prompt=SYSTEM_PROMPT
)


@email_agent.tool
async def create_gmail_draft(
    ctx: RunContext[EmailAgentDependencies],
    recipient_email: str,
    subject: str,
    body: str,
    cc_emails: Optional[str] = None,
    bcc_emails: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a Gmail draft.
    
    Args:
        recipient_email: Primary recipient email address
        subject: Email subject line
        body: Email body content
        cc_emails: Optional CC recipients (comma-separated)
        bcc_emails: Optional BCC recipients (comma-separated)
    
    Returns:
        Dictionary with draft creation results
    """
    try:
        # Parse email lists
        to_list = [recipient_email.strip()]
        cc_list = []
        bcc_list = []
        
        if cc_emails:
            cc_list = [email.strip() for email in cc_emails.split(',') if email.strip()]
        if bcc_emails:
            bcc_list = [email.strip() for email in bcc_emails.split(',') if email.strip()]
        
        # Create the draft using the pure tool function
        result = await create_email_draft_tool(
            credentials_path=ctx.deps.gmail_credentials_path,
            token_path=ctx.deps.gmail_token_path,
            to=to_list,
            subject=subject,
            body=body,
            cc=cc_list if cc_list else None,
            bcc=bcc_list if bcc_list else None
        )
        
        logger.info(f"Gmail draft created: {result.get('draft_id')}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create Gmail draft: {e}")
        return {
            "success": False,
            "error": str(e),
            "recipient": recipient_email,
            "subject": subject
        }


@email_agent.tool
async def list_gmail_drafts(
    ctx: RunContext[EmailAgentDependencies],
    max_results: int = 10
) -> Dict[str, Any]:
    """
    List existing Gmail drafts.
    
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
        logger.error(f"Failed to list Gmail drafts: {e}")
        return {
            "success": False,
            "error": str(e),
            "drafts": [],
            "count": 0
        }
