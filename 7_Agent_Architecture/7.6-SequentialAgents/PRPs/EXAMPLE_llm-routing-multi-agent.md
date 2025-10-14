name: "LLM Routing Multi-Agent Research System - Comprehensive Implementation PRP"
description: |

## Purpose
Complete implementation guide for building a LangGraph workflow with Pydantic AI agents featuring intelligent LLM-based routing. Provides sufficient context, validation loops, and self-correction capabilities for AI agents to achieve working code through iterative refinement.

## Core Principles
1. **Context is King**: All necessary documentation, examples, and caveats included
2. **Validation Loops**: Executable tests/lints for iterative improvement
3. **Information Dense**: Uses patterns from 7.3-MultiAgentIntro and 7.4-LangGraphAgentWithGuardrail
4. **Progressive Success**: Router → Agents → Workflow → API → Tests
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a research-focused multi-agent system where a lightweight router LLM evaluates incoming requests and routes to specialized Pydantic AI agents (web search via Brave API, email search via Gmail, or document search via RAG). All agents support streaming responses and end the graph execution.

## Why
- **User Experience**: Single interface for multiple research sources (web, email, documents)
- **Cost Optimization**: Lightweight routing model reduces per-request costs
- **Specialization**: Each agent optimized for specific data sources and tasks
- **Streaming Performance**: Real-time response streaming for better UX
- **Research Efficiency**: Users get targeted results without manual tool selection

## What
Create a LangGraph workflow that:
1. Receives user research queries
2. Uses lightweight router to determine appropriate agent
3. Routes to specialized agents: web_search, email_search, rag_search, or fallback
4. Streams responses in real-time using Pydantic AI `.iter()` function
5. Integrates with existing API infrastructure and Supabase backend

### Success Criteria
- [ ] Router correctly identifies agent type 95%+ of the time
- [ ] All agents stream responses successfully with fallback handling
- [ ] Gmail search works with readonly permissions
- [ ] API endpoints integrate seamlessly with new workflow
- [ ] Fallback handles invalid/unclear requests gracefully
- [ ] All validation gates pass (ruff, mypy, pytest)

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/agents/
  why: Pydantic AI agent patterns, streaming with .iter(), result_type usage
  
- url: https://ai.pydantic.dev/graph/
  why: PydanticAI graph integration patterns and async iteration
  
- url: https://langchain-ai.github.io/langgraph/concepts/multi_agent/
  why: LangGraph multi-agent architecture patterns and routing strategies
  
- url: https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/
  why: Agent architectures, router patterns, conditional routing
  
- url: https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list
  why: Gmail API message search parameters and query syntax
  
- file: ../7.3-MultiAgentIntro/agents/research_agent.py
  why: Brave API integration pattern, tool structure, dependencies
  
- file: ../7.3-MultiAgentIntro/agents/email_agent.py
  why: Gmail integration baseline (needs modification for search)
  
- file: ../7.3-MultiAgentIntro/agents/tools.py
  why: Pure tool function patterns, Gmail service setup, error handling
  
- file: ../7.4-LangGraphAgentWithGuardrail/graph/workflow.py
  why: LangGraph node patterns, streaming with writer(), conditional routing
  
- file: ../7.4-LangGraphAgentWithGuardrail/graph/state.py
  why: State management structure for LangGraph workflows
  
- file: ../7.4-LangGraphAgentWithGuardrail/api/endpoints.py
  why: API integration, streaming responses, conversation history
  
- file: ./tools/rag_tools.py
  why: Existing RAG implementation for document search agent
```

### Current Codebase Tree
```bash
7.5-LLMRouting/
├── agents/
│   ├── deps.py              # Agent dependencies (needs router deps)
│   ├── guardrail_agent.py   # DELETE - not needed for routing
│   └── primary_agent.py     # DELETE - not needed for routing
├── api/
│   ├── endpoints.py         # MODIFY - update for routing workflow (shouldn't need to change much)
│   ├── models.py           # MODIFY - add router request/response models
│   └── streaming.py        # KEEP - reuse streaming patterns
├── graph/
│   ├── state.py            # MODIFY - create RouterState
│   └── workflow.py         # COMPLETE OVERHAUL - routing workflow
├── tools/
│   ├── rag_tools.py        # KEEP - use for RAG agent
│   └── validation_tools.py # DELETE - guardrail specific
├── clients.py              # KEEP - LLM client setup
├── .env.example           # MODIFY - document routing config
└── requirements.txt       # KEEP - has all dependencies
```

### Desired Codebase Tree
```bash
7.5-LLMRouting/
├── agents/
│   ├── __init__.py
│   ├── deps.py              # Enhanced with router dependencies
│   ├── router_agent.py      # NEW - lightweight routing logic
│   ├── web_search_agent.py  # NEW - Brave API search
│   ├── email_search_agent.py # NEW - Gmail search (not drafts)
│   ├── rag_search_agent.py  # NEW - document search
│   └── prompts.py           # NEW - centralized system prompts
├── graph/
│   ├── state.py            # RouterState for workflow
│   └── workflow.py         # Router → Agent → END workflow
├── tools/
│   ├── web_tools.py        # NEW - Brave search tools
│   ├── email_tools.py      # NEW - Gmail search tools (modified)
│   └── rag_tools.py        # EXISTING - document search tools
├── tests/
│   ├── test_router_agent.py # NEW - router decision testing
│   ├── test_web_agent.py    # NEW - web search testing
│   ├── test_email_agent.py  # NEW - email search testing
│   ├── test_rag_agent.py    # NEW - RAG search testing
│   └── test_workflow.py     # MODIFIED - routing workflow tests
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Gmail API requires specific scopes for search
# OLD: ["https://www.googleapis.com/auth/gmail.compose", "https://www.googleapis.com/auth/gmail.send"]
# NEW: ["https://www.googleapis.com/auth/gmail.readonly"] for search functionality

# CRITICAL: PydanticAI result_type for structured routing decisions
# Use: result_type=RouterResponse for Pydantic validation
# NOT: Manual JSON parsing or string manipulation

# CRITICAL: LangGraph streaming requires writer() pattern
# Use: writer(chunk) in node functions for real-time streaming  
# NOT: Collecting full response before sending

# CRITICAL: Gmail API message search has rate limits
# Max 250 quota units per user per 100 seconds
# Use maxResults=50 max, implement backoff on 429 errors

# CRITICAL: Brave API requires exact header format
# Use: "X-Subscription-Token" not "Authorization: Bearer"
# Headers: {"X-Subscription-Token": api_key, "Accept": "application/json"}

# CRITICAL: Environment uses venv_linux for Python execution
# Always use: source venv_linux/bin/activate before running tests
# NOT: Global python or other virtual environments
```

## Implementation Blueprint

### Data Models and Structure
```python
# Core routing models for type safety and validation
from typing import Literal, List, Dict, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass 
class RouterResponse:
    """Structured router decision for Pydantic AI result_type"""
    decision: Literal["web_search", "email_search", "rag_search", "fallback"]

class RouterState(TypedDict, total=False):
    """LangGraph state for routing workflow"""
    # Input
    query: str
    session_id: str  
    request_id: str
    
    # Router output
    routing_decision: str
    router_confidence: str
    
    # Agent output  
    final_response: str
    agent_type: str
    streaming_success: bool
    
    # API context
    pydantic_message_history: List[ModelMessage]

class RouterDependencies:
    """Router agent dependencies - minimal for fast decisions"""
    session_id: Optional[str] = None

class AgentDependencies:
    """Shared dependencies for search agents"""
    brave_api_key: str
    gmail_credentials_path: str
    gmail_token_path: str
    session_id: Optional[str] = None
```

### Task Implementation Order

```yaml
Task 1: Setup Router Infrastructure
MODIFY agents/deps.py:
  - ADD create_router_deps() function
  - PATTERN: Minimal dependencies for fast routing decisions
  - PRESERVE existing create_agent_deps() pattern

CREATE agents/prompts.py:
  - CENTRALIZE all system prompts for maintainability
  - PATTERN: Clear, example-rich prompts with explicit instructions
  - INCLUDE router prompt with decision examples

CREATE agents/router_agent.py:
  - MIRROR pattern from: existing agent files
  - USE result_type=RouterResponse for structured output
  - SYSTEM_PROMPT with clear routing criteria and examples

Task 2: Implement Search Agents  
CREATE tools/web_tools.py:
  - COPY from: ../7.3-MultiAgentIntro/agents/tools.py
  - EXTRACT search_web_tool function only
  - PRESERVE exact error handling and rate limiting

CREATE agents/web_search_agent.py:
  - PATTERN: ../7.3-MultiAgentIntro/agents/research_agent.py
  - REMOVE email creation tools, KEEP only web search
  - ADD streaming support with .iter() function

CREATE tools/email_tools.py:
  - MODIFY ../7.3-MultiAgentIntro/agents/tools.py Gmail functions
  - CHANGE scopes to ["gmail.readonly"] 
  - ADD search_emails_tool function with messages.list API
  - PRESERVE authentication and error patterns

CREATE agents/email_search_agent.py:
  - BASE: ../7.3-MultiAgentIntro/agents/email_agent.py
  - REPLACE draft creation with email search functionality
  - ADD search_emails tool with Gmail query syntax
  - FORMAT results as readable email summaries

CREATE agents/rag_search_agent.py:
  - USE existing tools/rag_tools.py functions
  - PATTERN: Other agent files for structure
  - IMPLEMENT streaming for RAG search results

Task 3: Overhaul Workflow
MODIFY graph/state.py:
  - REPLACE AgentState with RouterState
  - REMOVE guardrail-specific fields
  - ADD routing decision and agent type fields
  - PRESERVE API context fields for compatibility

COMPLETE OVERHAUL graph/workflow.py:
  - DELETE all guardrail nodes and logic
  - CREATE router_node with decision logic
  - ADD conditional routing function: route_based_on_decision
  - CREATE agent nodes (web_search_node, email_search_node, rag_search_node)
  - ADD fallback_node for invalid requests
  - PRESERVE streaming patterns with writer()

Task 4: Update API Integration
MODIFY api/models.py:
  - ADD RouterRequest model (if needed beyond existing AgentRequest)
  - UPDATE response models for routing metadata
  - PRESERVE existing Supabase integration models

MODIFY api/endpoints.py:
  - UPDATE import from graph.workflow
  - CHANGE create_api_initial_state to router state
  - PRESERVE authentication, rate limiting, conversation history
  - UPDATE streaming response handler for new workflow

Task 5: Testing Infrastructure
CREATE tests/test_router_agent.py:
  - TEST routing decisions for each agent type
  - MOCK dependencies for isolated testing
  - VERIFY structured RouterResponse output

CREATE tests/test_web_agent.py:
  - TEST Brave API integration
  - MOCK Brave API responses
  - VERIFY streaming functionality

CREATE tests/test_email_agent.py:
  - TEST Gmail search functionality  
  - MOCK Gmail API responses
  - VERIFY readonly scope usage

CREATE tests/test_rag_agent.py:
  - TEST document search functionality
  - USE existing RAG test patterns
  - VERIFY streaming integration

MODIFY tests/test_workflow.py:
  - TEST complete routing workflow
  - VERIFY conditional routing logic
  - TEST fallback scenarios
  - PRESERVE API integration test patterns

Task 6: Environment and Documentation
MODIFY .env.example:
  - DOCUMENT Gmail readonly scope requirement
  - ADD new LLM_CHOICE_SMALL=gpt-4.1-nano
  - ADD routing-specific configuration notes

UPDATE README.md:
  - REPLACE guardrail architecture with routing architecture
  - UPDATE setup instructions for Gmail readonly scopes
  - ADD routing decision examples and agent descriptions
  - PRESERVE existing API and deployment information
```

### Per-Task Pseudocode

```python
# Task 1: Router Agent Implementation
# agents/router_agent.py

ROUTER_SYSTEM_PROMPT = """
You are a routing assistant that determines which specialized agent should handle user requests.

Based on the user's query, choose ONE of these options:
- "web_search": For current events, general information, research topics, news, or anything requiring web search
- "email_search": For finding emails, checking inbox, searching conversations, or email-related queries  
- "rag_search": For questions about documents, files, or knowledge base content
- "fallback": For requests that don't fit the above categories or are unclear

Examples:
- "What's the latest news about AI?" → web_search
- "Find emails from John about the project" → email_search  
- "What does our company policy say about remote work?" → rag_search
- "How are you feeling today?" → fallback

Respond with ONLY the routing decision word.
"""

router_agent = Agent(
    get_llm_model(),  # Uses LLM_CHOICE=gpt-4.1-mini from .env
    result_type=RouterResponse,
    deps_type=RouterDependencies,
    system_prompt=ROUTER_SYSTEM_PROMPT
)

# Task 2: Email Search Tool with Gmail API
# tools/email_tools.py

async def search_emails_tool(
    credentials_path: str,
    token_path: str, 
    query: str,
    max_results: int = 10
) -> Dict[str, Any]:
    """Gmail API email search with readonly permissions"""
    # CRITICAL: Use gmail.readonly scope
    scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    
    try:
        service = _get_gmail_service(credentials_path, token_path, scopes)
        
        # PATTERN: Gmail API messages.list with query
        results = service.users().messages().list(
            userId='me',
            q=query,  # Gmail search syntax: "from:user@example.com subject:project"
            maxResults=min(max_results, 50)  # Gmail API limit
        ).execute()
        
        messages = results.get('messages', [])
        email_results = []
        
        # PATTERN: Extract metadata for each message
        for msg in messages:
            message = service.users().messages().get(
                userId='me', 
                id=msg['id'],
                format='metadata'  # Headers only, not full body
            ).execute()
            
            # PATTERN: Parse headers for display
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            email_results.append({
                "id": msg['id'],
                "subject": subject, 
                "from": sender,
                "date": date,
                "snippet": message.get('snippet', '')
            })
        
        return {"success": True, "results": email_results, "count": len(email_results)}
        
    except Exception as e:
        # PATTERN: Graceful error handling
        return {"success": False, "error": str(e), "results": [], "count": 0}

# Task 3: Workflow Node with Streaming
# graph/workflow.py

async def router_node(state: RouterState, writer) -> dict:
    """Router node that determines which agent to use"""
    try:
        deps = create_router_deps()
        
        # PATTERN: Get structured routing decision
        result = await router_agent.run(state["query"], deps=deps)
        decision = result.data.decision
        
        # PATTERN: Stream routing feedback to user
        writer(f"🔀 Routing to: {decision}\n\n")
        
        return {
            "routing_decision": decision,
            "router_confidence": "high"
        }
        
    except Exception as e:
        # PATTERN: Fallback on router failure
        writer(f"⚠️ Router failed, defaulting to web search\n\n")
        return {
            "routing_decision": "web_search", 
            "router_confidence": "fallback"
        }

async def web_search_node(state: RouterState, writer) -> dict:
    """Web search agent with streaming"""
    try:
        deps = create_agent_deps()
        agent_input = state["query"]
        full_response = ""
        
        try:
            # PATTERN: Streaming with fallback
            async with web_search_agent.run_stream(agent_input, deps=deps) as result:
                async for chunk in result.stream_text(delta=True):
                    writer(chunk)
                    full_response += chunk
                    
        except Exception as stream_error:
            # PATTERN: Non-streaming fallback
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating response...]\n")
            
            run = await web_search_agent.run(agent_input, deps=deps)
            full_response = run.data
            writer(full_response)
        
        return {
            "final_response": full_response,
            "agent_type": "web_search",
            "streaming_success": True
        }
        
    except Exception as e:
        error_msg = f"Web search error: {str(e)}"
        writer(error_msg)
        return {
            "final_response": error_msg,
            "agent_type": "error",
            "streaming_success": False
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
```

### Integration Points
```yaml
GMAIL_API:
  - scope_change: "Replace compose scopes with gmail.readonly"
  - oauth_flow: "Re-authenticate with new scopes (delete token.json)"
  - query_syntax: "Support Gmail search operators: from:, subject:, before:, after:"
  
LANGGRAPH:
  - workflow_structure: "START → router → conditional_routing → agent → END"
  - streaming_mode: "Use stream_mode='custom' for real-time token streaming"
  - state_management: "RouterState replaces AgentState, simplified structure"
  
PYDANTIC_AI:
  - result_types: "Use RouterResponse for structured routing decisions"
  - streaming: "Implement .iter() function for all terminal agents"
  - dependencies: "Minimize router deps, full deps for search agents"
  
API_ENDPOINTS:
  - request_format: "Reuse existing AgentRequest model"
  - response_streaming: "Preserve existing streaming response format"
  - conversation_history: "Maintain Supabase integration for chat history"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Activate correct virtual environment
source venv_linux/bin/activate

# Run these FIRST - fix any errors before proceeding
ruff check agents/ graph/ tools/ --fix  # Auto-fix what's possible
ruff check api/ tests/ --fix
mypy agents/router_agent.py           # Type checking new files
mypy agents/web_search_agent.py
mypy agents/email_search_agent.py
mypy agents/rag_search_agent.py
mypy graph/workflow.py

# Expected: No errors. If errors, READ the error and fix.
# Common issues: Missing imports, incorrect type annotations, unused variables
```

### Level 2: Unit Tests
```python
# CREATE test_router_agent.py with these test cases:
def test_router_web_search_decision():
    """Router correctly identifies web search requests"""
    # Mock dependencies and test routing logic
    
def test_router_email_search_decision():
    """Router correctly identifies email search requests"""
    # Test email-related queries
    
def test_router_fallback_decision():
    """Router uses fallback for unclear requests"""
    # Test ambiguous or invalid queries

def test_gmail_search_readonly_scope():
    """Gmail search uses correct readonly permissions"""
    # Verify scope configuration
    
def test_brave_api_integration():
    """Web search integrates with Brave API"""
    # Mock Brave API responses

def test_streaming_error_handling():
    """Agents handle streaming failures gracefully"""
    # Test fallback to non-streaming mode
```

```bash
# Run and iterate until passing:
source venv_linux/bin/activate
pytest tests/test_router_agent.py -v
pytest tests/test_web_agent.py -v 
pytest tests/test_email_agent.py -v
pytest tests/test_rag_agent.py -v
pytest tests/test_workflow.py -v

# If failing: Read error, understand root cause, fix code, re-run
# Never mock to pass - fix the underlying issue
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check . --fix`
- [ ] No type errors: `mypy agents/ graph/ tools/`
- [ ] Router correctly routes 4/4 test queries
- [ ] Gmail readonly scope works (no compose permission errors)
- [ ] All agents stream responses successfully
- [ ] API integration maintains conversation history
- [ ] Fallback handles edge cases gracefully
- [ ] Documentation updated with routing architecture

---

## Anti-Patterns to Avoid
- ❌ Don't mix Gmail compose and readonly scopes (choose one based on functionality)
- ❌ Don't skip streaming error handling (always provide non-streaming fallback)
- ❌ Don't hardcode agent selections (use conditional routing based on router decisions)
- ❌ Don't ignore rate limiting (Gmail API has strict quotas)
- ❌ Don't break existing API contracts (maintain AgentRequest/AgentResponse compatibility)
- ❌ Don't forget to delete guardrail-specific files (clean up old architecture)

## Confidence Score: 9.5/10

The implementation path is crystal clear with comprehensive context, detailed validation loops, and proven patterns from reference implementations. Success probability is very high due to:
✅ **Complete code patterns from working examples**
✅ **Detailed error handling and fallback strategies**  
✅ **Step-by-step validation with executable commands**
✅ **Specific gotchas and library quirks documented**
✅ **Clear integration points and environment setup**