from openai import AsyncOpenAI
from supabase import Client
from httpx import AsyncClient
from dataclasses import dataclass
from typing import Optional
import os

from clients import get_agent_clients

@dataclass
class AgentDeps:
    """Dependencies for RAG agents including optional feedback for guardrail system"""
    supabase: Client
    embedding_client: AsyncOpenAI
    http_client: AsyncClient
    feedback: Optional[str] = None

@dataclass
class RouterDependencies:
    """Router agent dependencies - minimal for fast decisions"""
    session_id: Optional[str] = None

@dataclass
class AgentDependencies:
    """Shared dependencies for search agents"""
    brave_api_key: str
    gmail_credentials_path: str
    gmail_token_path: str
    supabase: Client
    embedding_client: AsyncOpenAI
    http_client: AsyncClient
    session_id: Optional[str] = None

def create_agent_deps(feedback: Optional[str] = None) -> AgentDeps:
    """Create AgentDeps instance with optional feedback"""
    embedding_client, supabase, http_client = get_agent_clients()
    
    return AgentDeps(
        supabase=supabase,
        embedding_client=embedding_client,
        http_client=http_client,
        feedback=feedback
    )

def create_router_deps(session_id: Optional[str] = None) -> RouterDependencies:
    """Create RouterDependencies instance for fast routing decisions"""
    return RouterDependencies(session_id=session_id)

def create_search_agent_deps(session_id: Optional[str] = None) -> AgentDependencies:
    """Create AgentDependencies instance for search agents"""
    embedding_client, supabase, http_client = get_agent_clients()
    
    # Get environment variables for external APIs
    brave_api_key = os.getenv("BRAVE_API_KEY", "")
    gmail_credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/credentials.json")
    gmail_token_path = os.getenv("GMAIL_TOKEN_PATH", "credentials/token.json")
    
    return AgentDependencies(
        brave_api_key=brave_api_key,
        gmail_credentials_path=gmail_credentials_path,
        gmail_token_path=gmail_token_path,
        supabase=supabase,
        embedding_client=embedding_client,
        http_client=http_client,
        session_id=session_id
    )