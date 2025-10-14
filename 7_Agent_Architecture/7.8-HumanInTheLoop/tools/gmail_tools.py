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
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.send"
    ]
    
    creds = None
    
    # Validate credentials file exists
    if not os.path.exists(credentials_path):
        raise Exception(
            f"Gmail credentials file not found at {credentials_path}. "
            "Please download credentials.json from Google Cloud Console and ensure "
            "the Gmail API is enabled with the correct OAuth2 scopes."
        )
    
    # Load existing token
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, scopes)
            logger.info("Loaded existing Gmail token")
        except Exception as e:
            logger.warning(f"Failed to load existing token: {e}")
            # Delete corrupt token file
            try:
                os.remove(token_path)
                logger.info("Removed corrupt token file")
            except:
                pass
            creds = None
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Gmail credentials refreshed successfully")
            except Exception as e:
                logger.warning(f"Failed to refresh credentials: {e}")
                logger.info("Will need to re-authenticate")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
                creds = flow.run_local_server(port=0, open_browser=False)
                logger.info("Gmail authentication completed successfully")
            except Exception as e:
                raise Exception(
                    f"Gmail authentication failed: {e}. "
                    "Please ensure credentials.json is valid and Gmail API is enabled."
                )
        
        # Save the credentials for the next run
        try:
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                logger.info(f"Gmail token saved to {token_path}")
        except Exception as e:
            logger.warning(f"Failed to save token: {e}")
    
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


async def read_inbox_emails_tool(
    credentials_path: str,
    token_path: str,
    max_results: int = 10,
    query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Read emails from inbox with optional filtering.
    
    Args:
        credentials_path: Path to Gmail credentials.json file
        token_path: Path to store/load Gmail token.json
        max_results: Maximum number of emails to return
        query: Optional Gmail search query (e.g., "is:unread", "from:example@email.com")
        
    Returns:
        Dictionary with email list and metadata
        
    Raises:
        Exception: If reading emails fails
    """
    try:
        # Get Gmail service
        try:
            service = _get_gmail_service(credentials_path, token_path)
        except Exception as auth_error:
            raise Exception(f"Gmail authentication failed: {str(auth_error)}")
        
        # Test connection with a simple API call first
        try:
            profile = service.users().getProfile(userId="me").execute()
            logger.info(f"Gmail authenticated for: {profile.get('emailAddress', 'unknown')}")
        except Exception as profile_error:
            raise Exception(f"Gmail API connection test failed: {str(profile_error)}")
        
        # Build query parameters
        list_params = {
            "userId": "me",
            "maxResults": max_results,
            "labelIds": ["INBOX"]
        }
        
        if query:
            list_params["q"] = query
        
        # Get list of message IDs
        logger.info(f"Listing emails with params: {list_params}")
        try:
            results = service.users().messages().list(**list_params).execute()
        except Exception as list_error:
            raise Exception(f"Gmail message listing failed: {str(list_error)}")
        
        if not results:
            logger.warning("Gmail API returned empty results")
            return {
                "success": True,
                "emails": [],
                "count": 0,
                "query_used": query,
                "max_results": max_results
            }
        
        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} message IDs")
        
        # Return early if no messages
        if not messages:
            return {
                "success": True,
                "emails": [],
                "count": 0,
                "query_used": query,
                "max_results": max_results
            }
        
        # Fetch detailed information for each message
        email_details = []
        for i, message in enumerate(messages):
            try:
                logger.info(f"Fetching details for message {i+1}/{len(messages)}: {message['id']}")
                
                msg_result = service.users().messages().get(
                    userId="me", 
                    id=message['id'],
                    format="full"
                ).execute()
                
                if not msg_result:
                    logger.warning(f"Empty result for message {message['id']}")
                    continue
                
                # Extract relevant information safely
                payload = msg_result.get('payload', {})
                headers = payload.get('headers', [])
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                
                # Get body text with robust error handling
                body = ""
                try:
                    if 'parts' in payload:
                        # Multi-part message
                        for part in payload['parts']:
                            if part.get('mimeType') == 'text/plain' and 'body' in part and 'data' in part['body']:
                                body_data = part['body']['data']
                                if body_data:  # Check if data is not empty
                                    body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                                    break
                    elif payload.get('mimeType') == 'text/plain' and 'body' in payload and 'data' in payload['body']:
                        # Single part message
                        body_data = payload['body']['data']
                        if body_data:  # Check if data is not empty
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                
                except Exception as body_error:
                    logger.warning(f"Failed to decode body for message {message['id']}: {body_error}")
                    body = f"[Body decoding failed: {str(body_error)}]"
                
                email_details.append({
                    "id": message['id'],
                    "thread_id": message.get('threadId', ''),
                    "subject": subject,
                    "from": sender,
                    "date": date,
                    "body": body[:500] + "..." if len(body) > 500 else body,  # Truncate long bodies
                    "snippet": msg_result.get('snippet', '')
                })
                
            except Exception as msg_error:
                logger.error(f"Failed to process message {message['id']}: {msg_error}")
                # Add a placeholder entry so we don't lose the message completely
                email_details.append({
                    "id": message['id'],
                    "thread_id": message.get('threadId', ''),
                    "subject": f"[Error loading message: {str(msg_error)}]",
                    "from": "Unknown",
                    "date": "Unknown",
                    "body": "",
                    "snippet": ""
                })
        
        logger.info(f"Successfully retrieved {len(email_details)} emails from inbox")
        
        return {
            "success": True,
            "emails": email_details,
            "count": len(email_details),
            "query_used": query,
            "max_results": max_results
        }
        
    except HttpError as e:
        error_msg = f"Gmail API error reading emails: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error reading emails: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)


async def send_email_tool(
    credentials_path: str,
    token_path: str,
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send an email (called only after approval).
    
    Args:
        credentials_path: Path to Gmail credentials.json file
        token_path: Path to store/load Gmail token.json
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        
    Returns:
        Dictionary with send results
        
    Raises:
        Exception: If sending email fails
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
        
        # Send the email
        send_result = (
            service.users()
            .messages()
            .send(userId="me", body=message)
            .execute()
        )
        
        message_id = send_result.get('id')
        thread_id = send_result.get('threadId')
        
        logger.info(f"Email sent successfully: {message_id}")
        
        return {
            "success": True,
            "message_id": message_id,
            "thread_id": thread_id,
            "sent_at": datetime.now().isoformat(),
            "recipients": to,
            "cc_recipients": cc or [],
            "bcc_recipients": bcc or [],
            "subject": subject
        }
        
    except HttpError as e:
        logger.error(f"Gmail API error sending email: {e}")
        raise Exception(f"Failed to send email: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        raise Exception(f"Unexpected error: {e}")