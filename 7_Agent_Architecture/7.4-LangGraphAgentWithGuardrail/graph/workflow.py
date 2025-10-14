from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import json
from typing import List, Dict, Any, Optional

from graph.state import AgentState, should_continue_iteration
from agents.primary_agent import primary_agent
from agents.guardrail_agent import guardrail_agent
from agents.deps import create_agent_deps
from tools.validation_tools import extract_google_drive_urls, extract_file_ids_from_urls
from pydantic_ai.messages import ModelMessage, PartDeltaEvent, PartStartEvent, TextPartDelta
from pydantic_ai import Agent

load_dotenv()


async def primary_agent_node(state: AgentState, writer) -> dict:
    """
    Primary agent node - generates RAG response.
    
    Args:
        state: Current workflow state
        writer: Stream writer for real-time output
        
    Returns:
        State updates
    """
    try:
        # Create dependencies with optional feedback
        deps = create_agent_deps(feedback=state.get("feedback"))
        
        # Use pydantic_message_history from state (API mode only)
        message_history = state.get("pydantic_message_history", [])
        agent_input = state["query"]
        
        # Run primary agent with streaming
        full_response = ""
        streaming_success = False
        
        try:
            # PATTERN: Use .iter() for streaming with message history
            async with primary_agent.iter(agent_input, deps=deps, message_history=message_history) as run:
                async for node in run:
                    if primary_agent.is_model_request_node(node):
                        # Stream tokens from the model's request
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                    writer(event.part.content)
                                    full_response += event.part.content
                                elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                    delta = event.delta.content_delta
                                    writer(delta)
                                    full_response += delta
                streaming_success = True
                
                # Get final result and capture new messages
                if run.result and run.result.data and not full_response:
                    full_response = str(run.result.data)
                    writer(full_response)
                
                # Capture new messages for conversation history
                new_messages = run.result.new_messages_json()
                    
        except Exception as stream_error:
            # PATTERN: Non-streaming fallback
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await primary_agent.run(agent_input, deps=deps, message_history=message_history)
            full_response = str(run.data) if run.data else "No response generated"
            writer(full_response)
            streaming_success = False
            
            # Capture new messages from fallback run
            new_messages = run.new_messages_json()
        
        return {
            "primary_response": full_response,
            "message_history": [new_messages]
        }
        
    except Exception as e:
        error_msg = f"Error in primary agent: {str(e)}"
        print(error_msg)
        return {
            "primary_response": error_msg,
            "message_history": []
        }

async def guardrail_agent_node(state: AgentState, writer) -> dict:
    """
    Guardrail validation node - validates citations.
    
    Args:
        state: Current workflow state
        writer: Stream writer for real-time output
        
    Returns:
        State updates
    """
    try:
        # Stream validation message with better formatting
        validation_message = "\n\n### 🛡️ Guardrail Validation\n\nValidating response for accuracy and proper citations...\n"
        if writer:
            writer(validation_message)
        
        # Create dependencies
        deps = create_agent_deps()
        
        # Create validation query
        validation_query = f"""
        Validate this response and its citations:
        
        Original Query: {state['query']}
        
        Response to Validate: {state['primary_response']}
        
        Please check if all citations are valid and relevant.
        """
        
        # Run guardrail validation
        result = await guardrail_agent.run(validation_query, deps=deps)
        validation_output = result.data
        
        # Extract Google Drive URLs
        google_drive_urls = extract_google_drive_urls(state["primary_response"])
        file_ids = extract_file_ids_from_urls(google_drive_urls)
        
        # Determine validation result
        if "VALID" in validation_output and not validation_output.startswith("INVALID"):
            # Stream success message with better formatting
            success_message = "\n### ✅ Validation Passed\n\nAll citations are properly supported.\n\n"
            if writer:
                writer(success_message)
                
            return {
                "validation_result": "valid",
                "google_drive_urls": google_drive_urls,
                "file_ids": file_ids,
                "final_output": state["primary_response"],
                "guardrail_message": success_message
            }
        else:
            # Stream failure message with better formatting
            failure_message = f"\n### ❌ Validation Failed\n\n{validation_output}\n\nRequesting improved response...\n\n"
            if writer:
                writer(failure_message)
                
            return {
                "validation_result": "invalid",
                "google_drive_urls": google_drive_urls,
                "file_ids": file_ids,
                "feedback": validation_output,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "guardrail_message": failure_message
            }
            
    except Exception as e:
        error_msg = f"Error in guardrail agent: {str(e)}"
        print(error_msg)
        
        # Default pass-through with better formatting
        default_message = "\n### ⚠️ Validation Error\n\nValidation failed, defaulting to pass-through mode.\n\n"
        if writer:
            writer(default_message)
        
        # Extract URLs as fallback
        google_drive_urls = extract_google_drive_urls(state["primary_response"])
        file_ids = extract_file_ids_from_urls(google_drive_urls)
        
        return {
            "validation_result": "valid",
            "google_drive_urls": google_drive_urls,
            "file_ids": file_ids,
            "final_output": state["primary_response"],
            "guardrail_message": default_message,
            "guardrail_error": error_msg
        }

async def fallback_node(state: AgentState, writer) -> dict:
    """
    Fallback node - streams a final message when max iterations reached.
    
    Args:
        state: Current workflow state
        writer: Stream writer for real-time output
        
    Returns:
        State updates
    """
    fallback_message = f"\n\n### ⚠️ Maximum Iterations Reached\n\nUnable to provide a fully validated response after {state['iteration_count']} attempts.\n\n**Last feedback:** {state.get('feedback', 'No feedback available')}\n\n"
    
    if writer:
        writer(fallback_message)
    
    return {
        "final_output": state["primary_response"],
        "fallback_triggered": True
    }


def route_after_validation(state: AgentState) -> str:
    """
    Route after validation based on results.
    
    Args:
        state: Current workflow state
        
    Returns:
        Next node name
    """
    # Check if we should continue iterating
    if should_continue_iteration(state):
        return "primary_agent_node"
    else:
        # Check if we hit max iterations and need fallback
        if state.get("iteration_count", 0) >= 3 and state.get("validation_result") == "invalid":
            return "fallback_node"
        return "end"


def create_workflow():
    """Create and configure the LangGraph workflow"""
    
    # Create state graph
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("primary_agent_node", primary_agent_node)
    builder.add_node("guardrail_agent_node", guardrail_agent_node)
    builder.add_node("fallback_node", fallback_node)
    
    # Set entry point
    builder.add_edge(START, "primary_agent_node")
    
    # Add edges
    builder.add_edge("primary_agent_node", "guardrail_agent_node")
    
    # Add conditional routing after validation
    builder.add_conditional_edges(
        "guardrail_agent_node",
        route_after_validation,
        {
            "end": END,
            "primary_agent_node": "primary_agent_node",
            "fallback_node": "fallback_node"
        }
    )
    
    # Fallback always goes to END
    builder.add_edge("fallback_node", END)
    
    # Compile the graph
    return builder.compile()

# Create the workflow instance
workflow = create_workflow()


def create_api_initial_state(
    query: str,
    session_id: str,
    request_id: str,
    pydantic_message_history: Optional[List[ModelMessage]] = None
) -> AgentState:
    """Create initial state for API mode"""
    return {
        "query": query,
        "primary_response": "",
        "google_drive_urls": [],
        "file_ids": [],
        "validation_result": None,
        "feedback": None,
        "iteration_count": 0,
        "final_output": "",
        "message_history": [],
        "session_id": session_id,
        "request_id": request_id,
        "pydantic_message_history": pydantic_message_history or []
    }


def extract_api_response_data(state: AgentState) -> Dict[str, Any]:
    """Extract response data for API return"""
    return {
        "session_id": state.get("session_id"),
        "request_id": state.get("request_id"),
        "query": state["query"],
        "response": state.get("final_output", ""),
        "citations": state.get("google_drive_urls", []),
        "validation_passed": state.get("validation_result") == "valid",
        "iterations": state.get("iteration_count", 0),
        "conversation_title": state.get("conversation_title"),
        "is_new_conversation": state.get("is_new_conversation", False)
    }
