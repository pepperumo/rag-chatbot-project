name: "RAG Pydantic AI Agent with LangGraph Guardrail System"
description: |

## Purpose
Build a RAG-enabled primary agent with a guardrail system using Pydantic AI and LangGraph for source validation and citation enforcement.

## Core Principles
1. **Two-Agent Architecture**: Primary RAG agent → Guardrail agent → Output
2. **Source Citation Enforcement**: Guardrail validates citations and content relevance
3. **Feedback Loop**: Failed validation returns control to primary agent with context
4. **Modular Design**: Separate concerns between agents, tools, and graph orchestration

---

## Goal
Create a multi-agent system where:
- Primary agent performs RAG queries and cites sources (file IDs)
- Guardrail agent validates citations and content relevance
- System provides feedback loop for correction when validation fails
- All orchestrated through LangGraph with proper state management

## Why
- **Quality Assurance**: Ensures all RAG responses include proper citations
- **Content Validation**: Verifies cited sources actually contain relevant information
- **Reliability**: Prevents hallucinated or incorrect citations
- **Iterative Improvement**: Feedback mechanism allows correction rather than failure

## What
Two Pydantic AI agents orchestrated by LangGraph:
1. **Primary Agent**: RAG queries + initial response with citations
2. **Guardrail Agent**: Citation validation + content relevance checking

### Success Criteria
- [ ] Primary agent performs RAG queries using provided tools
- [ ] Primary agent cites sources (file IDs) in responses
- [ ] Guardrail agent validates citations exist and are relevant
- [ ] Failed validation triggers feedback loop to primary agent
- [ ] LangGraph orchestrates the flow with proper state management
- [ ] System streams output properly
- [ ] All agents follow established patterns from examples

## All Needed Context

### Documentation & References
```yaml
# MUST USE - Core implementation patterns
# Use the RAG tool to get any documentation you need for the implementation patterns.
# Use specific searches for more general ways to implement things for Pydantic AI and LangGraph
# and for specific syntax and ways to implement things.
- MCP: Archon
  Source: Pydantic AI: https://ai.pydantic.dev/
  Source: LangGraph: https://langchain-ai.github.io/langgraph/

# CRITICAL - Existing codebase patterns
- file: examples/agent.py
  why: "Pydantic AI agent setup, dependencies, tool registration"
  pattern: "Agent dependencies, tool decorators, RunContext usage"
  
- file: examples/tools.py
  why: "RAG tool implementations: retrieve_relevant_documents_tool, get_document_content_tool"
  pattern: "Tool function signatures, error handling, database queries"
  
- file: examples/agent_api.py
  why: "Streaming response patterns, dependency injection"
  pattern: "Agent.iter usage, streaming responses, error handling"
  
- file: examples/clients.py
  why: "Client setup for Supabase, OpenAI embedding client"
  pattern: "Environment variable usage, client initialization"
  
- file: examples/archon_graph.py
  why: "LangGraph multi-agent patterns, state management"
  pattern: "StateGraph, nodes, edges, message passing, Command usage"
```

### Current Codebase Structure
```bash
/mnt/c/Users/colem/OpenSource/Archon/AgentGuardrailWithLangGraph/
├── examples/
│   ├── agent.py                 # Primary agent reference
│   ├── tools.py                 # RAG tools reference
│   ├── agent_api.py             # Streaming API reference
│   ├── clients.py               # Client setup reference
│   └── archon_graph.py          # LangGraph patterns
├── cli.py                       # CLI interface
├── requirements.txt             # Dependencies
├── .env.example                 # Environment config
└── PRPs/
    └── rag-guardrail-agents.md  # This PRP
```

### Target Codebase Structure
```bash
/mnt/c/Users/colem/OpenSource/Archon/AgentGuardrailWithLangGraph/
├── agents/
│   ├── __init__.py
│   ├── primary_agent.py         # RAG agent with citation requirements
│   ├── guardrail_agent.py       # Citation validation agent
│   └── deps.py                  # Agent dependencies
├── tools/
│   ├── __init__.py
│   ├── rag_tools.py             # RAG query tools
│   └── validation_tools.py      # Citation validation tools
├── graph/
│   ├── __init__.py
│   ├── workflow.py              # LangGraph orchestration
│   └── state.py                 # Graph state management
├── main.py                      # Main entry point
├── tests/
│   ├── test_primary_agent.py
│   ├── test_guardrail_agent.py
│   └── test_workflow.py
└── README.md                    # Setup instructions
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Pydantic AI requires specific patterns
# - Agent dependencies must be dataclasses with proper typing
# - Tools must use RunContext[DepsType] pattern
# - System prompts should instruct citation behavior explicitly

# CRITICAL: LangGraph state management
# - State must be TypedDict or compatible
# - Command API for node transitions: return Command(goto="next_node", update={...})
# - Message history requires proper serialization for agent handoff

# CRITICAL: RAG tool patterns from examples/tools.py
# - retrieve_relevant_documents_tool returns formatted chunks with file_id
# - get_document_content_tool retrieves full content by document_id
# - Both tools require Supabase client and proper error handling

# CRITICAL: Google Drive URL extraction
# - Regex pattern: r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)/'
# - Extract file IDs from group(1) of the regex matches
# - Handle multiple URLs in a single response
# - Validate URLs are properly formatted before processing

# CRITICAL: Environment setup
# - Use python_dotenv and load_dotenv() pattern from examples
# - Virtual environment: venv_linux for Python execution
# - Client setup follows examples/clients.py pattern
# - .env.example contains all required environment variables
```

## Implementation Blueprint

### Data Models and State
```python
# Graph state for agent coordination
from typing import TypedDict, List, Optional
from dataclasses import dataclass

class AgentState(TypedDict):
    query: str                          # Original user query
    primary_response: str               # Primary agent response
    google_drive_urls: List[str]        # Extracted Google Drive URLs
    file_ids: List[str]                 # Extracted file IDs from URLs
    validation_result: Optional[str]    # Guardrail validation outcome
    feedback: Optional[str]             # Feedback for primary agent
    iteration_count: int                # Prevent infinite loops
    final_output: str                   # Validated final response
    message_history: List[bytes]        # Message history for agent handoff

# Agent dependencies with optional feedback
@dataclass
class AgentDeps:
    supabase: Client
    embedding_client: AsyncOpenAI
    http_client: AsyncClient
    feedback: Optional[str] = None      # Optional feedback from guardrail
```

### Implementation Tasks (Sequential Order)

```yaml
Task 1: Setup Project Structure
CREATE agents/__init__.py, tools/__init__.py, graph/__init__.py:
  - Empty __init__.py files for Python packages
  - Follow existing project conventions

CREATE agents/deps.py:
  - MIRROR pattern from: examples/clients.py
  - MODIFY to include only RAG-related dependencies
  - PRESERVE client setup patterns (Supabase, OpenAI)

Task 2: Implement RAG Tools
CREATE tools/rag_tools.py:
  - COPY patterns from: examples/tools.py
  - EXTRACT: retrieve_relevant_documents_tool, get_document_content_tool
  - MODIFY to ensure consistent return formats with file_id metadata
  - PRESERVE error handling and database query patterns

CREATE tools/validation_tools.py:
  - NEW function: extract_google_drive_urls(response: str) -> List[str]
    - USE regex pattern: r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)/'
    - RETURN list of extracted file IDs from URLs
  - NEW function: validate_citation_relevance(file_id: str, query: str, response: str) -> bool
    - USE get_document_content_tool internally for content retrieval
    - RETURN boolean indicating if content is relevant
  - RETURN structured validation results

Task 3: Implement Primary Agent
CREATE agents/primary_agent.py:
  - MIRROR pattern from: examples/agent.py
  - MODIFY system prompt to REQUIRE citation format: "Source: [file_id]"
  - REGISTER tools: retrieve_relevant_documents, list_documents, get_document_content
  - PRESERVE dependency injection pattern with RunContext
  - CRITICAL: System prompt must explicitly instruct citation behavior
  - CRITICAL: Add @agent.system_prompt decorator to handle optional feedback
  - CRITICAL: When feedback exists, modify behavior to address the feedback

Task 4: Implement Guardrail Agent
CREATE agents/guardrail_agent.py:
  - MIRROR agent setup pattern from: examples/agent.py
  - REGISTER tools: get_document_content, validation functions
  - SYSTEM PROMPT: "Validate citations and content relevance"
  - RETURN structured validation with feedback

Task 5: Create Graph State Management
CREATE graph/state.py:
  - DEFINE AgentState TypedDict with all required fields
  - INCLUDE message serialization helpers for agent handoff
  - PATTERN: Follow examples/archon_graph.py state management

Task 6: Implement LangGraph Workflow
CREATE graph/workflow.py:
  - MIRROR pattern from: examples/archon_graph.py
  - NODES: primary_agent_node, guardrail_agent_node
  - EDGES: primary -> guardrail -> (END | primary with feedback)
  - IMPLEMENT streaming with writer parameter in each node
  - IMPLEMENT conditional routing based on validation results
  - PRESERVE message history between agent calls
  - CRITICAL: Use agent.iter() for streaming, not agent.run()
  - CRITICAL: Stream validation feedback ("good response" / "bad response")
  - CRITICAL: Loop back to primary_agent_node with feedback in state
  - CRITICAL: Pass feedback as dependency to primary agent on retry

Task 7: Create Main Entry Point
CREATE main.py:
  - MIRROR pattern from: examples/agent_api.py streaming approach
  - INTEGRATE graph workflow with streaming output
  - PRESERVE environment variable setup
  - IMPLEMENT proper error handling and logging

Task 8: Add Testing Framework
CREATE tests/test_primary_agent.py:
  - MOCK all dependencies (Supabase, OpenAI, AsyncClient)
  - TEST agent initialization and tool registration
  - TEST RAG query responses include Google Drive URLs
  - TEST error handling for missing documents
  - TEST feedback integration through optional dependency

CREATE tests/test_guardrail_agent.py:
  - MOCK all dependencies and tool responses
  - TEST Google Drive URL extraction using regex
  - TEST content relevance validation
  - TEST feedback generation for invalid citations

CREATE tests/test_workflow.py:
  - MOCK all external dependencies
  - TEST complete workflow execution
  - TEST feedback loop functionality
  - TEST streaming output behavior with mixed validation messages

Task 9: Documentation and Setup
CREATE README.md:
  - INCLUDE environment setup instructions
  - DOCUMENT required environment variables
  - PROVIDE usage examples and API documentation
  - EXPLAIN agent architecture and workflow
```

### Critical Implementation Details

#### Primary Agent System Prompt
```python
PRIMARY_AGENT_SYSTEM_PROMPT = """
You are a RAG-enabled research assistant. When answering questions:

1. ALWAYS search for relevant information using your tools
2. ALWAYS cite your sources as Google Drive document URLs in this exact format: 
   "https://docs.google.com/document/d/[file_id]/"
3. Multiple sources should be cited as separate URLs
4. Only use information from the documents you retrieve
5. If you cannot find relevant information, say so explicitly

Example response format:
"Based on the research data, the quarterly revenue increased by 15%. Source: https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/

For additional context, market trends show growth. Source: https://docs.google.com/document/d/9i8h7g6f5e4d3c2b1a0z/"
"""
```

#### Guardrail Agent System Prompt
```python
GUARDRAIL_SYSTEM_PROMPT = """
You are a citation validation specialist. Your job is to:

1. Extract all Google Drive document URLs from the response (format: https://docs.google.com/document/d/[file_id]/)
2. Verify each cited source contains relevant information for the query
3. Return structured validation results
4. Provide specific feedback if validation fails

Validation criteria:
- All citations must be valid Google Drive document URLs
- Cited content must be relevant to the original query
- No hallucinated or fake citations allowed
- Return "VALID" if all citations check out, otherwise provide specific feedback
"""
```

#### Streaming Implementation Pattern
```python
from pydantic_ai.messages import PartStartEvent, PartDeltaEvent, TextPartDelta
from pydantic_ai import Agent, RunContext
import json

async def primary_agent_node(state: AgentState, writer) -> dict:
    """Primary agent node - streams RAG response with citations"""
    # Include feedback in dependencies if it exists
    deps = AgentDeps(
        supabase=supabase,
        embedding_client=embedding_client,
        http_client=http_client,
        feedback=state.get("feedback")  # Pass feedback as optional dependency
    )
    full_response = ""
    
    # Stream primary agent response
    async with primary_agent.iter(
        state["query"], 
        deps=deps,
        message_history=state.get("message_history", [])
    ) as run:
        async for node in run:
            if Agent.is_model_request_node(node):
                async with node.stream(run.ctx) as request_stream:
                    async for event in request_stream:
                        if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                            writer(json.dumps({"text": event.part.content}).encode('utf-8') + b'\n')
                            full_response += event.part.content
                        elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                            delta = event.delta.content_delta
                            writer(json.dumps({"text": full_response}).encode('utf-8') + b'\n')
                            full_response += delta
    
    return {
        "primary_response": full_response,
        "message_history": run.result.new_messages_json()
    }

async def guardrail_agent_node(state: AgentState, writer) -> dict:
    """Guardrail validation node - validates and streams feedback"""
    deps = AgentDeps(
        supabase=supabase,
        embedding_client=embedding_client,
        http_client=http_client
    )
    
    validation_query = f"""
    Validate this response and its citations:
    Query: {state['query']}
    Response: {state['primary_response']}
    """
    
    # Run guardrail validation (non-streaming for quick validation)
    result = await guardrail_agent.run(validation_query, deps=deps)
    
    # Extract Google Drive URLs using regex
    google_drive_urls = extract_google_drive_urls(state["primary_response"])
    
    # Stream validation result
    if "VALID" in result.data:
        writer(json.dumps({"text": "✅ This was a good response - citations are valid"}).encode('utf-8') + b'\n')
        return {
            "validation_result": "valid",
            "google_drive_urls": google_drive_urls,
            "final_output": state["primary_response"]
        }
    else:
        writer(json.dumps({"text": "❌ This was a bad response - citations need correction"}).encode('utf-8') + b'\n')
        return {
            "validation_result": "invalid",
            "google_drive_urls": google_drive_urls,
            "feedback": result.data,
            "iteration_count": state.get("iteration_count", 0) + 1
        }

# Primary agent system prompt decorator to handle feedback
@primary_agent.system_prompt
async def add_feedback_to_prompt(ctx: RunContext[AgentDeps]) -> str:
    """Add feedback to system prompt if provided"""
    if ctx.deps.feedback:
        return f"""
        FEEDBACK FROM VALIDATION:
        {ctx.deps.feedback}
        
        Please address this feedback and provide a corrected response with proper citations.
        """
    return ""

# Regex utility function for URL extraction
import re

def extract_google_drive_urls(text: str) -> List[str]:
    """Extract Google Drive document URLs from text using regex"""
    pattern = r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)/'
    matches = re.findall(pattern, text)
    return [f"https://docs.google.com/document/d/{file_id}/" for file_id in matches]

def extract_file_ids_from_urls(urls: List[str]) -> List[str]:
    """Extract file IDs from Google Drive URLs"""
    pattern = r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)/'
    file_ids = []
    for url in urls:
        match = re.search(pattern, url)
        if match:
            file_ids.append(match.group(1))
    return file_ids
```

### Integration Points
```yaml
ENVIRONMENT:
  - copy from: .env.example
  - required: LLM_API_KEY, LLM_MODEL, LLM_BASE_URL
  - optional: EMBEDDING_MODEL_CHOICE, EMBEDDING_BASE_URL

DATABASE:
  - use existing: Supabase connection pattern
  - tables: documents, document_metadata (from examples)
  - functions: match_documents, execute_custom_sql

CLIENTS:
  - pattern: examples/clients.py
  - required: AsyncOpenAI, Supabase Client, AsyncClient
  - initialization: get_agent_clients() function
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
source venv_linux/bin/activate
ruff check agents/ tools/ graph/ main.py --fix
mypy agents/ tools/ graph/ main.py

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```bash
# Create and run tests for each component
source venv_linux/bin/activate
pytest tests/test_primary_agent.py -v
pytest tests/test_guardrail_agent.py -v
pytest tests/test_workflow.py -v

# Expected: All tests pass. Fix any failures before proceeding.
```

### Level 3: Integration Test
```bash
# Test complete workflow
source venv_linux/bin/activate
python main.py

# Test with sample query:
# "What are the key findings about AI safety in the research papers?"
# Expected: Response with proper citations validated by guardrail
```

### Level 4: Streaming Test
```bash
# Test streaming functionality
curl -X POST http://localhost:8000/api/rag-agents \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize the latest AI developments", "stream": true}'

# Expected: Streaming JSON chunks with incremental response
```

## Final Validation Checklist
- [ ] Primary agent performs RAG queries correctly
- [ ] Primary agent includes citations in responses
- [ ] Guardrail agent validates citations accurately
- [ ] Invalid citations trigger feedback loop
- [ ] Feedback loop prevents infinite iterations (max 3)
- [ ] LangGraph orchestrates agents properly
- [ ] Streaming output works correctly
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check`
- [ ] No type errors: `mypy`
- [ ] README.md includes setup instructions
- [ ] Environment variables documented

---

## Anti-Patterns to Avoid
- ❌ Don't skip citation validation - it's the core requirement
- ❌ Don't create infinite feedback loops - implement max iterations
- ❌ Don't hardcode file IDs - use dynamic RAG queries
- ❌ Don't ignore streaming patterns - follow examples/agent_api.py
- ❌ Don't skip proper error handling in agents and tools
- ❌ Don't modify existing examples - create new files
- ❌ Don't skip environment variable setup - document clearly

## Implementation Confidence Score: 8/10

**High confidence factors:**
- Clear reference implementations in examples/
- Well-established patterns for both Pydantic AI and LangGraph
- Specific tool implementations already exist
- Streaming patterns well-documented in examples

**Risk factors:**
- Agent coordination complexity (mitigated by following archon_graph.py patterns)
- Citation parsing reliability (mitigated by structured prompts)
- Feedback loop termination (mitigated by iteration counting)

**Success likelihood:** High - all necessary patterns exist in codebase, clear requirements, and validation gates ensure quality.