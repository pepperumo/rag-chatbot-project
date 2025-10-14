from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

from graph.state import RouterState
from agents.router_agent import router_agent
from agents.web_search_agent import web_search_agent
from agents.email_search_agent import email_search_agent
from agents.rag_search_agent import rag_search_agent
from agents.deps import create_router_deps, create_search_agent_deps
from pydantic_ai.messages import ModelMessage
from pydantic_ai import Agent
from pydantic_ai.messages import PartDeltaEvent, PartStartEvent, TextPartDelta

load_dotenv()


async def router_node(state: RouterState, writer) -> dict:
    """Router node that determines which agent to use"""
    try:
        deps = create_router_deps(session_id=state.get("session_id"))
        
        # PATTERN: Get structured routing decision with message history
        message_history = state.get("pydantic_message_history", [])
        result = await router_agent.run(state["query"], deps=deps, message_history=message_history)
        decision = result.data.decision
        
        # PATTERN: Stream routing feedback to user
        writer(f"🔀 Routing to: {decision}\n\n")
        
        return {
            "routing_decision": decision,
            "router_confidence": "high"
        }
        
    except Exception as e:
        print(f"Error routing request: {e}")
        # PATTERN: Fallback on router failure
        writer("⚠️ Router failed, defaulting to web search\n\n")
        return {
            "routing_decision": "web_search", 
            "router_confidence": "fallback"
        }


async def web_search_node(state: RouterState, writer) -> dict:
    """Web search agent with streaming using .iter() pattern"""
    try:
        deps = create_search_agent_deps(session_id=state.get("session_id"))
        agent_input = state["query"]
        message_history = state.get("pydantic_message_history", [])
        full_response = ""
        streaming_success = False
        
        try:
            # PATTERN: Use .iter() for streaming with message history
            async with web_search_agent.iter(agent_input, deps=deps, message_history=message_history) as run:
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
                
                # Get final result and capture new messages
                if run.result and run.result.data and not full_response:
                    full_response = str(run.result.data)
                    writer(full_response)
                
                # Capture new messages for conversation history
                new_messages = run.result.new_messages_json()
                    
        except Exception as stream_error:
            # PATTERN: Non-streaming fallback
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await web_search_agent.run(agent_input, deps=deps, message_history=message_history)
            full_response = str(run.data) if run.data else "No response generated"
            writer(full_response)
            streaming_success = False
            
            # Capture new messages from fallback run
            new_messages = run.new_messages_json()
        
        return {
            "final_response": full_response,
            "agent_type": "web_search",
            "streaming_success": streaming_success,
            "message_history": [new_messages]
        }
        
    except Exception as e:
        error_msg = f"Web search error: {str(e)}"
        writer(error_msg)
        return {
            "final_response": error_msg,
            "agent_type": "error",
            "streaming_success": False,
            "message_history": []
        }


async def email_search_node(state: RouterState, writer) -> dict:
    """Email search agent with streaming using .iter() pattern"""
    try:
        deps = create_search_agent_deps(session_id=state.get("session_id"))
        agent_input = state["query"]
        message_history = state.get("pydantic_message_history", [])
        full_response = ""
        streaming_success = False
        
        try:
            # PATTERN: Use .iter() for streaming with message history
            async with email_search_agent.iter(agent_input, deps=deps, message_history=message_history) as run:
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
                
                # Get final result and capture new messages
                if run.result and run.result.data and not full_response:
                    full_response = str(run.result.data)
                    writer(full_response)
                
                # Capture new messages for conversation history
                new_messages = run.result.new_messages_json()
                    
        except Exception as stream_error:
            # PATTERN: Non-streaming fallback
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await email_search_agent.run(agent_input, deps=deps, message_history=message_history)
            full_response = str(run.data) if run.data else "No response generated"
            writer(full_response)
            streaming_success = False
            
            # Capture new messages from fallback run
            new_messages = run.new_messages_json()
        
        return {
            "final_response": full_response,
            "agent_type": "email_search",
            "streaming_success": streaming_success,
            "message_history": [new_messages]
        }
        
    except Exception as e:
        error_msg = f"Email search error: {str(e)}"
        writer(error_msg)
        return {
            "final_response": error_msg,
            "agent_type": "error",
            "streaming_success": False,
            "message_history": []
        }


async def rag_search_node(state: RouterState, writer) -> dict:
    """RAG search agent with streaming using .iter() pattern"""
    try:
        deps = create_search_agent_deps(session_id=state.get("session_id"))
        agent_input = state["query"]
        message_history = state.get("pydantic_message_history", [])
        full_response = ""
        streaming_success = False
        
        try:
            # PATTERN: Use .iter() for streaming with message history
            async with rag_search_agent.iter(agent_input, deps=deps, message_history=message_history) as run:
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
                
                # Get final result and capture new messages
                if run.result and run.result.data and not full_response:
                    full_response = str(run.result.data)
                    writer(full_response)
                
                # Capture new messages for conversation history
                new_messages = run.result.new_messages_json()
                    
        except Exception as stream_error:
            # PATTERN: Non-streaming fallback
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await rag_search_agent.run(agent_input, deps=deps, message_history=message_history)
            full_response = str(run.data) if run.data else "No response generated"
            writer(full_response)
            streaming_success = False
            
            # Capture new messages from fallback run
            new_messages = run.new_messages_json()
        
        return {
            "final_response": full_response,
            "agent_type": "rag_search",
            "streaming_success": streaming_success,
            "message_history": [new_messages]
        }
        
    except Exception as e:
        error_msg = f"RAG search error: {str(e)}"
        writer(error_msg)
        return {
            "final_response": error_msg,
            "agent_type": "error",
            "streaming_success": False,
            "message_history": []
        }


async def fallback_node(state: RouterState, writer) -> dict:
    """Fallback node for unclear or invalid requests"""
    try:
        fallback_message = f"""
I understand you're asking: "{state['query']}"

However, this query doesn't clearly fit into my specialized search capabilities:
- **Web Search**: For current events, news, research topics, general information
- **Email Search**: For finding emails, checking inbox, searching conversations  
- **Document Search**: For questions about documents, files, or knowledge base content

Could you rephrase your question to be more specific about what type of information you're looking for?

For example:
- "What's the latest news about..." (web search)
- "Find emails from..." (email search)  
- "What does the documentation say about..." (document search)
"""
        
        writer(fallback_message)
        
        return {
            "final_response": fallback_message,
            "agent_type": "fallback",
            "streaming_success": True,
            "message_history": []  # Fallback doesn't use LLM, so no new messages
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


def route_based_on_decision(state: RouterState) -> str:
    """Conditional routing based on router decision"""
    decision = state.get("routing_decision", "fallback")
    
    # PATTERN: Map decisions to node names
    routing_map = {
        "web_search": "web_search_node",
        "email_search": "email_search_node", 
        "rag_search": "rag_search_node",
        "fallback": "fallback_node"
    }
    
    return routing_map.get(decision, "fallback_node")


def create_workflow():
    """Create and configure the LangGraph routing workflow"""
    
    # Create state graph
    builder = StateGraph(RouterState)
    
    # Add nodes
    builder.add_node("router_node", router_node)
    builder.add_node("web_search_node", web_search_node)
    builder.add_node("email_search_node", email_search_node)
    builder.add_node("rag_search_node", rag_search_node)
    builder.add_node("fallback_node", fallback_node)
    
    # Set entry point
    builder.add_edge(START, "router_node")
    
    # Add conditional routing after router
    builder.add_conditional_edges(
        "router_node",
        route_based_on_decision,
        {
            "web_search_node": "web_search_node",
            "email_search_node": "email_search_node",
            "rag_search_node": "rag_search_node",
            "fallback_node": "fallback_node"
        }
    )
    
    # All agent nodes go to END
    builder.add_edge("web_search_node", END)
    builder.add_edge("email_search_node", END)
    builder.add_edge("rag_search_node", END)
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
) -> RouterState:
    """Create initial state for API mode"""
    return {
        "query": query,
        "session_id": session_id,
        "request_id": request_id,
        "routing_decision": "",
        "router_confidence": "",
        "final_response": "",
        "agent_type": "",
        "streaming_success": False,
        "message_history": [],
        "pydantic_message_history": pydantic_message_history or [],
        "conversation_title": None,
        "is_new_conversation": False
    }


def extract_api_response_data(state: RouterState) -> Dict[str, Any]:
    """Extract response data for API return"""
    return {
        "session_id": state.get("session_id"),
        "request_id": state.get("request_id"),
        "query": state["query"],
        "response": state.get("final_response", ""),
        "agent_type": state.get("agent_type", "unknown"),
        "routing_decision": state.get("routing_decision", "unknown"),
        "streaming_success": state.get("streaming_success", False),
        "conversation_title": state.get("conversation_title"),
        "is_new_conversation": state.get("is_new_conversation", False)
    }