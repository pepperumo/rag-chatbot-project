"""
Streamlit UI for the Sequential Agent Workflow.

This provides a simple interface that directly integrates with the LangGraph 
workflow without any API dependencies or authentication.
"""
import streamlit as st
import asyncio
import uuid
from typing import Dict, Any
from dotenv import load_dotenv
from graph.workflow import workflow, create_api_initial_state

# Load environment variables
load_dotenv()

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
                except (UnicodeDecodeError, ValueError):
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
                "synthesis_complete": final_state.get("synthesis_complete", False),
                "research_sources": final_state.get("research_sources", [])
            }
        
        return full_response, workflow_metadata
        
    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        return f"Error: {str(e)}", {}


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🔄 Parallel Research & Synthesis Agent")
    st.markdown("Multi-perspective analysis for businesses, startups, and market intelligence")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Research a company, explore a business idea, or ask a question..."):
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
        
        **Research Requests:**
        - "Research John Doe at TechCorp"
        - "I want to start an AI pet startup for dogs"
        - "Analyze the market for sustainable fashion"
        - "What's the competitive landscape for meal delivery?"
        - "Research opportunities in the EdTech space"
        
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