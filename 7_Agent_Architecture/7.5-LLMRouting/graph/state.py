from typing import TypedDict, List, Optional
from pydantic_ai.messages import ModelMessage

class RouterState(TypedDict, total=False):
    """LangGraph state for routing workflow"""
    # Input
    query: str
    session_id: str  
    request_id: str
    
    # Router output
    routing_decision: str
    router_confidence: str
    
    # Agent output  
    final_response: str
    agent_type: str
    streaming_success: bool
    message_history: List[ModelMessage]
    
    # API context (preserved for compatibility)
    pydantic_message_history: List[ModelMessage]
    conversation_title: Optional[str]
    is_new_conversation: Optional[bool]