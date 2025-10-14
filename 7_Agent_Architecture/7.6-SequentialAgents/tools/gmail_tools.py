"""
Gmail tool functions for the sequential agent system.
These are standalone functions that can be imported and used by any agent.
"""

import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def _get_gmail_service(credentials_path: str, token_path: str) -> Any:
    """
    Get authenticated Gmail service.
    
    Args:
        credentials_path: Path to credentials.json file
        token_path: Path to token.json file
        
    Returns:
        Authenticated Gmail service object
    """
    scopes = [
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.send"
    ]
    
    creds = None
    
    # Load existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Gmail credentials refreshed successfully")
            except Exception as e:
                logger.warning(f"Failed to refresh credentials: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(credentials_path):
                raise Exception(
                    f"Gmail credentials file not found at {credentials_path}. "
                    "Please download credentials.json from Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)
            logger.info("Gmail authentication completed successfully")
        
        # Save the credentials for the next run
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            logger.info(f"Gmail token saved to {token_path}")
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service initialized successfully")
        return service
    except Exception as e:
        raise Exception(f"Failed to build Gmail service: {e}")


def _create_email_message(to: List[str], subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> dict:
    """
    Create a message for the Gmail API.
    
    Args:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        
    Returns:
        Encoded message dict
    """
    message = MIMEMultipart()
    message['to'] = ', '.join(to)
    message['subject'] = subject
    
    if cc:
        message['cc'] = ', '.join(cc)
    if bcc:
        message['bcc'] = ', '.join(bcc)
    
    # Attach the body
    body_part = MIMEText(body, 'plain')
    message.attach(body_part)
    
    # Encode the message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    return {'raw': raw_message}


async def create_email_draft_tool(
    credentials_path: str,
    token_path: str,
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Pure function to create a Gmail draft.
    
    Args:
        credentials_path: Path to Gmail credentials.json file
        token_path: Path to store/load Gmail token.json
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        
    Returns:
        Dictionary with draft creation results
        
    Raises:
        Exception: If draft creation fails
    """
    if not to or len(to) == 0:
        raise ValueError("At least one recipient is required")
    
    if not subject or not subject.strip():
        raise ValueError("Subject is required")
    
    if not body or not body.strip():
        raise ValueError("Body is required")
    
    try:
        # Get Gmail service
        service = _get_gmail_service(credentials_path, token_path)
        
        # Create the message
        message = _create_email_message(to, subject, body, cc, bcc)
        create_message = {"message": message}
        
        # Create the draft
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body=create_message)
            .execute()
        )
        
        draft_id = draft.get('id')
        message_id = draft.get('message', {}).get('id')
        thread_id = draft.get('message', {}).get('threadId')
        
        logger.info(f"Gmail draft created successfully: {draft_id}")
        
        return {
            "success": True,
            "draft_id": draft_id,
            "message_id": message_id,
            "thread_id": thread_id,
            "created_at": datetime.now().isoformat(),
            "recipients": to,
            "subject": subject
        }
        
    except HttpError as e:
        logger.error(f"Gmail API error creating draft: {e}")
        raise Exception(f"Failed to create draft: {e}")
    except Exception as e:
        logger.error(f"Unexpected error creating draft: {e}")
        raise Exception(f"Unexpected error: {e}")


async def list_email_drafts_tool(
    credentials_path: str,
    token_path: str,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Pure function to list Gmail drafts.
    
    Args:
        credentials_path: Path to Gmail credentials.json file
        token_path: Path to store/load Gmail token.json
        max_results: Maximum number of drafts to return
        
    Returns:
        Dictionary with draft list
        
    Raises:
        Exception: If listing fails
    """
    try:
        # Get Gmail service
        service = _get_gmail_service(credentials_path, token_path)
        
        results = (
            service.users()
            .drafts()
            .list(userId="me", maxResults=max_results)
            .execute()
        )
        
        drafts = results.get('drafts', [])
        logger.info(f"Retrieved {len(drafts)} Gmail drafts")
        
        return {
            "success": True,
            "drafts": drafts,
            "count": len(drafts)
        }
        
    except HttpError as e:
        logger.error(f"Gmail API error listing drafts: {e}")
        raise Exception(f"Failed to list drafts: {e}")
    except Exception as e:
        logger.error(f"Unexpected error listing drafts: {e}")
        raise Exception(f"Unexpected error: {e}")