from pydantic_ai import Agent
from httpx import AsyncClient
import streamlit as st
import requests
import asyncio
import os

from agent import agent, AgentDeps
from clients import get_agent_clients, get_mem0_client

# Import all the message part classes from Pydantic AI
from pydantic_ai.messages import (
    ModelMessage, ModelRequest, ModelResponse, TextPart, 
    UserPromptPart, PartDeltaEvent, PartStartEvent, TextPartDelta
)

@st.cache_resource
def get_agent_deps():
    return get_agent_clients()

@st.cache_resource
def initialize_mem0():
    return get_mem0_client()

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
    # Retrieve relevant memories with Mem0
    memory = initialize_mem0()
    relevant_memories = memory.search(query=user_input, user_id="streamlit_user", limit=3)
    memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories["results"]) 

    # Set up the dependencies for the agent
    embedding_client, supabase = get_agent_deps()

    async with AsyncClient() as http_client:
        agent_deps = AgentDeps(
            embedding_client=embedding_client, 
            supabase=supabase, 
            http_client=http_client,
            brave_api_key=os.getenv("BRAVE_API_KEY", ""),
            searxng_base_url=os.getenv("SEARXNG_BASE_URL", ""),
            memories=memories_str
        )   

        async with agent.run_mcp_servers():
            async with agent.iter(user_input, deps=agent_deps, message_history=st.session_state.messages) as run:
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
    st.session_state.messages.extend(run.result.new_messages())

    # Update memories based on the last user message and agent response
    memory_messages = [
        {"role": "user", "content": user_input},
        # Include the AI response as well if you wish but that generally leads to a lot of useless memories
        # {"role": "assistant", "content": run.result.data}
    ]
    memory.add(memory_messages, user_id="streamlit_user")         


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~ Main Function with UI Creation ~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

async def main():
    st.title("Pydantic AI Agent")
    
    # Initialize chat history in session state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display all messages from the conversation so far
    # Each message is either a ModelRequest or ModelResponse.
    # We iterate over their parts to decide how to display them.
    for msg in st.session_state.messages:
        if isinstance(msg, ModelRequest) or isinstance(msg, ModelResponse):
            for part in msg.parts:
                display_message_part(part)

    # Chat input for the user
    user_input = st.chat_input("What do you want to do today?")

    if user_input:
        # Display user prompt in the UI
        with st.chat_message("user"):
            st.markdown(user_input)

        # Display the assistant's partial response while streaming
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
