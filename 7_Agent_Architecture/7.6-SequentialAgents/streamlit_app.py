"""
Streamlit UI for the Sequential Agent Workflow.

This provides a simple interface that directly integrates with the LangGraph 
workflow without any API dependencies or authentication.
"""
import streamlit as st
import asyncio
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LangGraph workflow and dependencies
from graph.workflow import workflow, create_api_initial_state

# Page configuration
st.set_page_config(
    page_title="Sequential Research & Outreach Agent",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better formatting
st.markdown("""
<style>
    .stMarkdown h3 {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        color: #1f77b4;
    }
    .agent-response {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .agent-separator {
        border-left: 3px solid #1f77b4;
        padding-left: 1rem;
        margin: 1rem 0;
    }
    .workflow-status {
        background-color: #e3f2fd;
        border: 1px solid #90caf9;
        color: #1565c0;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


async def stream_agent_response(query: str, session_id: str):
    """
    Stream response directly from the LangGraph workflow.
    
    Args:
        query: User's query
        session_id: Session identifier
        
    Returns:
        Tuple of (full_response, workflow_metadata)
    """
    # Create initial state for LangGraph
    initial_state = create_api_initial_state(
        query=query,
        session_id=session_id,
        request_id=str(uuid.uuid4()),
        pydantic_message_history=[]
    )
    
    # Create workflow configuration
    thread_id = f"sequential-agents-{session_id}"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Create placeholders for streaming
    response_placeholder = st.empty()
    
    full_response = ""
    workflow_metadata = {}
    
    try:
        # Stream the workflow response
        async for msg in workflow.astream(
            initial_state, config, stream_mode="custom"
        ):
            if isinstance(msg, str):
                # Direct string content from writer
                full_response += msg
                response_placeholder.markdown(full_response)
            elif isinstance(msg, bytes):
                # Bytes content, decode and add
                try:
                    decoded = msg.decode('utf-8')
                    full_response += decoded
                    response_placeholder.markdown(full_response)
                except:
                    # If can't decode, skip
                    pass
        
        # Get final state to extract metadata
        final_state = None
        async for state in workflow.astream(initial_state, config, stream_mode="values"):
            final_state = state
            break  # We only need the final state
        
        if final_state:
            workflow_metadata = {
                "is_research_request": final_state.get("is_research_request", False),
                "agent_type": final_state.get("agent_type", "unknown"),
                "email_draft_created": final_state.get("email_draft_created", False),
                "research_sources": final_state.get("research_sources", [])
            }
        
        return full_response, workflow_metadata
        
    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        return f"Error: {str(e)}", {}


def display_workflow_metadata(metadata: Dict[str, Any]):
    """Display workflow metadata in a formatted way."""
    if metadata:
        with st.expander("🔍 Workflow Details", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Request Type", 
                         "Research & Outreach" if metadata.get("is_research_request") else "Conversation")
                st.metric("Final Agent", metadata.get("agent_type", "unknown").title())
            with col2:
                st.metric("Email Draft Created", 
                         "✅ Yes" if metadata.get("email_draft_created") else "❌ No")
                sources = metadata.get("research_sources", [])
                st.metric("Research Sources", len(sources))
            
            if sources:
                st.markdown("**Research Sources:**")
                for source in sources:
                    st.markdown(f"- [{source.get('title', 'Source')}]({source.get('url', '#')})")


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🔄 Sequential Research & Outreach Agent")
    st.markdown("Automated research and professional outreach workflow")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Display workflow metadata if available
                if message["role"] == "assistant" and "metadata" in message:
                    display_workflow_metadata(message["metadata"])
        
        # Chat input
        if prompt := st.chat_input("Research someone or ask a question..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Display assistant response
            with st.chat_message("assistant"):
                try:
                    # Run the async streaming function
                    response, metadata = asyncio.run(
                        stream_agent_response(prompt, st.session_state.session_id)
                    )
                    
                    # Add assistant message to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "metadata": metadata
                    })
                    
                    # Display workflow metadata
                    display_workflow_metadata(metadata)
                    
                except Exception as e:
                    error_msg = f"Error processing your request: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "metadata": {}
                    })
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar with session info and controls
    with st.sidebar:
        st.header("Session Info")
        st.text(f"Session ID: {st.session_state.session_id[:8]}...")
        
        if st.button("🔄 New Conversation"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
        
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Instructions
        st.markdown("""
        ### 💡 How to Use
        
        **Research & Outreach Requests:**
        - "Research John Doe at TechCorp and draft an outreach email"
        - "Find information about Sarah Smith at Microsoft"
        - "Look up ABC Company and create a business email"
        
        **Normal Conversation:**
        - "How are you today?"
        - "Explain machine learning to me"
        - "What's the weather like?"
        
        The system will automatically detect your intent and route to the appropriate workflow.
        """)
        
        st.divider()
        st.caption("Powered by LangGraph, Pydantic AI, and Brave Search")


if __name__ == "__main__":
    main()