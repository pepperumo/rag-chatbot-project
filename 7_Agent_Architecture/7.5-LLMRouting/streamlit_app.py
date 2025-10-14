"""
Streamlit UI for the RAG Guardrail Agent.

This provides a simple interface that directly integrates with the LangGraph 
workflow without any API dependencies or authentication.
"""
import streamlit as st
import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LangGraph workflow and dependencies
from graph.workflow import workflow, create_api_initial_state

# Page configuration
st.set_page_config(
    page_title="RAG Guardrail Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better formatting
st.markdown("""
<style>
    .stMarkdown h3 {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .agent-response {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .guardrail-validation {
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .validation-passed {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .validation-failed {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .validation-error {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-container {
        max-width: 800px;
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
        Tuple of (full_response, citations, validation_passed)
    """
    # Create initial state for LangGraph
    initial_state = create_api_initial_state(
        query=query,
        session_id=session_id,
        request_id=str(uuid.uuid4()),
        pydantic_message_history=[]
    )
    
    # Create workflow configuration
    thread_id = f"rag-guardrail-{session_id}"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Create placeholders for streaming
    response_placeholder = st.empty()
    status_placeholder = st.empty()
    
    full_response = ""
    citations = []
    validation_passed = False
    
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
            citations = final_state.get("google_drive_urls", [])
            validation_passed = final_state.get("validation_result") == "valid"
        
        return full_response, citations, validation_passed
        
    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        return f"Error: {str(e)}", [], False


def display_citations(citations: List[str]):
    """Display citations in a formatted way."""
    if citations:
        st.markdown("### 📎 Citations")
        for i, citation in enumerate(citations, 1):
            st.markdown(f"{i}. [{citation}]({citation})")


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🛡️ RAG Guardrail Agent")
    st.markdown("An intelligent agent with citation validation and guardrails")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Display citations if available
                if message["role"] == "assistant" and "citations" in message:
                    display_citations(message["citations"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about research documents..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Display assistant response
            with st.chat_message("assistant"):
                try:
                    # Run the async streaming function
                    response, citations, validation_passed = asyncio.run(
                        stream_agent_response(prompt, st.session_state.session_id)
                    )
                    
                    # Add assistant message to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "citations": citations,
                        "validation_passed": validation_passed
                    })
                    
                    # Display citations
                    if citations:
                        display_citations(citations)
                    
                except Exception as e:
                    error_msg = f"Error processing your request: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "citations": [],
                        "validation_passed": False
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
        - Ask questions about research documents
        - The agent will search for relevant information
        - Citations will be validated automatically
        - Look for the ✅ or ❌ validation indicators
        """)
        
        st.divider()
        st.caption("Powered by LangGraph and Pydantic AI")


if __name__ == "__main__":
    main()