"""
Email Draft Agent for sequential research and outreach system.

This agent creates Gmail drafts based on accumulated research data.
"""

import logging
from typing import Dict, Any, Optional
from pydantic_ai import Agent, RunContext

from clients import get_model
from .deps import EmailDraftAgentDependencies
from .prompts import EMAIL_DRAFT_SYSTEM_PROMPT
from tools.gmail_tools import create_email_draft_tool

logger = logging.getLogger(__name__)


# Initialize the email draft agent
email_draft_agent = Agent(
    get_model(use_smaller_model=False),
    deps_type=EmailDraftAgentDependencies,
    system_prompt=EMAIL_DRAFT_SYSTEM_PROMPT,
    instrument=True
)


@email_draft_agent.tool
async def create_gmail_draft(
    ctx: RunContext[EmailDraftAgentDependencies],
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
