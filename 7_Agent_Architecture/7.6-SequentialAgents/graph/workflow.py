"""
Sequential Agent Workflow for Research and Outreach System.

This module implements a LangGraph workflow that routes requests through a guardrail agent,
then executes a sequential workflow of research → enrichment → email draft creation.
"""

from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

from graph.state import SequentialAgentState
from agents.guardrail_agent import guardrail_agent
from agents.research_agent import research_agent
from agents.enrichment_agent import enrichment_agent
from agents.email_draft_agent import email_draft_agent
from agents.fallback_agent import fallback_agent
from agents.deps import (
    create_guardrail_deps,
    create_research_deps,
    create_email_deps
)
from pydantic_ai.messages import ModelMessage
from pydantic_ai import Agent
from pydantic_ai.messages import PartDeltaEvent, PartStartEvent, TextPartDelta

load_dotenv()


async def guardrail_node(state: SequentialAgentState, writer) -> dict:
    """Guardrail node that determines if request is for research/outreach or conversation"""
    try:
        deps = create_guardrail_deps(session_id=state.get("session_id"))
        
        # Get structured routing decision with message history
        message_history = state.get("pydantic_message_history", [])
        result = await guardrail_agent.run(state["query"], deps=deps, message_history=message_history)
        decision = result.data.is_research_request
        reasoning = result.data.reasoning
        
        # Stream routing feedback to user
        if decision:
            writer("🔬 Detected research/outreach request. Starting sequential workflow...\n\n")
        else:
            writer("💬 Routing to conversation mode...\n\n")
        
        return {
            "is_research_request": decision,
            "routing_reason": reasoning
        }
        
    except Exception as e:
        print(f"Error in guardrail: {e}")
        writer("⚠️ Guardrail failed, defaulting to conversation mode\n\n")
        return {
            "is_research_request": False,
            "routing_reason": f"Guardrail error: {str(e)}"
        }


async def research_node(state: SequentialAgentState, writer) -> dict:
    """Research agent with streaming using .iter() pattern"""
    try:
        # Agent separator
        writer("\n\n### 🔍 Research Agent Starting...\n")
        
        deps = create_research_deps(session_id=state.get("session_id"))
        agent_input = state["query"]
        message_history = state.get("pydantic_message_history", [])
        full_response = ""
        streaming_success = False
        research_sources = []
        
        try:
            # Use .iter() for streaming with message history
            async with research_agent.iter(agent_input, deps=deps, message_history=message_history) as run:
                async for node in run:
                    if Agent.is_model_request_node(node):
                        # Stream tokens from the model's request
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                    writer(event.part.content)
                                    full_response += event.part.content
                                elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                    delta = event.delta.content_delta
                                    writer(delta)
                                    full_response += delta
            streaming_success = True
            
            # Get final result but DON'T capture new messages for history
            if run.result and run.result.data and not full_response:
                full_response = str(run.result.data)
                writer(full_response)
                
        except Exception as stream_error:
            # Non-streaming fallback
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await research_agent.run(agent_input, deps=deps, message_history=message_history)
            full_response = str(run.data) if run.data else "No response generated"
            writer(full_response)
            streaming_success = False
        
        # Extract sources from response (simple URL extraction)
        if "http" in full_response:
            import re
            urls = re.findall(r'https?://[^\s]+', full_response)
            research_sources = [{"url": url, "title": "Source"} for url in urls[:5]]
        
        return {
            "research_summary": full_response,
            "research_sources": research_sources,
            "agent_type": "research",
            "streaming_success": streaming_success
            # NO message_history key - this agent doesn't update conversation history
        }
        
    except Exception as e:
        error_msg = f"Research error: {str(e)}"
        writer(error_msg)
        return {
            "research_summary": error_msg,
            "research_sources": [],
            "agent_type": "error",
            "streaming_success": False
        }


async def enrichment_node(state: SequentialAgentState, writer) -> dict:
    """Enrichment agent with streaming using .iter() pattern"""
    try:
        # Agent separator
        writer("\n\n### 📊 Enrichment Agent Starting...\n")
        
        deps = create_research_deps(session_id=state.get("session_id"))
        
        # Construct enrichment prompt with previous research
        enrichment_prompt = f"""
        Based on the following initial research findings, please find additional information to enrich the data:
        
        Original Request: {state["query"]}
        
        Initial Research Summary:
        {state.get("research_summary", "No initial research available")}
        
        Focus on finding missing details like:
        - More complete contact information
        - Detailed company information (size, industry, recent news)
        - Educational background
        - Professional connections
        - Recent activities or achievements
        
        Provide ONLY a comprehensive enrichment summary with your findings.
        """
        
        message_history = state.get("pydantic_message_history", [])
        full_response = ""
        streaming_success = False
        enriched_data = {}
        
        try:
            # Use .iter() for streaming with message history
            async with enrichment_agent.iter(enrichment_prompt, deps=deps, message_history=message_history) as run:
                async for node in run:
                    if Agent.is_model_request_node(node):
                        # Stream tokens from the model's request
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                    writer(event.part.content)
                                    full_response += event.part.content
                                elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                    delta = event.delta.content_delta
                                    writer(delta)
                                    full_response += delta
            streaming_success = True
            
            # Get final result but DON'T capture new messages for history
            if run.result and run.result.data and not full_response:
                full_response = str(run.result.data)
                writer(full_response)
                
        except Exception as stream_error:
            # Non-streaming fallback
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await enrichment_agent.run(enrichment_prompt, deps=deps, message_history=message_history)
            full_response = str(run.data) if run.data else "No response generated"
            writer(full_response)
            streaming_success = False
        
        # Simple data extraction - in practice you'd parse the response more carefully
        enriched_data = {
            "summary": full_response,
            "timestamp": "enrichment_completed"
        }
        
        return {
            "enrichment_summary": full_response,
            "enriched_data": enriched_data,
            "agent_type": "enrichment",
            "streaming_success": streaming_success
            # NO message_history key - this agent doesn't update conversation history
        }
        
    except Exception as e:
        error_msg = f"Enrichment error: {str(e)}"
        writer(error_msg)
        return {
            "enrichment_summary": error_msg,
            "enriched_data": {},
            "agent_type": "error",
            "streaming_success": False
        }


async def email_draft_node(state: SequentialAgentState, writer) -> dict:
    """Email draft agent that creates Gmail draft and updates history"""
    try:
        # Agent separator
        writer("\n\n### ✉️ Email Draft Agent Starting...\n")
        
        deps = create_email_deps(session_id=state.get("session_id"))
        
        # Construct comprehensive prompt with all accumulated research
        email_prompt = f"""
        Create a professional outreach email based on the following research:
        
        Original Request: {state["query"]}
        
        Initial Research:
        {state.get("research_summary", "No initial research available")}
        
        Additional Enrichment Data:
        {state.get("enrichment_summary", "No enrichment data available")}
        
        Please create a well-structured email draft that:
        1. Has an appropriate greeting
        2. References specific findings from the research
        3. Provides clear value proposition
        4. Includes a professional closing
        5. Maintains a friendly but professional tone
        
        Format the email properly with subject line, greeting, body, and closing.
        """
        
        message_history = state.get("pydantic_message_history", [])
        full_response = ""
        streaming_success = False
        
        try:
            # Use .iter() for streaming with message history
            async with email_draft_agent.iter(email_prompt, deps=deps, message_history=message_history) as run:
                async for node in run:
                    if Agent.is_model_request_node(node):
                        # Stream tokens from the model's request
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                    writer(event.part.content)
                                    full_response += event.part.content
                                elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                    delta = event.delta.content_delta
                                    writer(delta)
                                    full_response += delta
            streaming_success = True
            
            # CRITICAL: Capture new messages for conversation history
            new_messages = run.result.new_messages_json()
                
        except Exception as stream_error:
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await email_draft_agent.run(email_prompt, deps=deps, message_history=message_history)
            full_response = str(run.data) if run.data else "No response generated"
            writer(full_response)
            streaming_success = False
            
            # Capture new messages from fallback run
            new_messages = run.new_messages_json()
        
        # Notify user about draft location
        writer("\n\n### ✉️ Email draft has been created in your Gmail drafts folder.")
        
        return {
            "final_response": full_response,
            "email_draft_created": True,
            "agent_type": "email_draft",
            "streaming_success": streaming_success,
            "message_history": [new_messages]  # THIS agent updates history
        }
        
    except Exception as e:
        error_msg = f"Email draft error: {str(e)}"
        writer(error_msg)
        return {
            "final_response": error_msg,
            "email_draft_created": False,
            "agent_type": "error",
            "streaming_success": False,
            "message_history": []
        }


async def fallback_node(state: SequentialAgentState, writer) -> dict:
    """Fallback node for normal conversation"""
    try:
        # Agent separator
        writer("\n\n💬 Conversation Agent Starting...\n\n")
        
        deps = create_guardrail_deps(session_id=state.get("session_id"))
        agent_input = state["query"]
        message_history = state.get("pydantic_message_history", [])
        full_response = ""
        streaming_success = False
        
        try:
            # Use .iter() for streaming with message history
            async with fallback_agent.iter(agent_input, deps=deps, message_history=message_history) as run:
                async for node in run:
                    if Agent.is_model_request_node(node):
                        # Stream tokens from the model's request
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                    writer(event.part.content)
                                    full_response += event.part.content
                                elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                    delta = event.delta.content_delta
                                    writer(delta)
                                    full_response += delta
            streaming_success = True
            
            # CRITICAL: Capture new messages for conversation history
            new_messages = run.result.new_messages_json()
                
        except Exception as stream_error:
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await fallback_agent.run(agent_input, deps=deps, message_history=message_history)
            full_response = str(run.data) if run.data else "No response generated"
            writer(full_response)
            streaming_success = False
            
            # Capture new messages from fallback run
            new_messages = run.new_messages_json()
        
        return {
            "final_response": full_response,
            "agent_type": "fallback",
            "streaming_success": streaming_success,
            "message_history": [new_messages]  # THIS agent updates history
        }
        
    except Exception as e:
        error_msg = f"Fallback error: {str(e)}"
        writer(error_msg)
        return {
            "final_response": error_msg,
            "agent_type": "error",
            "streaming_success": False,
            "message_history": []
        }


def route_after_guardrail(state: SequentialAgentState) -> str:
    """Conditional routing based on guardrail decision"""
    if state.get("is_research_request", False):
        return "research_node"
    else:
        return "fallback_node"


def create_workflow():
    """Create and configure the sequential agent workflow"""
    
    # Create state graph
    builder = StateGraph(SequentialAgentState)
    
    # Add nodes
    builder.add_node("guardrail_node", guardrail_node)
    builder.add_node("research_node", research_node)
    builder.add_node("enrichment_node", enrichment_node)
    builder.add_node("email_draft_node", email_draft_node)
    builder.add_node("fallback_node", fallback_node)
    
    # Set entry point
    builder.add_edge(START, "guardrail_node")
    
    # Add conditional routing after guardrail
    builder.add_conditional_edges(
        "guardrail_node",
        route_after_guardrail,
        {
            "research_node": "research_node",
            "fallback_node": "fallback_node"
        }
    )
    
    # Sequential edges for research flow
    builder.add_edge("research_node", "enrichment_node")
    builder.add_edge("enrichment_node", "email_draft_node")
    builder.add_edge("email_draft_node", END)
    builder.add_edge("fallback_node", END)
    
    # Compile the graph
    return builder.compile()


# Create the workflow instance
workflow = create_workflow()


def create_api_initial_state(
    query: str,
    session_id: str,
    request_id: str,
    pydantic_message_history: Optional[List[ModelMessage]] = None
) -> SequentialAgentState:
    """Create initial state for API mode"""
    return {
        "query": query,
        "session_id": session_id,
        "request_id": request_id,
        "is_research_request": False,
        "routing_reason": "",
        "research_summary": "",
        "research_sources": [],
        "enrichment_summary": "",
        "enriched_data": {},
        "email_draft_created": False,
        "draft_id": None,
        "final_response": "",
        "agent_type": "",
        "pydantic_message_history": pydantic_message_history or [],
        "message_history": [],
        "conversation_title": None,
        "is_new_conversation": False
    }


def extract_api_response_data(state: SequentialAgentState) -> Dict[str, Any]:
    """Extract response data for API return"""
    return {
        "session_id": state.get("session_id"),
        "request_id": state.get("request_id"),
        "query": state["query"],
        "response": state.get("final_response", ""),
        "agent_type": state.get("agent_type", "unknown"),
        "is_research_request": state.get("is_research_request", False),
        "routing_reason": state.get("routing_reason", ""),
        "research_summary": state.get("research_summary", ""),
        "enrichment_summary": state.get("enrichment_summary", ""),
        "email_draft_created": state.get("email_draft_created", False),
        "conversation_title": state.get("conversation_title"),
        "is_new_conversation": state.get("is_new_conversation", False)
    }