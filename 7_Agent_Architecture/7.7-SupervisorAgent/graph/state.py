from typing import TypedDict, List, Optional
from pydantic_ai.messages import ModelMessage


class SupervisorAgentState(TypedDict, total=False):
    """LangGraph state for supervisor agent workflow with intelligent delegation"""
    # Input and session management
    query: str
    session_id: str  
    request_id: str
    iteration_count: int  # Track delegation iterations for 20-iteration limit
    
    # Supervisor coordination
    supervisor_reasoning: str  # Last supervisor decision reasoning
    shared_state: List[str]  # Append-only list where all sub-agents add summaries
    delegate_to: Optional[str]  # Current delegation target
    
    # Final response and workflow control
    final_response: str
    workflow_complete: bool
    
    # Message history management (only supervisor updates when providing final response)
    pydantic_message_history: List[ModelMessage]
    message_history: List[bytes]
    
    # API context (preserved for compatibility)
    conversation_title: Optional[str]
    is_new_conversation: Optional[bool]