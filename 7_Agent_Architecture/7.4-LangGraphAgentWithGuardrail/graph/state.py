from typing import TypedDict, List, Optional
from pydantic_ai.messages import ModelMessage

class AgentState(TypedDict, total=False):
    """State for the RAG guardrail agent system (API mode)"""
    # Core workflow fields
    query: str                          # Original user query
    primary_response: str               # Primary agent response
    google_drive_urls: List[str]        # Extracted Google Drive URLs
    file_ids: List[str]                 # Extracted file IDs from URLs
    validation_result: Optional[str]    # Guardrail validation outcome
    feedback: Optional[str]             # Feedback for primary agent
    iteration_count: int                # Prevent infinite loops
    final_output: str                   # Validated final response
    message_history: List[bytes]        # Message history for agent handoff
    
    # API context fields
    session_id: str                     # API session ID
    request_id: str                     # Request tracking ID
    pydantic_message_history: List[ModelMessage]  # Pydantic AI messages
    guardrail_message: Optional[str]    # Formatted guardrail message
    fallback_triggered: Optional[bool]  # Whether fallback was triggered



def should_continue_iteration(state: AgentState, max_iterations: int = 3) -> bool:
    """
    Check if we should continue iterating based on validation results.
    
    Args:
        state: Current state
        max_iterations: Maximum number of iterations allowed
        
    Returns:
        True if should continue, False otherwise
    """
    print("should_continue_iteration", state["iteration_count"])
    print("should_continue_iteration", state["validation_result"])
    if state["iteration_count"] >= max_iterations:
        return False
    
    if state["validation_result"] == "valid":
        return False
    
    return True



