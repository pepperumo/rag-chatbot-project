"""
Supervisor Agent Workflow for Intelligent Multi-Agent Coordination.

This module implements a LangGraph workflow with a supervisor pattern that intelligently
delegates tasks between web research, task management, and email drafting agents.
"""

from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import os

from graph.state import SupervisorAgentState
from agents.supervisor_agent import supervisor_agent, SupervisorAgentDependencies
from agents.web_research_agent import web_research_agent, WebResearchAgentDependencies
from agents.task_management_agent import task_management_agent, TaskManagementAgentDependencies
from agents.email_draft_agent import email_draft_agent, EmailDraftAgentDependencies
from agents.fallback_agent import fallback_agent

from pydantic_ai.messages import ModelMessage

load_dotenv()


def create_supervisor_deps(session_id: Optional[str] = None) -> SupervisorAgentDependencies:
    """Create supervisor agent dependencies"""
    return SupervisorAgentDependencies(session_id=session_id)


def create_web_research_deps(session_id: Optional[str] = None) -> WebResearchAgentDependencies:
    """Create web research agent dependencies"""
    brave_api_key = os.getenv("BRAVE_API_KEY")
    if not brave_api_key:
        raise ValueError("BRAVE_API_KEY environment variable is required")
    return WebResearchAgentDependencies(
        brave_api_key=brave_api_key,
        session_id=session_id
    )


def create_task_management_deps(session_id: Optional[str] = None) -> TaskManagementAgentDependencies:
    """Create task management agent dependencies"""
    asana_api_key = os.getenv("ASANA_API_KEY")
    asana_workspace_gid = os.getenv("ASANA_WORKSPACE_GID")
    if not asana_api_key:
        raise ValueError("ASANA_API_KEY environment variable is required")
    return TaskManagementAgentDependencies(
        asana_api_key=asana_api_key,
        asana_workspace_gid=asana_workspace_gid,
        session_id=session_id
    )


def create_email_deps(session_id: Optional[str] = None) -> EmailDraftAgentDependencies:
    """Create email draft agent dependencies"""
    gmail_credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials/credentials.json")
    gmail_token_path = "./credentials/token.json"
    return EmailDraftAgentDependencies(
        gmail_credentials_path=gmail_credentials_path,
        gmail_token_path=gmail_token_path,
        session_id=session_id
    )


async def supervisor_node(state: SupervisorAgentState, writer) -> dict:
    """
    Supervisor node with structured output streaming and intelligent delegation.
    
    CRITICAL: Stream messages field when providing final response, with fallback
    """
    try:
        deps = create_supervisor_deps(session_id=state.get("session_id"))
        
        # PATTERN: Pass current state context to supervisor agent
        shared_state_summary = "\n".join(state.get("shared_state", []))
        enhanced_query = f"""
        User Request: {state["query"]}
        Shared State: {shared_state_summary}
        Iteration: {state.get("iteration_count", 0)}/20
        """
        message_history = state.get("pydantic_message_history", [])
        
        full_response = ""
        full_reasoning = ""
        decision_data = None
        new_messages = []
        
        try:
            # Streaming structured output using .run_stream()
            async with supervisor_agent.run_stream(enhanced_query, deps=deps, message_history=message_history) as result:
                async for partial_decision in result.stream():
                    # Stream messages field if it's being populated for final responses
                    messages = partial_decision.get('messages')
                    reasoning = partial_decision.get('reasoning')
                    if messages:
                        writer(messages[len(full_response):])
                        full_response = messages
            
                    if reasoning:
                        writer(reasoning[len(full_reasoning):])
                        full_reasoning = reasoning
            
            # Extract structured decision from streaming result
            decision_data = await result.get_output()

            new_messages = result.new_messages_json()
            
        except Exception as stream_error:
            # FALLBACK: Non-streaming structured output
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating decision...]\n")
            
            result = await supervisor_agent.run(enhanced_query, deps=deps)
            decision_data = result.output
            
            # Use only the messages field if present for final response
            messages = decision_data.get('messages')
            reasoning = decision_data.get('reasoning')
            if messages:
                writer(messages)
                full_response = messages

            if reasoning:
                writer(reasoning)

            new_messages = result.new_messages_json()
        
        # PATTERN: Use structured decision for workflow control
        final_response = decision_data.get('messages') if decision_data.get('final_response') else ""
        
        return {
            "supervisor_reasoning": decision_data.get('reasoning'),
            "iteration_count": state.get("iteration_count", 0) + 1,
            "final_response": final_response,
            "workflow_complete": final_response,
            "delegate_to": decision_data.get('delegate_to'),
            "message_history": [new_messages]
        }
        
    except Exception as e:
        error_msg = f"Supervisor error: {str(e)}"
        writer(error_msg)
        return {
            "final_response": error_msg,
            "workflow_complete": True
        }


async def web_research_node(state: SupervisorAgentState, writer) -> dict:
    """Web research agent that appends summary to shared state"""
    try:
        writer("\n\n### 🔍 Web Research Agent Starting...\n")
        
        deps = create_web_research_deps(session_id=state.get("session_id"))
        agent_input = state["query"]
        message_history = state.get("pydantic_message_history", [])
        
        # No streaming for sub-agents - use .run() directly
        run = await web_research_agent.run(agent_input, deps=deps, message_history=message_history)
        full_response = str(run.output) if run.output else "No response generated"
        
        writer(f"✅ Web research completed\n\n")
        
        # Use full response in shared state (agent prompt ensures it's concise)
        summary = f"Web Research: {full_response}"
        current_shared = state.get("shared_state", [])
        
        return {
            "shared_state": current_shared + [summary]
        }
        
    except Exception as e:
        error_msg = f"Web research error: {str(e)}"
        writer(error_msg)
        summary = f"Web Research Error: {error_msg}"
        current_shared = state.get("shared_state", [])
        return {
            "shared_state": current_shared + [summary]
        }


async def task_management_node(state: SupervisorAgentState, writer) -> dict:
    """Task management agent that appends summary to shared state"""
    try:
        writer("\n\n### 📋 Task Management Agent Starting...\n")
        
        deps = create_task_management_deps(session_id=state.get("session_id"))
        
        # Construct prompt with context from shared state
        shared_context = "\n".join(state.get("shared_state", []))
        task_prompt = f"""
        Based on the user request and previous agent work, manage tasks and projects:
        
        User Request: {state["query"]}
        
        Previous Agent Work:
        {shared_context}
        
        Use this information to create appropriate projects and tasks in Asana.
        """
        
        message_history = state.get("pydantic_message_history", [])
        
        # No streaming for sub-agents - use .run() directly
        run = await task_management_agent.run(task_prompt, deps=deps, message_history=message_history)
        full_response = str(run.output) if run.output else "No response generated"
        
        writer(f"✅ Task management completed\n\n")
        
        # Use full response in shared state (agent prompt ensures it's concise)
        summary = f"Task Management: {full_response}"
        current_shared = state.get("shared_state", [])
        
        return {
            "shared_state": current_shared + [summary]
        }
        
    except Exception as e:
        error_msg = f"Task management error: {str(e)}"
        writer(error_msg)
        summary = f"Task Management Error: {error_msg}"
        current_shared = state.get("shared_state", [])
        return {
            "shared_state": current_shared + [summary]
        }


async def email_draft_node(state: SupervisorAgentState, writer) -> dict:
    """Email draft agent that appends summary to shared state"""
    try:
        writer("\n\n### ✉️ Email Draft Agent Starting...\n")
        
        deps = create_email_deps(session_id=state.get("session_id"))
        
        # Construct prompt with context from shared state
        shared_context = "\n".join(state.get("shared_state", []))
        email_prompt = f"""
        Create professional email drafts based on the user request and accumulated work:
        
        User Request: {state["query"]}
        
        Previous Agent Work:
        {shared_context}
        
        Use this information to create appropriate email drafts in Gmail.
        """
        
        message_history = state.get("pydantic_message_history", [])
        
        # No streaming for sub-agents - use .run() directly
        run = await email_draft_agent.run(email_prompt, deps=deps, message_history=message_history)
        full_response = str(run.output) if run.output else "No response generated"
        
        writer(f"✅ Email draft completed\n\n")
        
        # Use full response in shared state (agent prompt ensures it's concise)
        summary = f"Email Draft: {full_response}"
        current_shared = state.get("shared_state", [])
        
        return {
            "shared_state": current_shared + [summary]
        }
        
    except Exception as e:
        error_msg = f"Email draft error: {str(e)}"
        writer(error_msg)
        summary = f"Email Draft Error: {error_msg}"
        current_shared = state.get("shared_state", [])
        return {
            "shared_state": current_shared + [summary]
        }


def route_supervisor_decision(state: SupervisorAgentState) -> str:
    """Route based on supervisor decision"""
    # Check iteration limit
    if state.get("iteration_count", 0) >= 20:
        return END
    
    # Check if workflow is complete
    if state.get("workflow_complete", False):
        return END
    
    # Route based on delegation decision
    delegate_to = state.get("delegate_to")
    if delegate_to == "web_research":
        return "web_research_node"
    elif delegate_to == "task_management":
        return "task_management_node"
    elif delegate_to == "email_draft":
        return "email_draft_node"
    else:
        return END


def create_workflow():
    """Create and configure the supervisor agent workflow"""
    
    # Create state graph
    builder = StateGraph(SupervisorAgentState)
    
    # Add nodes
    builder.add_node("supervisor_node", supervisor_node)
    builder.add_node("web_research_node", web_research_node)
    builder.add_node("task_management_node", task_management_node)
    builder.add_node("email_draft_node", email_draft_node)
    
    # Set entry point
    builder.add_edge(START, "supervisor_node")
    
    # Add conditional routing from supervisor
    builder.add_conditional_edges(
        "supervisor_node",
        route_supervisor_decision,
        {
            "web_research_node": "web_research_node",
            "task_management_node": "task_management_node", 
            "email_draft_node": "email_draft_node",
            END: END
        }
    )
    
    # All sub-agents return to supervisor for next decision
    builder.add_edge("web_research_node", "supervisor_node")
    builder.add_edge("task_management_node", "supervisor_node")
    builder.add_edge("email_draft_node", "supervisor_node")
    
    # Compile the graph
    return builder.compile()


# Create the workflow instance
workflow = create_workflow()


def create_api_initial_state(
    query: str,
    session_id: str,
    request_id: str,
    pydantic_message_history: Optional[List[ModelMessage]] = None
) -> SupervisorAgentState:
    """Create initial state for supervisor workflow API mode"""
    return {
        "query": query,
        "session_id": session_id,
        "request_id": request_id,
        "iteration_count": 0,
        "supervisor_reasoning": "",
        "shared_state": [],
        "delegate_to": None,
        "final_response": "",
        "workflow_complete": False,
        "pydantic_message_history": pydantic_message_history or [],
        "message_history": [],
        "conversation_title": None,
        "is_new_conversation": False
    }


def extract_api_response_data(state: SupervisorAgentState) -> Dict[str, Any]:
    """Extract response data for API return"""
    return {
        "session_id": state.get("session_id"),
        "request_id": state.get("request_id"),
        "query": state["query"],
        "response": state.get("final_response", ""),
        "supervisor_reasoning": state.get("supervisor_reasoning", ""),
        "shared_state": state.get("shared_state", []),
        "iteration_count": state.get("iteration_count", 0),
        "workflow_complete": state.get("workflow_complete", False),
        "conversation_title": state.get("conversation_title"),
        "is_new_conversation": state.get("is_new_conversation", False)
    }