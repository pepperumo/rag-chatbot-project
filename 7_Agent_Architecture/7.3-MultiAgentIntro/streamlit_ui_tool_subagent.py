"""
Streamlit UI for Original Research Agent (no handoffs).

This UI provides a web interface for the original research agent with streaming capabilities.
"""

import streamlit as st
import asyncio
import sys
import os
import uuid
import logging
from typing import Optional

from pydantic_ai import Agent
from httpx import AsyncClient
from pydantic_ai.messages import ModelRequest, ModelResponse, PartDeltaEvent, PartStartEvent, TextPartDelta

from agents_delegation.research_agent import research_agent, ResearchAgentDependencies
from agents_delegation.providers import validate_llm_configuration, get_model_info
from config.settings import settings

# Setup logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

def display_message_part(part):
    """
    Display a single part of a message in the Streamlit UI.
    Customize how you display system prompts, user prompts,
    tool calls, tool returns, etc.
    """
    # User messages
    if part.part_kind == 'user-prompt' and part.content:
        with st.chat_message("user"):
            st.markdown(part.content)
    # AI messages
    elif part.part_kind == 'text' and part.content:
        with st.chat_message("assistant"):
            st.markdown(part.content)             

async def run_agent_with_streaming(user_input):
    """Run the original research agent with streaming capabilities."""
    # Initialize session_id if not present
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    try:
        # Create agent dependencies using configuration
        agent_deps = ResearchAgentDependencies(
            brave_api_key=settings.brave_api_key,
            gmail_credentials_path=settings.gmail_credentials_path,
            gmail_token_path=settings.gmail_token_path,
            session_id=st.session_state.session_id
        )
        
        # Use .iter() method for streaming
        async with research_agent.iter(user_input, deps=agent_deps, message_history=st.session_state.messages) as run:
            async for node in run:
                if Agent.is_model_request_node(node):
                    # A model request node => We can stream tokens from the model's request
                    async with node.stream(run.ctx) as request_stream:
                        async for event in request_stream:
                            if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                yield event.part.content
                            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                delta = event.delta.content_delta
                                yield delta
        
        # Add the new messages to the chat history (including tool calls and responses)
        if hasattr(run, 'result') and run.result and hasattr(run.result, 'new_messages'):
            try:
                new_messages = run.result.new_messages()
                if new_messages:
                    st.session_state.messages.extend(new_messages)
            except Exception as e:
                logger.error(f"Error getting new messages: {e}")
        else:
            logger.warning("No result or new_messages method available")
            
    except Exception as e:
        logger.error(f"Agent error: {e}")
        yield f"❌ Error: {e}"       

async def main():
    """Main Streamlit UI function."""
    st.title("🔬 Original Research Agent")
    
    # Show configuration info
    config_info = get_model_info()
    st.sidebar.header("Configuration")
    st.sidebar.info(f"**LLM:** {config_info['llm_provider']}/{config_info['llm_model']}")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    st.sidebar.info(f"**Session ID:** {st.session_state.session_id[:8]}...")
    
    # Validate configuration
    if not validate_llm_configuration():
        st.error("❌ LLM configuration invalid. Please check your .env file.")
        return
    
    # Display capabilities
    st.markdown("""
    **Capabilities:**
    - 🌐 Web research using Brave Search
    - 📧 Email draft creation via Gmail API
    - 📝 Direct text responses
    """)

    # Display all messages from the conversation so far
    for msg in st.session_state.messages:
        if isinstance(msg, ModelRequest) or isinstance(msg, ModelResponse):
            for part in msg.parts:
                display_message_part(part)

    # Chat input for the user
    user_input = st.chat_input("What do you want to research today?")

    if user_input:
        # Display user prompt in the UI
        with st.chat_message("user"):
            st.markdown(user_input)

        # Display the assistant's response
        with st.chat_message("assistant"):
            # Create a placeholder for the streaming text
            message_placeholder = st.empty()
            full_response = ""
            
            # Properly consume the async generator with async for
            generator = run_agent_with_streaming(user_input)
            async for message in generator:
                full_response += message
                message_placeholder.markdown(full_response + "▌")
            
            # Final response without the cursor
            message_placeholder.markdown(full_response)


if __name__ == "__main__":
    asyncio.run(main())