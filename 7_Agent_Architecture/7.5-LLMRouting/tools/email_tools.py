"""
Email search tool functions for the multi-agent routing system.
Pure tool functions for Gmail search with readonly permissions.
"""

import os
import logging
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def _get_gmail_service(credentials_path: str, token_path: str, scopes: List[str]) -> Any:
    """
    Get authenticated Gmail service with specified scopes.
    
    Args:
        credentials_path: Path to credentials.json file
        token_path: Path to token.json file
        scopes: List of OAuth scopes to request
        
    Returns:
        Authenticated Gmail service object
    """
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


async def search_emails_tool(
    credentials_path: str,
    token_path: str, 
    query: str,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Gmail API email search with readonly permissions.
    
    Args:
        credentials_path: Path to Gmail credentials.json file
        token_path: Path to store/load Gmail token.json
        query: Gmail search query (supports Gmail search operators)
        max_results: Maximum number of results to return (1-50)
        
    Returns:
        Dictionary with search results
        
    Raises:
        Exception: If search fails
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # CRITICAL: Use gmail.readonly scope
    scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    
    # Ensure max_results is within valid range (Gmail API limit)
    max_results = min(max(max_results, 1), 50)
    
    try:
        service = _get_gmail_service(credentials_path, token_path, scopes)
        
        # PATTERN: Gmail API messages.list with query
        results = service.users().messages().list(
            userId='me',
            q=query,  # Gmail search syntax: "from:user@example.com subject:project"
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        email_results = []
        
        # PATTERN: Extract metadata for each message
        for msg in messages:
            try:
                message = service.users().messages().get(
                    userId='me', 
                    id=msg['id'],
                    format='metadata'  # Headers only, not full body
                ).execute()
                
                # PATTERN: Parse headers for display
                headers = message['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                
                email_results.append({
                    "id": msg['id'],
                    "subject": subject, 
                    "from": sender,
                    "date": date,
                    "snippet": message.get('snippet', '')
                })
            except Exception as e:
                logger.warning(f"Failed to get message {msg['id']}: {e}")
                continue
        
        logger.info(f"Found {len(email_results)} emails for query: {query}")
        return {"success": True, "results": email_results, "count": len(email_results)}
        
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        # PATTERN: Graceful error handling
        return {"success": False, "error": f"Gmail API error: {str(e)}", "results": [], "count": 0}
    except Exception as e:
        logger.error(f"Email search error: {e}")
        # PATTERN: Graceful error handling
        return {"success": False, "error": str(e), "results": [], "count": 0}


async def get_email_content_tool(
    credentials_path: str,
    token_path: str,
    message_id: str
) -> Dict[str, Any]:
    """
    Get full content of a specific email message.
    
    Args:
        credentials_path: Path to Gmail credentials.json file
        token_path: Path to store/load Gmail token.json
        message_id: Gmail message ID
        
    Returns:
        Dictionary with email content
        
    Raises:
        Exception: If retrieval fails
    """
    if not message_id or not message_id.strip():
        raise ValueError("Message ID cannot be empty")
    
    # CRITICAL: Use gmail.readonly scope
    scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    
    try:
        service = _get_gmail_service(credentials_path, token_path, scopes)
        
        # Get full message content
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = message['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        to = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
        
        # Extract body (simplified - gets text/plain part)
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        import base64
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        else:
            if message['payload']['mimeType'] == 'text/plain':
                if 'data' in message['payload']['body']:
                    import base64
                    body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        return {
            "success": True,
            "message_id": message_id,
            "subject": subject,
            "from": sender,
            "to": to,
            "date": date,
            "body": body,
            "snippet": message.get('snippet', '')
        }
        
    except HttpError as e:
        logger.error(f"Gmail API error getting message {message_id}: {e}")
        return {"success": False, "error": f"Gmail API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error getting message {message_id}: {e}")
        return {"success": False, "error": str(e)}