"""
Streamlit UI for Multi-Agent Research & Email System with Handoffs.

This UI provides a web interface for the research agent with output function handoffs.
Streams both regular responses and email handoffs seamlessly.
"""

import streamlit as st
import asyncio
import uuid
import logging
from typing import Optional

from pydantic_ai.messages import ModelRequest, ModelResponse, PartDeltaEvent, PartStartEvent, TextPartDelta

from agents_handoff.cli_interface import research_agent, ResearchAgentDependencies
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

async def run_agent_with_streaming(user_input, placeholder):
    """Run the agent with streaming output - works for both regular responses and handoffs."""
    # Initialize session_id
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    try:
        # Create dependencies
        agent_deps = ResearchAgentDependencies(
            brave_api_key=settings.brave_api_key,
            gmail_credentials_path=settings.gmail_credentials_path,
            gmail_token_path=settings.gmail_token_path,
            session_id=st.session_state.session_id
        )
        
        logger.info(f"Starting streaming for: {user_input}")
        
        # Stream the agent response (tools work much better for streaming!)
        accumulated_text = ""
        async with research_agent.iter(
            user_input, 
            deps=agent_deps, 
            message_history=st.session_state.messages
        ) as run:
            async for event in run:
                if isinstance(event, PartStartEvent):
                    logger.debug(f"Part started: {event.part_kind}")
                elif isinstance(event, PartDeltaEvent):
                    if isinstance(event.delta, TextPartDelta):
                        accumulated_text += event.delta.content
                        placeholder.markdown(accumulated_text)
        
        # Get final result and update message history
        result = run.result
        if hasattr(result, 'new_messages') and callable(result.new_messages):
            new_messages = result.new_messages()
            if new_messages:
                st.session_state.messages.extend(new_messages)
        
        logger.info("Streaming completed")
        
        # Return accumulated text if we got any, otherwise the final result
        if accumulated_text:
            return accumulated_text
        elif hasattr(result, 'output'):
            final_response = str(result.output)
            placeholder.markdown(final_response)
            return final_response
        else:
            return "No response"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_msg = f"❌ Error: {e}"
        placeholder.markdown(error_msg)
        return error_msg       


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~ Main Function with UI Creation ~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

async def main():
    """Main Streamlit UI function."""
    st.title("🔬 Multi-Agent Research & Email System (with Handoffs)")
    
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
    - 📧 **Automatic email handoffs** - Agent decides when to create emails
    - 🤖 Multi-agent collaboration with structured outputs
    - 🔄 Seamless handoffs between research and email agents
    """)

    # Display all messages from the conversation so far
    for msg in st.session_state.messages:
        if isinstance(msg, ModelRequest) or isinstance(msg, ModelResponse):
            for part in msg.parts:
                display_message_part(part)

    # Chat input for the user
    user_input = st.chat_input("Ask me to research something or create an email!")

    if user_input:
        # Display user prompt in the UI
        with st.chat_message("user"):
            st.markdown(user_input)

        # Display the assistant's response with streaming
        with st.chat_message("assistant"):
            # Create a placeholder for streaming content
            placeholder = st.empty()
            
            # Stream the response (handles both regular responses and handoffs)
            response = await run_agent_with_streaming(user_input, placeholder)


if __name__ == "__main__":
    asyncio.run(main())
