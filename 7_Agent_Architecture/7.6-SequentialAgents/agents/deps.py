from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class GuardrailDependencies:
    """Guardrail agent dependencies - minimal for fast decisions"""
    session_id: Optional[str] = None

@dataclass
class ResearchAgentDependencies:
    """Dependencies for the research agent"""
    brave_api_key: str
    session_id: Optional[str] = None

@dataclass
class EmailDraftAgentDependencies:
    """Dependencies for the email draft agent"""
    gmail_credentials_path: str
    gmail_token_path: str
    session_id: Optional[str] = None

def create_guardrail_deps(session_id: Optional[str] = None) -> GuardrailDependencies:
    """Create GuardrailDependencies instance for fast guardrail decisions"""
    return GuardrailDependencies(session_id=session_id)

def create_research_deps(session_id: Optional[str] = None) -> ResearchAgentDependencies:
    """Create ResearchAgentDependencies instance"""
    brave_api_key = os.getenv("BRAVE_API_KEY", "")
    
    return ResearchAgentDependencies(
        brave_api_key=brave_api_key,
        session_id=session_id
    )

def create_email_deps(session_id: Optional[str] = None) -> EmailDraftAgentDependencies:
    """Create EmailDraftAgentDependencies instance"""
    gmail_credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/credentials.json")
    gmail_token_path = os.getenv("GMAIL_TOKEN_PATH", "credentials/token.json")
    
    return EmailDraftAgentDependencies(
        gmail_credentials_path=gmail_credentials_path,
        gmail_token_path=gmail_token_path,
        session_id=session_id
    )