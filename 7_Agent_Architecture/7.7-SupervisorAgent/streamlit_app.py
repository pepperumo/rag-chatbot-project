"""
Streamlit UI for the Supervisor Pattern Multi-Agent System.

This provides an intuitive interface for interacting with the supervisor agent 
that dynamically delegates to specialized sub-agents with real-time streaming.
"""
import streamlit as st
import asyncio
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LangGraph workflow and dependencies
from graph.workflow import workflow, create_api_initial_state, extract_api_response_data

# Page configuration
st.set_page_config(
    page_title="Supervisor Agent System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Streamlit configuration - no custom CSS needed for markdown

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


async def stream_supervisor_response(query: str, session_id: str):
    """
    Stream response from the supervisor pattern workflow.
    
    Args:
        query: User's query
        session_id: Session identifier
        
    Returns:
        Tuple of (full_response, workflow_metadata)
    """
    # Create initial state for supervisor workflow
    initial_state = create_api_initial_state(
        query=query,
        session_id=session_id,
        request_id=str(uuid.uuid4()),
        pydantic_message_history=[]
    )
    
    # Create workflow configuration
    thread_id = f"supervisor-agent-{session_id}"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Create placeholders for response and status
    status_placeholder = st.empty()
    response_placeholder = st.empty()
    
    full_response = ""
    workflow_metadata = {}
    shared_state_items = []
    
    try:
        # Stream the supervisor workflow
        async for chunk in workflow.astream(initial_state, config, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                
                # Handle supervisor node outputs
                if node_name == "supervisor_node":
                    # Show delegation status
                    if node_output.get("delegate_to"):
                        agent_map = {
                            "web_research": "🔍 Web Research Agent",
                            "task_management": "📋 Task Management Agent", 
                            "email_draft": "✉️ Email Draft Agent"
                        }
                        agent_name = agent_map.get(node_output["delegate_to"], node_output["delegate_to"])
                        status_placeholder.info(f"🚀 Delegating to: **{agent_name}**")
                    
                    # Show final response
                    if node_output.get("final_response"):
                        full_response = node_output["final_response"]
                        status_placeholder.empty()  # Clear status
                        response_placeholder.markdown(full_response)
                
                # Show agent working status
                elif node_name in ["web_research_node", "task_management_node", "email_draft_node"]:
                    agent_map = {
                        "web_research_node": "🔍 Web Research Agent",
                        "task_management_node": "📋 Task Management Agent", 
                        "email_draft_node": "✉️ Email Draft Agent"
                    }
                    agent_name = agent_map.get(node_name, node_name)
                    status_placeholder.info(f"⚡ {agent_name} working...")
                    
                    # Track shared state for metadata
                    if node_output.get("shared_state"):
                        shared_state_items = node_output["shared_state"]
                
                # Real-time UI updates
                await asyncio.sleep(0.1)  # Small delay for smooth updates
        
        # Simple metadata
        workflow_metadata = {
            "shared_state": shared_state_items,
            "response": full_response
        }
        
        return full_response, workflow_metadata
        
    except Exception as e:
        st.error(f"Error in supervisor workflow: {str(e)}")
        return f"Error: {str(e)}", {}



def main():
    """Main Streamlit application."""
    
    # Header
    st.title("🎯 Supervisor Agent System")
    st.markdown("Intelligent multi-agent coordination with real-time streaming")
    
    # Chat container
    with st.container():
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me anything - I'll intelligently delegate or respond directly..."):
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
                        stream_supervisor_response(prompt, st.session_state.session_id)
                    )
                    
                    # Add assistant message to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "metadata": metadata
                    })
                    
                except Exception as e:
                    error_msg = f"Error in supervisor workflow: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "metadata": {}
                    })
    
    # Sidebar with session info and examples
    with st.sidebar:
        st.header("🎯 Supervisor Agent")
        st.text(f"Session: {st.session_state.session_id[:8]}...")
        
        if st.button("🔄 New Session"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
        
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Example queries
        st.markdown("""
        ### 💡 Example Queries
        
        **🔍 Web Research:**
        - "Research the latest AI safety developments"
        - "Find Tesla's latest quarterly earnings"
        - "What are current renewable energy trends?"
        
        **📋 Task Management:**
        - "Create a project plan for Q1 launch"
        - "Set up tasks for marketing campaign"
        - "Organize development timeline"
        
        **✉️ Email Drafting:**
        - "Draft email to investors about Q4 results"
        - "Write outreach email for partnerships"
        - "Compose client update email"
        
        **🎯 Direct Response:**
        - "What is machine learning?"
        - "Explain neural networks"
        - "How does AI work?"
        """)
        
        st.divider()
        
        # Architecture info
        st.markdown("""
        ### 🏗️ Architecture
        
        **Supervisor Pattern:**
        - Intelligent request analysis
        - Dynamic agent delegation
        - Real-time streaming responses
        - Shared state coordination
        
        **Sub-Agents:**
        - 🔍 Web Research (Brave API)
        - 📋 Task Management (Asana API)
        - ✉️ Email Draft (Gmail API)
        """)
        
        st.divider()
        st.caption("Powered by Pydantic AI, LangGraph & Supervisor Pattern")


if __name__ == "__main__":
    main()