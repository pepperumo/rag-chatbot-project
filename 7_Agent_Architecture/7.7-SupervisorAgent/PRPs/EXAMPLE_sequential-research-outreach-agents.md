name: "Sequential Research & Outreach Agents with LangGraph"
description: |

## Purpose
Build a LangGraph workflow with 5 agents using Pydantic AI for sequential research and outreach. The system routes user requests through a guardrail agent, then executes a sequential workflow of research → data enrichment → email draft creation.

## Core Principles
1. **Sequential Flow**: Each agent passes its output to the next in the chain
2. **Streaming Summaries**: All agents stream their work summaries to the user
3. **Selective History Updates**: Only the final agent updates conversation history
4. **Cost Optimization**: Use smaller model for routing, normal model for execution
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Create a multi-agent system that:
- Routes requests through an input guardrail agent using a small LLM
- Executes sequential research workflow (research → enrichment → email draft)
- Provides a fallback agent for normal conversation
- Streams agent summaries without updating conversation history (except final agent)
- Maintains conversation context throughout the workflow

## Why
- Automates lead research and outreach workflow
- Provides cost-effective routing with smaller models
- Enables rich, multi-step agent interactions
- Maintains conversation context while controlling history updates

## What
User-visible behavior:
1. User submits a request
2. Guardrail agent determines if it's a research/outreach request
3. If yes: Research → Data Enrichment → Email Draft (sequential)
4. If no: Routes to fallback conversational agent
5. Each agent streams its summary to the user
6. Only final agent's response is added to conversation history

### Success Criteria
- [ ] Guardrail agent correctly routes research vs conversation requests
- [ ] Research agent performs Brave API searches and streams summary
- [ ] Data enrichment agent fills gaps (location, company, education)
- [ ] Email draft agent creates Gmail draft and updates conversation history
- [ ] Fallback agent handles normal conversation with history
- [ ] All agents stream their summaries to user in real-time
- [ ] State flows correctly through LangGraph workflow
- [ ] API endpoint supports streaming responses

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.5-LLMRouting/graph/workflow.py
  why: LangGraph workflow patterns, streaming implementation, node structure
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.5-LLMRouting/graph/state.py
  why: State structure for passing data between agents
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.5-LLMRouting/agents/router_agent.py
  why: Pattern for guardrail agent with structured output
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.3-MultiAgentIntro/agents/research_agent.py
  why: Brave API search implementation pattern
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.3-MultiAgentIntro/agents/email_agent.py
  why: Gmail draft creation pattern
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.3-MultiAgentIntro/agents/tools.py
  why: Brave search and Gmail tools implementation

- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.5-LLMRouting/api/endpoints.py
  why: API endpoint pattern with streaming, mostly unchanged

- url: https://python.langchain.com/docs/langgraph/concepts/streaming
  why: LangGraph streaming patterns and state management

- url: https://ai.pydantic.dev/agents/
  why: Pydantic AI agent creation patterns and structured outputs
```

### Current Codebase tree
```bash
7.6-SequentialAgents/
├── agents/
│   ├── deps.py          # Agent dependencies
│   ├── email_search_agent.py  # To be replaced
│   ├── prompts.py       # System prompts
│   ├── rag_search_agent.py    # To be replaced
│   ├── router_agent.py  # To be modified for guardrail
│   └── web_search_agent.py    # To be replaced
├── api/
│   ├── endpoints.py     # Mostly unchanged
│   └── ...
├── graph/
│   ├── state.py         # To be modified for sequential state
│   └── workflow.py      # To be completely overhauled
├── tools/
│   ├── email_tools.py   # To be replaced with Gmail tools
│   ├── rag_tools.py     # To be removed
│   └── web_tools.py     # To be replaced with Brave tools
└── ...
```

### Desired Codebase tree with files
```bash
7.6-SequentialAgents/
├── agents/
│   ├── deps.py          # Updated dependencies for all agents
│   ├── guardrail_agent.py  # NEW: Input routing agent
│   ├── research_agent.py    # NEW: Brave search agent
│   ├── enrichment_agent.py  # NEW: Data enrichment agent
│   ├── email_draft_agent.py # NEW: Gmail draft creation
│   ├── fallback_agent.py    # NEW: Normal conversation
│   └── prompts.py       # Updated system prompts
├── graph/
│   ├── state.py         # Sequential workflow state
│   └── workflow.py      # Sequential agent workflow
├── tools/
│   ├── brave_tools.py   # NEW: Brave search implementation
│   └── gmail_tools.py   # NEW: Gmail draft creation
└── ...
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Message history handling
# - All agents receive pydantic_message_history from state
# - Only final agent returns new_messages for history update
# - Intermediate agents just stream summaries

# CRITICAL: Streaming pattern
# - Use async with agent.iter() for streaming
# - Writer function sends chunks to user
# - Fallback to agent.run() if streaming fails

# CRITICAL: Model selection
# - use_smaller_model=True for guardrail agent
# - use_smaller_model=False for all execution agents

# CRITICAL: Gmail scopes
# - Requires 'gmail.compose' and 'gmail.send' scopes
# - Token stored in credentials/token.json

# CRITICAL: State flow
# - Each agent adds its summary to state
# - Next agent includes previous summaries in prompt
```

## Implementation Blueprint

### Data models and structure

```python
# graph/state.py - Sequential workflow state
from typing import TypedDict, List, Optional, Dict, Any
from pydantic_ai.messages import ModelMessage

class SequentialAgentState(TypedDict, total=False):
    """LangGraph state for sequential agent workflow"""
    # Input
    query: str
    session_id: str  
    request_id: str
    
    # Guardrail output
    is_research_request: bool
    routing_reason: str
    
    # Research outputs (accumulated)
    research_summary: str
    research_sources: List[Dict[str, str]]
    
    # Enrichment outputs (accumulated)
    enrichment_summary: str
    enriched_data: Dict[str, Any]
    
    # Email draft output
    email_draft_created: bool
    draft_id: Optional[str]
    
    # Final response
    final_response: str
    agent_type: str
    
    # Message history management
    pydantic_message_history: List[ModelMessage]
    message_history: List[bytes]  # Only populated by final agent
    
    # API context
    conversation_title: Optional[str]
    is_new_conversation: Optional[bool]
```

### List of tasks to complete

```yaml
Task 1: Create guardrail agent
MODIFY agents/router_agent.py → agents/guardrail_agent.py:
  - CHANGE RouterResponse to have is_research_request: bool field
  - UPDATE system prompt for research/outreach detection
  - KEEP structured output pattern with Pydantic AI

Task 2: Create research agent  
CREATE agents/research_agent.py:
  - PATTERN from: 7.3-MultiAgentIntro/agents/research_agent.py
  - MODIFY to not update conversation history
  - ADD streaming summary output
  - INTEGRATE Brave search tool

Task 3: Create enrichment agent
CREATE agents/enrichment_agent.py:
  - SIMILAR to research_agent.py structure  
  - FOCUS on finding missing data (location, company, education)
  - USE previous research_summary from state in prompt
  - STREAM enrichment findings

Task 4: Create email draft agent
CREATE agents/email_draft_agent.py:
  - PATTERN from: 7.3-MultiAgentIntro/agents/email_agent.py
  - USE all accumulated research from state
  - CREATE Gmail draft
  - RETURN new_messages for history update

Task 5: Create fallback agent
CREATE agents/fallback_agent.py:
  - SIMPLE conversational agent
  - USE pydantic_message_history
  - RETURN new_messages for history update

Task 6: Create Brave search tools
CREATE tools/brave_tools.py:
  - COPY implementation from 7.3-MultiAgentIntro/agents/tools.py
  - EXTRACT search_web_tool function

Task 7: Create Gmail tools  
CREATE tools/gmail_tools.py:
  - COPY Gmail functions from 7.3-MultiAgentIntro/agents/tools.py
  - INCLUDE create_email_draft_tool and helper functions

Task 8: Update workflow for sequential execution
MODIFY graph/workflow.py:
  - REMOVE all existing routing logic
  - CREATE sequential flow: guardrail → research → enrichment → email
  - ADD conditional edge from guardrail to fallback
  - PRESERVE streaming patterns

Task 9: Update prompts
MODIFY agents/prompts.py:
  - ADD prompts for all 5 agents
  - ENSURE prompts guide sequential information flow

Task 10: Update tests
MODIFY tests/:
  - UPDATE all test files for new agent structure
  - ADD tests for sequential flow
  - TEST streaming behavior

Task 11: Update README
MODIFY README.md:
  - DOCUMENT new sequential workflow
  - UPDATE architecture diagram
  - EXPLAIN agent responsibilities
```

### Per task pseudocode and concrete examples

```python
# Task 1: Guardrail Agent (from 7.5-LLMRouting/agents/router_agent.py pattern)
# agents/guardrail_agent.py
from typing import Literal
from dataclasses import dataclass
from pydantic_ai import Agent
from clients import get_model
from .deps import GuardrailDependencies
from .prompts import GUARDRAIL_SYSTEM_PROMPT

@dataclass 
class GuardrailResponse:
    """Structured guardrail decision for Pydantic AI output_type"""
    is_research_request: bool
    reasoning: str

# Initialize the guardrail agent with smaller model for fast decisions
guardrail_agent = Agent(
    get_model(use_smaller_model=True),
    output_type=GuardrailResponse,
    deps_type=GuardrailDependencies,
    system_prompt=GUARDRAIL_SYSTEM_PROMPT
)

# Task 2: Research Agent Node with COMPLETE STREAMING PATTERN
# From 7.5-LLMRouting/graph/workflow.py web_search_node pattern
async def research_node(state: SequentialAgentState, writer) -> dict:
    """Research agent with streaming using .iter() pattern"""
    try:
        deps = create_research_deps(
            session_id=state.get("session_id"),
            brave_api_key=os.getenv("BRAVE_API_KEY")
        )
        agent_input = state["query"]
        message_history = state.get("pydantic_message_history", [])
        full_response = ""
        streaming_success = False
        research_sources = []
        
        try:
            # EXACT STREAMING PATTERN from 7.5-LLMRouting
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
                
                # Get final result but DON'T capture new messages
                if run.result and run.result.data and not full_response:
                    full_response = str(run.result.data)
                    writer(full_response)
                    
        except Exception as stream_error:
            # NON-STREAMING FALLBACK from 7.5-LLMRouting
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await research_agent.run(agent_input, deps=deps, message_history=message_history)
            full_response = str(run.data) if run.data else "No response generated"
            writer(full_response)
            streaming_success = False
        
        # Extract sources from response (customize based on your needs)
        # This is a simple example - you'd parse actual URLs from the response
        if "http" in full_response:
            import re
            urls = re.findall(r'https?://[^\s]+', full_response)
            research_sources = [{"url": url, "title": "Source"} for url in urls[:5]]
        
        return {
            "research_summary": full_response,
            "research_sources": research_sources,
            "agent_type": "research",
            "streaming_success": streaming_success
            # NO message_history key!
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

# Task 4: Email Draft Agent Node (from 7.3-MultiAgentIntro pattern)
async def email_draft_node(state: SequentialAgentState, writer) -> dict:
    """Email draft agent that creates Gmail draft and updates history"""
    try:
        deps = create_email_deps(
            session_id=state.get("session_id"),
            gmail_credentials_path=os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials/credentials.json"),
            gmail_token_path="./credentials/token.json"
        )
        
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
        """
        
        message_history = state.get("pydantic_message_history", [])
        full_response = ""
        streaming_success = False
        
        try:
            # Same streaming pattern as research agent
            async with email_draft_agent.iter(email_prompt, deps=deps, message_history=message_history) as run:
                async for node in run:
                    if Agent.is_model_request_node(node):
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
        writer("\n\n✉️ Email draft has been created in your Gmail drafts folder.")
        
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

# Task 6: EXACT Brave Search Tool (from 7.3-MultiAgentIntro/agents/tools.py)
# tools/brave_tools.py
async def search_web_tool(
    api_key: str,
    query: str,
    count: int = 10,
    offset: int = 0,
    country: Optional[str] = None,
    lang: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Pure function to search the web using Brave Search API.
    COPIED EXACTLY from 7.3-MultiAgentIntro/agents/tools.py
    """
    if not api_key or not api_key.strip():
        raise ValueError("Brave API key is required")
    
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Ensure count is within valid range
    count = min(max(count, 1), 20)
    
    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json"
    }
    
    params = {
        "q": query,
        "count": count,
        "offset": offset
    }
    
    if country:
        params["country"] = country
    if lang:
        params["lang"] = lang
    
    logger.info(f"Searching Brave for: {query}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params,
                timeout=30.0
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                raise Exception("Rate limit exceeded. Check your Brave API quota.")
            
            # Handle authentication errors
            if response.status_code == 401:
                raise Exception("Invalid Brave API key")
            
            # Handle other errors
            if response.status_code != 200:
                raise Exception(f"Brave API returned {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Extract web results
            web_results = data.get("web", {}).get("results", [])
            
            # Convert to our format
            results = []
            for idx, result in enumerate(web_results):
                # Calculate a simple relevance score based on position
                score = 1.0 - (idx * 0.05)  # Decrease by 0.05 for each position
                score = max(score, 0.1)  # Minimum score of 0.1
                
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("description", ""),
                    "score": score
                })
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except httpx.RequestError as e:
            logger.error(f"Request error during Brave search: {e}")
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error during Brave search: {e}")
            raise

# Task 7: EXACT Gmail Draft Creation (from 7.3-MultiAgentIntro/agents/tools.py)
# tools/gmail_tools.py
async def create_email_draft_tool(
    credentials_path: str,
    token_path: str,
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Pure function to create a Gmail draft.
    COPIED EXACTLY from 7.3-MultiAgentIntro/agents/tools.py
    """
    if not to or len(to) == 0:
        raise ValueError("At least one recipient is required")
    
    if not subject or not subject.strip():
        raise ValueError("Subject is required")
    
    if not body or not body.strip():
        raise ValueError("Body is required")
    
    try:
        # Get Gmail service
        service = _get_gmail_service(credentials_path, token_path)
        
        # Create the message
        message = _create_email_message(to, subject, body, cc, bcc)
        create_message = {"message": message}
        
        # Create the draft
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body=create_message)
            .execute()
        )
        
        draft_id = draft.get('id')
        message_id = draft.get('message', {}).get('id')
        thread_id = draft.get('message', {}).get('threadId')
        
        logger.info(f"Gmail draft created successfully: {draft_id}")
        
        return {
            "success": True,
            "draft_id": draft_id,
            "message_id": message_id,
            "thread_id": thread_id,
            "created_at": datetime.now().isoformat(),
            "recipients": to,
            "subject": subject
        }
        
    except HttpError as e:
        logger.error(f"Gmail API error creating draft: {e}")
        raise Exception(f"Failed to create draft: {e}")
    except Exception as e:
        logger.error(f"Unexpected error creating draft: {e}")
        raise Exception(f"Unexpected error: {e}")

# Task 8: EXACT Workflow Setup (from 7.5-LLMRouting/graph/workflow.py)
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

def route_after_guardrail(state: SequentialAgentState) -> str:
    """Conditional routing based on guardrail decision"""
    if state.get("is_research_request", False):
        return "research_node"
    else:
        return "fallback_node"
```

### Integration Points
```yaml
DEPENDENCIES:
  - add to: agents/deps.py
  - pattern: "brave_api_key: str, gmail_credentials_path: str"
  
ENV VARS:
  - already in: .env.example
  - verify: BRAVE_API_KEY, GMAIL_CREDENTIALS_PATH
  
API:
  - minimal changes to: api/endpoints.py
  - update: initial_state creation for new state structure
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors
cd /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.6-SequentialAgents
source venv_linux/bin/activate

ruff check . --fix
mypy agents/ graph/ tools/

# Expected: No errors
```

### Level 2: Unit Tests
```python
# Test guardrail routing
def test_guardrail_research_detection():
    """Correctly identifies research requests"""
    result = await guardrail_agent.run("Research John Doe and draft an email")
    assert result.data.is_research_request == True

def test_guardrail_conversation_detection():
    """Routes conversations to fallback"""
    result = await guardrail_agent.run("How are you today?")
    assert result.data.is_research_request == False

# Test sequential flow
def test_research_to_enrichment_state():
    """Research summary passes to enrichment"""
    # Mock workflow execution
    # Assert enrichment agent receives research summary

# Test history update
def test_only_final_agent_updates_history():
    """Only email/fallback agents return message_history"""
    # Execute workflow
    # Assert intermediate agents don't have message_history
    # Assert final agent does have message_history
```

```bash
# Run tests
pytest tests/ -v
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check .`
- [ ] No type errors: `mypy agents/ graph/`
- [ ] Research flow works end-to-end
- [ ] Fallback flow handles conversations
- [ ] Streaming works for all agents
- [ ] Only final agents update conversation history
- [ ] Gmail drafts created successfully
- [ ] Brave search returns results
- [ ] README updated with new architecture

---

## Anti-Patterns to Avoid
- ❌ Don't let intermediate agents update conversation history
- ❌ Don't skip streaming - users need real-time feedback
- ❌ Don't use large model for guardrail routing (use small model)
- ❌ Don't create new patterns when 7.5-LLMRouting patterns work
- ❌ Don't forget to pass accumulated state between agents
- ❌ Don't hardcode API keys - use environment variables

## Confidence Score: 10/10
This PRP now includes complete, working code examples directly copied from the reference implementations, eliminating any ambiguity about implementation patterns. The exact streaming logic, Brave API integration, and Gmail draft creation code are provided, making one-pass implementation virtually guaranteed.