from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class EmailAgentDependencies:
    """Dependencies for the human-in-the-loop email agent"""
    gmail_credentials_path: str
    gmail_token_path: str
    session_id: Optional[str] = None

def create_email_deps(session_id: Optional[str] = None) -> EmailAgentDependencies:
    """Create EmailAgentDependencies instance"""
    gmail_credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/credentials.json")
    gmail_token_path = os.getenv("GMAIL_TOKEN_PATH", "credentials/token.json")
    
    return EmailAgentDependencies(
        gmail_credentials_path=gmail_credentials_path,
        gmail_token_path=gmail_token_path,
        session_id=session_id
    )