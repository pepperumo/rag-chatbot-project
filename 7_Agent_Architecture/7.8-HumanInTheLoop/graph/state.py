from typing import TypedDict, List, Optional
from pydantic_ai.messages import ModelMessage


class EmailAgentState(TypedDict, total=False):
    """State for email agent workflow with human-in-the-loop approval"""
    # Conversation
    query: str
    session_id: str
    request_id: str
    pydantic_message_history: List[ModelMessage]
    
    # Email fields for approval request
    email_recipients: Optional[List[str]]
    email_subject: Optional[str]
    email_body: Optional[str]
    
    # Approval response from human
    approval_granted: Optional[bool]
    approval_feedback: Optional[str]
    
    # Revision handling
    revision_requested: Optional[bool]
    previous_email_recipients: Optional[List[str]]
    previous_email_subject: Optional[str]
    previous_email_body: Optional[str]
    
    # Message tracking
    message_history: List[bytes]  # For pydantic message serialization
    
    # Workflow control
    _resuming_from_interrupt: Optional[bool]  # Flag to prevent duplicate approval UI
    
    # API context (preserved for compatibility)
    conversation_title: Optional[str]
    is_new_conversation: Optional[bool]