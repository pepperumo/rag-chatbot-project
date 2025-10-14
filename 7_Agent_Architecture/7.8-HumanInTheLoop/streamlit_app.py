"""
Streamlit UI for the Human-in-the-Loop Email Agent.

This provides an intuitive interface for interacting with the email agent
that can read inbox, draft emails, and requires human approval for sending.
"""
import streamlit as st
import asyncio
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LangGraph workflow and dependencies
from graph.workflow import create_email_workflow, create_email_api_initial_state

# Page configuration
st.set_page_config(
    page_title="Email Agent Assistant",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


class StreamingWriter:
    """Writer class for streaming responses to Streamlit"""
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.content = ""
    
    def __call__(self, text):
        self.content += text
        self.placeholder.markdown(self.content)


async def stream_email_response(query: str, session_id: str):
    """
    Stream response from the human-in-the-loop email workflow.
    
    Args:
        query: User's query
        session_id: Session identifier
        
    Returns:
        Tuple of (full_response, workflow_metadata)
    """
    # Create initial state for email workflow
    initial_state = create_email_api_initial_state(
        query=query,
        session_id=session_id,
        request_id=str(uuid.uuid4()),
        pydantic_message_history=[]
    )
    
    # Create workflow
    workflow = create_email_workflow()
    
    # Create workflow configuration
    thread_id = f"email-hitl-{session_id}"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Create placeholders for response and status
    status_placeholder = st.empty()
    response_placeholder = st.empty()
    
    # Create streaming writer
    writer = StreamingWriter(response_placeholder)
    
    full_response = ""
    workflow_metadata = {}
    
    try:
        # Import workflow nodes
        from graph.workflow import email_agent_node, human_approval_node, email_send_node
        
        # Execute the workflow manually with proper streaming
        current_state = initial_state.copy()
        
        # Start with email agent node
        status_placeholder.info("⚡ Email agent working...")
        result = await email_agent_node(current_state, writer)
        current_state.update(result)
        
        # Check if we need approval
        if current_state.get("email_recipients"):
            status_placeholder.info("🔔 Approval required...")
            # Execute approval node
            approval_result = await human_approval_node(current_state, writer)
            current_state.update(approval_result)
            
            # If approved, send email
            if current_state.get("approval_granted"):
                status_placeholder.info("📤 Sending email...")
                send_result = await email_send_node(current_state, writer)
                current_state.update(send_result)
        
        status_placeholder.empty()  # Clear status
        
        # Get final response from writer
        full_response = writer.content
        
        # Simple metadata
        workflow_metadata = {
            "response": full_response
        }
        
        return full_response, workflow_metadata
        
    except Exception as e:
        error_msg = f"Error in email workflow: {str(e)}"
        st.error(error_msg)
        return error_msg, {}


def main():
    """Main Streamlit application."""
    
    # Header
    st.title("✉️ Email Agent Assistant")
    st.markdown("AI-powered email management with human approval for sending")
    
    # Chat container
    with st.container():
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me to check emails, draft responses, or manage your inbox..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Display assistant response with streaming
            with st.chat_message("assistant"):
                try:
                    # Run the async streaming function
                    response, metadata = asyncio.run(
                        stream_email_response(prompt, st.session_state.session_id)
                    )
                    
                    # Add assistant message to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "metadata": metadata
                    })
                    
                except Exception as e:
                    error_msg = f"Error in email workflow: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "metadata": {}
                    })
    
    # Sidebar with session info and examples
    with st.sidebar:
        st.header("✉️ Email Assistant")
        st.text(f"Session: {st.session_state.session_id[:8]}...")
        
        if st.button("🔄 New Session"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            # Reset workflow with new checkpointer
            checkpointer = MemorySaver()
            st.session_state.workflow = create_email_workflow(checkpointer=checkpointer)
            st.rerun()
        
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Example queries
        st.markdown("""
        ### 💡 Example Queries
        
        **📥 Reading Emails:**
        - "Check my inbox for new emails"
        - "Show me unread emails"
        - "Any emails from John?"
        
        **✍️ Drafting Emails:**
        - "Draft a reply to the latest email"
        - "Create an email to team about meeting"
        - "Write a follow-up email"
        
        **📤 Sending Emails:**
        - "Send an email to alice@example.com"
        - "Email the team about project update"
        - "Reply to Bob's email"
        """)
        
        st.divider()
        
        # Architecture info
        st.markdown("""
        ### 🏗️ Architecture
        
        **Human-in-the-Loop Pattern:**
        - Real-time streaming responses
        - LangGraph interrupt for approval
        - Memory checkpointer for state
        - Dynamic workflow resumption
        
        **Email Capabilities:**
        - 📥 Autonomous email reading
        - ✍️ Intelligent draft creation  
        - 🔒 Required approval for sending
        - 💾 Conversation memory persistence
        """)
        
        st.divider()
        st.caption("Powered by Pydantic AI & LangGraph")


if __name__ == "__main__":
    main()