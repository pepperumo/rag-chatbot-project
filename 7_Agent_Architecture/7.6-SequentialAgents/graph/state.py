from typing import TypedDict, List, Optional, Dict, Any
from pydantic_ai.messages import ModelMessage

class SequentialAgentState(TypedDict, total=False):
    """LangGraph state for sequential agent workflow"""
    # Input
    query: str
    session_id: str  
    request_id: str
    
    # Guardrail output
    is_research_request: bool
    routing_reason: str
    
    # Research outputs (accumulated)
    research_summary: str
    research_sources: List[Dict[str, str]]
    
    # Enrichment outputs (accumulated)
    enrichment_summary: str
    enriched_data: Dict[str, Any]
    
    # Email draft output
    email_draft_created: bool
    draft_id: Optional[str]
    
    # Final response
    final_response: str
    agent_type: str
    
    # Message history management
    pydantic_message_history: List[ModelMessage]
    message_history: List[bytes]  # Only populated by final agent
    
    # API context
    conversation_title: Optional[str]
    is_new_conversation: Optional[bool]