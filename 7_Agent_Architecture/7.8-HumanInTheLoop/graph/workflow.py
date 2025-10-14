"""
Human-in-the-Loop Email Agent Workflow with LangGraph.

This module implements a LangGraph workflow with interrupt-based human approval
for email sending operations. The agent can autonomously read and draft emails
but requires explicit human approval before sending.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

from graph.state import EmailAgentState
from agents.email_agent import email_agent, EmailAgentDependencies
from agents.deps import create_email_deps
from tools.gmail_tools import send_email_tool
from pydantic_ai.messages import ModelMessage

load_dotenv()


def create_email_agent_deps(session_id: Optional[str] = None) -> EmailAgentDependencies:
    """Create email agent dependencies"""
    return create_email_deps(session_id=session_id)


async def email_agent_node(state: EmailAgentState, writer) -> dict:
    """
    Main email agent processing with send detection.
    
    Args:
        state: Current workflow state
        writer: Streaming writer function
        
    Returns:
        Updated state dict
    """
    try:
        deps = create_email_agent_deps(session_id=state.get("session_id"))
        query = state["query"]
        message_history = state.get("pydantic_message_history", [])
        
        # Check if this is a revision request
        if state.get("revision_requested"):
            # Get previous email details
            feedback = state.get("approval_feedback", "")
            prev_recipients = state.get("previous_email_recipients", [])
            prev_subject = state.get("previous_email_subject", "")
            prev_body = state.get("previous_email_body", "")
            
            # Provide revision context that instructs agent to revise and send
            query = f"""
REVISION REQUEST - INCORPORATE FEEDBACK AND PREPARE REVISED EMAIL:

Original user request: "{query}"
User's revision feedback: "{feedback}"

Previous email that was declined:
- To: {', '.join(prev_recipients) if prev_recipients else 'Unknown'}
- Subject: {prev_subject}
- Body: {prev_body}

INSTRUCTIONS:
1. Incorporate the user's feedback to revise the email
2. Create an improved version based on their specific suggestions
3. IMPORTANT: After revising, request to send the improved email by setting request_send=true
4. Fill in recipients, subject, and body fields with the revised content
5. Say "I've revised the email based on your feedback. Here's the improved version:"
"""
        
        # Run agent and stream response
        full_response = ""
        decision_data = None
        new_messages = []
        
        async with email_agent.run_stream(query, deps=deps, message_history=message_history) as result:
            async for partial in result.stream():
                # Stream conversational message
                message_content = partial.get('message')
                if message_content:
                    new_content = message_content[len(full_response):]
                    if new_content:
                        writer(new_content)
                        full_response = message_content
            
            decision_data = await result.get_output()
            new_messages = result.new_messages_json()
        
        # Check if agent wants to send email
        if decision_data.get('request_send') and decision_data.get('recipients'):
            # Store email data in state for approval
            return {
                "email_recipients": decision_data['recipients'],
                "email_subject": decision_data['subject'],
                "email_body": decision_data['body'],
                "message_history": [new_messages] if new_messages else [],
                "revision_requested": None,
                "approval_feedback": None,
                "previous_email_recipients": None,
                "previous_email_subject": None,
                "previous_email_body": None
            }
        
        # Normal conversation response - update message history
        return {
            "message_history": [new_messages] if new_messages else [],
            "revision_requested": None,
            "approval_feedback": None,
            "previous_email_recipients": None,
            "previous_email_subject": None,
            "previous_email_body": None
        }
        
    except Exception as e:
        error_msg = f"Email agent error: {str(e)}"
        writer(error_msg)
        return {
            "email_recipients": None,
            "email_subject": None,
            "email_body": None,
            "message_history": []
        }


async def human_approval_node(state: EmailAgentState, writer) -> dict:
    """
    Human approval node with interrupt.
    ONLY shows approval UI on first request - not when resuming from interrupt.
    
    Args:
        state: Current workflow state
        writer: Streaming writer function
        
    Returns:
        Updated state dict with approval decision
    """
    
    # Validate email state before proceeding
    email_recipients = state.get("email_recipients", [])
    email_subject = state.get("email_subject", "No subject")
    email_body = state.get("email_body", "No body content")
    
    if not email_recipients:
        writer("❌ **Error: No email recipients found.**\n")
        return {
            "approval_granted": False,
            "approval_feedback": "Error: No recipients",
            "email_recipients": None,
            "email_subject": None,
            "email_body": None
        }
    
    # Present email for approval - ONLY on first visit, not when resuming
    approval_request = {
        "type": "email_approval",
        "recipients": email_recipients,
        "subject": email_subject,
        "body": email_body
    }
    
    # Only show UI on first visit - detect if we're resuming from interrupt
    # If the node is being executed again, it means we're resuming and should skip UI
    already_showed_ui = hasattr(human_approval_node, '_ui_shown_for_session')
    session_key = f"{state.get('session_id')}_{email_recipients}_{email_subject}"
    
    if not already_showed_ui or session_key not in getattr(human_approval_node, '_ui_shown_for_session', set()):
        # First time showing UI for this approval request
        if not hasattr(human_approval_node, '_ui_shown_for_session'):
            human_approval_node._ui_shown_for_session = set()
        human_approval_node._ui_shown_for_session.add(session_key)
        
        try:
            writer("\n\n🔔 **Email Approval Required**\n\n")
            writer(f"**To:** {', '.join(email_recipients)}\n")
            writer(f"**Subject:** {email_subject}\n\n")
            writer("**Message:**\n")
            writer(f"{email_body}\n\n")
            writer("Please respond with 'yes' to approve or 'no' to decline.\n")
            writer("You can add feedback after: 'yes-looks great' or 'no-please revise the tone'\n\n")
        except Exception as presentation_error:
            writer(f"❌ **Error presenting approval UI: {str(presentation_error)}**\n")
            return {
                "approval_granted": False,
                "approval_feedback": "Error in approval UI",
                "email_recipients": None,
                "email_subject": None,
                "email_body": None
            }
    
    # Interrupt should NOT be in try/catch - it's normal control flow
    human_response = interrupt(approval_request)
    
    # When this executes, it means we're resuming from interrupt
    # The UI was already shown, so don't show it again - just process the response
    approval_granted = human_response.get("approved", False)
    
    # Clean up the session tracking since approval process is complete
    if hasattr(human_approval_node, '_ui_shown_for_session'):
        human_approval_node._ui_shown_for_session.discard(session_key)
    
    if approval_granted:
        writer("\n✅ **Email approved! Sending now...**\n")
        return {
            "approval_granted": True,
            "approval_feedback": human_response.get("feedback", "")
        }
    else:
        # Route back to agent for revision
        feedback = human_response.get("feedback", "")
        writer(f"\n❌ **Email sending cancelled.** {feedback}\n")
        return {
            "approval_granted": False,
            "approval_feedback": feedback,
            "revision_requested": True,
            "previous_email_recipients": email_recipients,
            "previous_email_subject": email_subject, 
            "previous_email_body": email_body,
            "email_recipients": None,
            "email_subject": None,
            "email_body": None
        }


async def email_send_node(state: EmailAgentState, writer) -> dict:
    """
    Execute email sending after approval.
    
    Args:
        state: Current workflow state
        writer: Streaming writer function
        
    Returns:
        Updated state dict
    """
    try:
        writer("\n\n📤 **Sending Email...**\n")
        
        # Get email dependencies
        deps = create_email_agent_deps(session_id=state.get("session_id"))
        
        # Send the email using the tool
        result = await send_email_tool(
            credentials_path=deps.gmail_credentials_path,
            token_path=deps.gmail_token_path,
            to=state.get("email_recipients", []),
            subject=state.get("email_subject", ""),
            body=state.get("email_body", "")
        )
        
        if result.get("success"):
            success_msg = "✅ **Email sent successfully!**\n"
            success_msg += f"Message ID: {result.get('message_id')}\n"
            success_msg += f"Sent to: {', '.join(result.get('recipients', []))}\n"
            writer(success_msg)
        else:
            error_msg = f"❌ **Failed to send email:** {result.get('error', 'Unknown error')}\n"
            writer(error_msg)
        
        return {
            "email_recipients": None,
            "email_subject": None,
            "email_body": None,
            "approval_granted": None,
            "approval_feedback": None
        }
        
    except Exception as e:
        error_msg = f"❌ **Email sending error:** {str(e)}\n"
        writer(error_msg)
        return {
            "email_recipients": None,
            "email_subject": None,
            "email_body": None,
            "approval_granted": None,
            "approval_feedback": None
        }


def route_email_agent_decision(state: EmailAgentState) -> str:
    """Route based on email agent's decision"""
    # Check if agent requested email send
    if state.get("email_recipients") and state.get("email_subject"):
        return "human_approval_node"
    return END  # Normal conversation response



def route_after_approval(state: EmailAgentState) -> str:
    """Route based on approval decision"""
    if state.get("approval_granted"):
        return "email_send_node"
    return "email_agent_node"  # Go back to agent for revision when declined


def create_email_workflow(checkpointer=None):
    """Create and configure the email agent workflow with optional checkpointer"""
    
    # Create state graph
    builder = StateGraph(EmailAgentState)
    
    # Add nodes
    builder.add_node("email_agent_node", email_agent_node)
    builder.add_node("human_approval_node", human_approval_node)
    builder.add_node("email_send_node", email_send_node)
    
    # Set entry point
    builder.add_edge(START, "email_agent_node")
    
    # Add conditional routing from email agent
    builder.add_conditional_edges(
        "email_agent_node",
        route_email_agent_decision,
        {
            "human_approval_node": "human_approval_node",
            END: END
        }
    )
    
    # Add conditional routing after approval
    builder.add_conditional_edges(
        "human_approval_node",
        route_after_approval,
        {
            "email_send_node": "email_send_node",
            "email_agent_node": "email_agent_node"  # Go back to agent for revision
        }
    )
    
    # Email send node always ends the workflow
    builder.add_edge("email_send_node", END)
    
    # Compile the graph with optional checkpointer
    return builder.compile(checkpointer=checkpointer)


workflow = create_email_workflow()


def create_email_api_initial_state(
    query: str,
    session_id: str,
    request_id: str,
    pydantic_message_history: Optional[List[ModelMessage]] = None
) -> EmailAgentState:
    """Create initial state for email workflow API mode"""
    return {
        "query": query,
        "session_id": session_id,
        "request_id": request_id,
        "pydantic_message_history": pydantic_message_history or [],
        "email_recipients": None,
        "email_subject": None,
        "email_body": None,
        "approval_granted": None,
        "approval_feedback": None,
        "message_history": [],
        "conversation_title": None,
        "is_new_conversation": False
    }


def extract_email_api_response_data(state: EmailAgentState) -> Dict[str, Any]:
    """Extract response data for API return"""
    return {
        "session_id": state.get("session_id"),
        "request_id": state.get("request_id"),
        "query": state["query"],
        "email_recipients": state.get("email_recipients"),
        "email_subject": state.get("email_subject"),
        "email_body": state.get("email_body"),
        "approval_granted": state.get("approval_granted"),
        "approval_feedback": state.get("approval_feedback"),
        "conversation_title": state.get("conversation_title"),
        "is_new_conversation": state.get("is_new_conversation", False)
    }