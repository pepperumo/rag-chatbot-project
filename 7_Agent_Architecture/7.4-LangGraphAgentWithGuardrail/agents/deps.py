from openai import AsyncOpenAI
from supabase import Client
from httpx import AsyncClient
from dataclasses import dataclass
from typing import Optional

from clients import get_agent_clients

@dataclass
class AgentDeps:
    """Dependencies for RAG agents including optional feedback for guardrail system"""
    supabase: Client
    embedding_client: AsyncOpenAI
    http_client: AsyncClient
    feedback: Optional[str] = None

def create_agent_deps(feedback: Optional[str] = None) -> AgentDeps:
    """Create AgentDeps instance with optional feedback"""
    embedding_client, supabase, http_client = get_agent_clients()
    
    return AgentDeps(
        supabase=supabase,
        embedding_client=embedding_client,
        http_client=http_client,
        feedback=feedback
    )