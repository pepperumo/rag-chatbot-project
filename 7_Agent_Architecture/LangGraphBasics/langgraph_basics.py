#!/usr/bin/env python3
"""
LangGraph React Agent - Core Components Demonstration

This script demonstrates the three fundamental components of LangGraph:
1. STATE: Shared data structure that flows through the graph
2. NODES: Python functions that process and transform state
3. GRAPH BUILDING: How we connect nodes with edges to create workflows

LangGraph models agent workflows as directed graphs where:
- State represents the current snapshot of data/context
- Nodes encode agent logic and receive/return state
- Edges determine the flow between nodes (direct or conditional)

This implementation showcases a ReAct (Reasoning + Acting) pattern where
an agent can reason about problems and use tools when needed.
"""

import os
import json
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

# LangGraph imports - Core framework for building stateful agent workflows
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# LangChain imports - LLM and tool integration
from langchain.chat_models import init_chat_model
from langchain_community.tools import BraveSearch
from langchain_core.messages import ToolMessage, AIMessage

load_dotenv()

# Initialize the LLM and tools globally
# Using GPT-4.1-mini for fast reasoning and tool calling capabilities
llm = init_chat_model("openai:gpt-4.1-mini")
brave_tool = BraveSearch.from_api_key(api_key=os.getenv('BRAVE_API_KEY'), search_kwargs={"count": 3})
tools = [brave_tool]
# Bind tools to LLM so it can decide when and how to use them
llm_with_tools = llm.bind_tools(tools)


# ============================================================================
# 1. STATE DEFINITION - The Foundation of LangGraph
# ============================================================================
class State(TypedDict):
    """
    State Schema for the Agent Graph
    
    The State is LangGraph's most essential component - it contains all data and 
    context available to nodes and edges. State flows through the entire graph,
    getting updated by each node and passed to the next.
    
    Key aspects of State in LangGraph:
    - Shared data structure representing current application snapshot
    - Typically defined as TypedDict (recommended) or Pydantic BaseModel
    - Supports reducer functions to control how updates are applied
    - Determines the input/output schema for the entire graph
    
    In this implementation:
    - messages: List of conversation messages (human inputs, AI responses, tool calls)
    - add_messages: Special reducer that intelligently merges new messages with existing ones
      (handles deduplication, ordering, and proper message chaining)
    """
    messages: Annotated[list, add_messages]


# ============================================================================
# 2. NODE DEFINITIONS - The Logic Processors of LangGraph
# ============================================================================

class BasicToolNode:
    """
    Tool Execution Node - A specialized node for executing tools
    
    Nodes are Python functions (or callable classes like BasicToolNode) that:
    - Receive the current State as input
    - Perform computation, side effects, or transformations
    - Return an updated State
    
    This node specifically handles tool execution in the ReAct pattern:
    1. Extracts tool calls from the last AI message
    2. Executes each requested tool with provided arguments
    3. Formats results as ToolMessage objects
    4. Returns updated state with tool responses
    
    Tool execution flow:
    AI Message with tool_calls → Tool Node → ToolMessage responses → Back to Agent
    """
    
    def __init__(self, tools: list) -> None:
        # Create a lookup dictionary for O(1) tool access by name
        self.tools_by_name = {tool.name: tool for tool in tools}
    
    def __call__(self, inputs: dict):
        """
        Execute tools requested in the last AI message
        
        Args:
            inputs: State dictionary containing messages and other data
            
        Returns:
            dict: Updated state with ToolMessage responses
        """
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        
        outputs = []
        # Process each tool call requested by the AI
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            # Wrap tool results in ToolMessage for proper message chaining
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}


def route_tools(state: State):
    """
    Conditional Edge Function - Intelligent Routing Logic
    
    This function demonstrates conditional routing in LangGraph:
    - Examines the current state to make routing decisions
    - Returns a string that maps to the next node to execute
    - Enables dynamic workflows based on state conditions
    
    Routing Logic:
    - If the last AI message contains tool calls → route to "tools" node
    - If no tool calls present → route to END (conversation complete)
    
    This implements the core ReAct decision loop:
    1. Agent reasons about the problem
    2. Decides if tools are needed (this function determines that)
    3. Either uses tools or provides final answer
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    
    # Check if AI decided to use tools
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"  # Route to tool execution node
    return END  # No tools needed, end the conversation


def agent(state: State):
    """
    Primary Agent Node - The Brain of the ReAct Agent
    
    This node represents the core reasoning component:
    - Processes all messages in the conversation history
    - Uses LLM to reason about the current situation
    - Decides whether to use tools or provide a direct response
    - Returns either a final answer or tool calls for execution
    
    Key responsibilities:
    1. Maintains conversation context through message history
    2. Applies ReAct reasoning (think step-by-step)
    3. Determines appropriate actions (respond or use tools)
    4. Formats responses according to LangGraph message protocol
    
    The LLM is bound with tools, so it can automatically generate
    tool calls when it determines external information is needed.
    """
    # Get the current messages from state - full conversation context
    messages = state["messages"]
    
    # Call the LLM with tools bound - enables automatic tool call generation
    response = llm_with_tools.invoke(messages)
    
    # Return the response in the state update format
    # The add_messages reducer will properly integrate this into the conversation
    return {"messages": [response]}


# ============================================================================
# 3. GRAPH BUILDING - Connecting Nodes with Edges
# ============================================================================

def create_react_agent():
    """
    Graph Construction Function - The Architecture Blueprint
    
    This function demonstrates how to build LangGraph workflows by:
    1. Initializing a StateGraph with the defined State schema
    2. Adding nodes (computation units) to the graph
    3. Connecting nodes with edges (control flow)
    4. Compiling the graph into an executable workflow
    
    Graph Architecture Pattern:
    START → agent → [conditional routing] → tools → agent → END
                  ↘                                      ↗
                    → END (if no tools needed)
    
    Edge Types Demonstrated:
    - Direct edges: Fixed transitions (START→agent, tools→agent)
    - Conditional edges: Dynamic routing based on state (agent→tools or END)
    
    This creates a cyclic graph enabling the ReAct loop:
    Agent can use tools multiple times before providing final answer.
    """
    
    # Initialize the state graph with our State schema
    # This defines the data structure that flows through all nodes
    graph_builder = StateGraph(State)
    
    # Add nodes to the graph
    # Each node is a processing unit that transforms state
    graph_builder.add_node("agent", agent)
    
    # Create and add the tool execution node
    tool_node = BasicToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    
    # Define the graph topology with edges
    # START is a special node representing the entry point
    graph_builder.add_edge(START, "agent")
    
    # Conditional edge: Agent decides next step based on its output
    # This is where the intelligence lies - dynamic routing!
    graph_builder.add_conditional_edges(
        "agent",                    # Source node
        route_tools,               # Decision function
        {"tools": "tools", END: END},  # Mapping: decision → destination
    )
    
    # After using tools, always return to agent for next decision
    # This enables multi-step tool usage and reasoning
    graph_builder.add_edge("tools", "agent")
    
    # Compile the graph into an executable workflow
    # This creates the actual runnable agent from the graph definition
    return graph_builder.compile()


# Create the compiled agent - ready for execution
react_agent = create_react_agent()


# ============================================================================
# EXECUTION AND INTERACTION UTILITIES
# ============================================================================

def stream_graph_updates(graph, user_input: str):
    """
    Stream Graph Execution - Real-time Processing Display
    
    Demonstrates LangGraph's streaming capabilities:
    - Executes the graph with user input as initial state
    - Streams intermediate results as they're generated
    - Provides real-time feedback during agent reasoning
    
    This showcases how LangGraph enables:
    1. Transparent workflow execution
    2. Intermediate step visibility  
    3. Responsive user experience during complex reasoning
    """
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            if "messages" in value and value["messages"]:
                last_message = value["messages"][-1]
                if isinstance(last_message, AIMessage) and last_message.content:
                    print("Assistant:", last_message.content)


def main():
    """
    Main Execution Loop - Interactive Agent Interface
    
    Demonstrates practical LangGraph agent deployment:
    - Creates a compiled graph instance
    - Manages conversation state automatically
    - Handles user interaction and error cases
    - Shows how state persists across multiple interactions
    """
    graph = create_react_agent()

    print("🤖 LangGraph ReAct Agent - Demonstrating Core Components")
    print("📋 State: Messages with add_messages reducer")
    print("🔧 Nodes: Agent (reasoning) + Tools (actions)")
    print("🔀 Edges: Conditional routing based on tool usage")
    print("\nType 'quit', 'exit', or 'q' to stop.\n")
    
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            
            stream_graph_updates(graph, user_input)
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()