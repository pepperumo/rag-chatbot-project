name: "LangGraph Supervisor Pattern Agent Workflow PRP"
description: |

## Goal
Build a LangGraph workflow with 4 agents using Pydantic AI, demonstrating the evolution from sub-agents as tools to shared state management through a supervisor pattern. The supervisor agent intelligently delegates tasks between sub-agents using structured output and synthesizes responses for comprehensive final answers.

## Why
- **Architectural Evolution**: Demonstrates significant advancement from traditional sub-agents as tools approach (7.3-MultiAgentIntro) to sophisticated supervisor pattern with shared state management
- **Scalable Multi-Agent Coordination**: Enables much more scalable coordination where agents communicate through concise summaries rather than overwhelming verbose outputs  
- **Intelligent Workflow Management**: Supervisor doesn't just route mechanically but demonstrates intelligent delegation, optimal sequencing, and synthesis capabilities
- **Context Overflow Prevention**: LangGraph shared state prevents context overflow issues common in direct agent-to-agent communication
- **Real-world Task Management**: Integrates with Asana API for actual task management capabilities alongside research and email drafting

## What
A sophisticated LangGraph workflow with 4 Pydantic AI agents:

### Supervisor Agent
- Central coordinator receiving user requests and intelligently delegating tasks
- Uses **structured output with streaming** for real-time user feedback while making delegation decisions
- Makes informed decisions about which agent(s) to invoke based on request content and current state
- Synthesizes responses from sub-agents to provide comprehensive final answers
- Returns control after each sub-agent execution to either delegate to another agent, invoke multiple agents in sequence, or provide final response
- **Maximum 20 iterations** to prevent infinite loops

### Sub-Agents
1. **Web Research Agent** (Brave API): Performs targeted web research, updates shared state with research summaries
2. **Task Management Agent** (Asana API): Handles project and task management operations using Asana Python SDK, updates shared state with task summaries  
3. **Email Drafting Agent** (Gmail API): Creates and manages email drafts, updates shared state with email status and draft summaries

### Key Innovation - Shared State Management
- **Central Knowledge Repository**: Shared LangGraph state acts as central repository all agents can read from and contribute to
- **Concise Communication**: Sub-agents update state with summaries rather than full outputs, enabling efficient communication
- **Context-Aware Workflows**: Agents can build upon each other's work through shared state rather than operating in isolation
- **Intelligent Synthesis**: Supervisor synthesizes information from multiple sub-agents when needed for complex requests

### Success Criteria
- [ ] **Supervisor Intelligent Orchestration**: Supervisor agent demonstrates sophisticated intelligence by dynamically weaving in and out of sub-agents based on context - NOT sequential A→B→C execution, but intelligent interleaving like Research→Tasks→Research→Email→Tasks→Research (just as an example) based on evolving understanding. System prompt for the supervisor agent will be really important for this
- [ ] **Dynamic Delegation Patterns**: Each user request produces different agent execution patterns - some requests may use Research 3x, Tasks 1x, Email 2x; others may skip Email entirely or cycle between Research and Tasks multiple times before final response
- [ ] Supervisor agent successfully streams responses while making delegation decisions using structured output
- [ ] All 4 agents (supervisor + 3 sub-agents) integrate seamlessly with LangGraph workflow
- [ ] Simplified shared state management with single append-only list enables flexible agent collaboration  
- [ ] Asana API integration supports full project management: create/list projects, create/update/list tasks within projects
- [ ] Web research and email drafting maintain existing functionality from reference implementations
- [ ] Maximum 20 iteration limit prevents infinite loops while allowing complex multi-step workflows
- [ ] API endpoint maintains compatibility with existing frontend/client integrations

## Intelligent Orchestration Philosophy

**Core Ethos**: The supervisor agent represents the pinnacle of multi-agent intelligence - demonstrating sophisticated reasoning that adapts its delegation strategy based on evolving context and information needs.

**Dynamic Workflow Examples**:
- **Complex Research Project**: Research competitor → Create project in Asana → Research specific metrics → Create detailed tasks → Research pricing models → Update tasks with findings → Draft outreach email
- **Quick Task Management**: Create Asana project → Research best practices → Update project description → Create tasks based on research
- **Information Synthesis**: Research topic A → Research related topic B → Synthesize findings without any task creation or email drafting

**Intelligence Indicators**:
- **Contextual Awareness**: Supervisor builds understanding progressively, letting research inform task creation which informs further research
- **Adaptive Sequencing**: No two requests follow identical patterns - delegation order emerges from content analysis
- **Selective Usage**: Some agents may not be used at all if not relevant to the specific request
- **Iterative Refinement**: Agents may be called multiple times as understanding deepens

This approach showcases true AI orchestration intelligence rather than rigid workflow automation.

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://developers.asana.com/docs/python
  why: Official Asana Python SDK documentation and authentication patterns
  
- url: https://ai.pydantic.dev/output/
  why: Pydantic AI structured output and streaming capabilities - critical for supervisor delegation
  
- url: https://ai.pydantic.dev/examples/stream-whales/
  why: Working example of Pydantic AI structured output streaming with exact PartStartEvent/PartDeltaEvent patterns
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.6-SequentialAgents/graph/workflow.py
  why: LangGraph workflow patterns, state management, and streaming implementation
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.6-SequentialAgents/graph/state.py
  why: State structure patterns for LangGraph workflows
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.3-MultiAgentIntro/agents/email_agent.py
  why: Gmail API integration patterns and email agent implementation
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.3-MultiAgentIntro/agents/research_agent.py
  why: Brave API integration patterns and research agent implementation
  
- file: /mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.6-SequentialAgents/api/endpoints.py
  why: FastAPI endpoint patterns for LangGraph integration and streaming responses
```

### Current Codebase Tree
```bash
/mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.7-SupervisorAgent/
├── CLAUDE.md                    # Project guidelines and conventions
├── README.md                    # Current sequential agent docs (needs major overhaul)
├── requirements.txt             # Missing asana dependency - needs addition
├── .env.example                 # Environment variables template
├── clients.py                   # LLM client configuration
├── langgraph.json              # LangGraph configuration
├── streamlit_app.py            # Streamlit interface
├── agents/
│   ├── deps.py                 # Dependency injection patterns
│   ├── prompts.py              # System prompts (needs supervisor prompts)
│   ├── email_draft_agent.py    # Current email agent (needs integration)
│   ├── research_agent.py       # Current research agent (needs integration)
│   ├── enrichment_agent.py     # To be replaced with task management agent
│   ├── guardrail_agent.py      # To be replaced with supervisor agent
│   └── fallback_agent.py       # Keep for error handling
├── tools/
│   ├── brave_tools.py          # Brave API integration (reuse)
│   ├── gmail_tools.py          # Gmail API integration (reuse)
│   └── asana_tools.py          # NEW - Asana API integration needed
├── graph/
│   ├── state.py                # State definition (needs supervisor state)
│   └── workflow.py             # Workflow orchestration (major overhaul needed)
├── api/
│   ├── endpoints.py            # FastAPI endpoints (minor changes)
│   ├── models.py               # Request/response models (needs supervisor models)
│   ├── streaming.py            # Streaming utilities (reuse)
│   └── db_utils.py             # Database utilities (reuse)
└── tests/
    ├── test_supervisor_agent.py      # NEW - Supervisor agent tests needed
    ├── test_task_management_agent.py # NEW - Task management agent tests needed
    ├── test_supervisor_workflow.py   # NEW - Supervisor workflow tests needed
    └── test_asana_tools.py           # NEW - Asana tools tests needed
```

### Desired Codebase Tree
```bash
/mnt/c/Users/colem/dynamous/7_Agent_Architecture/7.7-SupervisorAgent/
├── agents/
│   ├── supervisor_agent.py     # NEW - Central coordinator with structured output streaming
│   ├── web_research_agent.py   # MODIFIED - From research_agent.py, state-focused
│   ├── task_management_agent.py # NEW - Asana API integration for task management
│   ├── email_draft_agent.py    # MODIFIED - State-focused version
│   └── fallback_agent.py       # MODIFIED - Error handling and simple queries
├── tools/
│   └── asana_tools.py          # NEW - Asana SDK integration functions
├── graph/
│   ├── state.py                # MODIFIED - SupervisorAgentState with iteration tracking
│   └── workflow.py             # MAJOR OVERHAUL - Supervisor pattern workflow
├── api/
│   └── models.py               # MODIFIED - Add supervisor-specific request/response models
└── tests/
    ├── test_supervisor_agent.py      # NEW - Structured output and delegation tests
    ├── test_task_management_agent.py # NEW - Asana integration tests  
    ├── test_supervisor_workflow.py   # NEW - End-to-end workflow tests
    └── test_asana_tools.py           # NEW - Asana API function tests
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Pydantic AI structured output requires specific model structure
# The supervisor agent needs TypedDict/BaseModel with optional fields for streaming
# Example: messages field must be Optional[str] for conditional streaming

# CRITICAL: Pydantic AI structured output streaming complexity risk mitigation
# ALWAYS test streaming in isolation BEFORE workflow integration
# Use fallback strategy: attempt streaming, fall back to non-streaming on failure
# Stream everything, extract structured fields in post-processing (simpler than detection)

# STREAMING FALLBACK PATTERN:
try:
    # Attempt streaming structured output
    async with supervisor_agent.iter(query, deps=deps) as run:
        # Streaming logic here
        pass
except Exception as stream_error:
    # Fallback to non-streaming structured output
    result = await supervisor_agent.run(query, deps=deps)
    # Handle decision_data = result.data without streaming

# CRITICAL: Asana Python SDK requires personal access token authentication
# Use configuration = asana.Configuration(); configuration.access_token = token
# SDK uses ApiClient(configuration) pattern for all operations

# CRITICAL: LangGraph state management with shared state
# All agents must update state keys, not return entire new state
# Use return {"key": value} pattern, not return new_state_dict

# CRITICAL: Maximum iteration tracking in LangGraph
# Must track iteration_count in state and enforce 20-iteration limit
# Prevents infinite delegation loops in supervisor pattern

# CRITICAL: Dependencies injection patterns
# Follow existing deps.py patterns for consistent dependency management
# Each agent needs its own dependencies class with required API keys/config
```

## Implementation Blueprint

### Data Models and Structure

```python
# graph/state.py - SupervisorAgentState
class SupervisorAgentState(TypedDict, total=False):
    # Input and session management
    query: str
    session_id: str  
    request_id: str
    iteration_count: int  # Track delegation iterations
    
    # Supervisor coordination
    supervisor_reasoning: str  # Last supervisor decision reasoning
    shared_state: List[str]  # Append-only list where all sub-agents add summaries
    
    # Final response and workflow control
    final_response: str
    workflow_complete: bool
    agent_type: str  # Final responding agent
    
    # Message history management (only supervisor updates when providing final response)
    pydantic_message_history: List[ModelMessage]
    message_history: List[bytes]
    
    # API context
    conversation_title: Optional[str]
    is_new_conversation: Optional[bool]

# agents/supervisor_agent.py - Structured Output Model
class SupervisorDecision(BaseModel):
    """Structured output for supervisor agent decisions with streaming support"""
    messages: Optional[str] = Field(
        None, 
        description="Streamed response to user - only populate if providing final response"
    )
    delegate_to: Optional[str] = Field(
        None,
        description="Agent to delegate to next: 'web_research', 'task_management', 'email_draft', or None for final response"
    )
    reasoning: str = Field(
        description="Reasoning for this decision - why delegating or providing final response"
    )
    final_response: bool = Field(
        default=False,
        description="True if this is the final response to user, False if delegating"
    )
```

### Tasks to Complete (In Order)

```yaml
Task 0: Streaming Foundation Validation (CRITICAL FIRST STEP)
CREATE test_streaming_poc.py:
  - IMPLEMENT minimal supervisor agent with SupervisorDecision output_type
  - TEST structured output streaming in isolation from workflow complexity
  - VALIDATE PartStartEvent/PartDeltaEvent handling works correctly
  - INCLUDE fallback to non-streaming structured output if streaming fails
  - PATTERN: Based on https://ai.pydantic.dev/examples/stream-whales/ streaming example
  - ONLY proceed to Task 1 if streaming validation passes completely

Task 1: Set up Asana Integration Foundation
CREATE tools/asana_tools.py:
  - IMPLEMENT async create_project_tool function with Asana SDK
  - IMPLEMENT async list_projects_tool function
  - IMPLEMENT async get_project_details_tool function  
  - IMPLEMENT async create_task_tool function with project assignment
  - IMPLEMENT async update_task_tool function  
  - IMPLEMENT async list_tasks_tool function (with project filtering)
  - IMPLEMENT async get_workspace_info function
  - PATTERN: Follow brave_tools.py error handling and async patterns
  - INCLUDE comprehensive error handling for API failures

MODIFY requirements.txt:
  - ADD asana>=3.2.0 to dependencies list

Task 2: Create Task Management Agent (Distinct Pydantic AI Agent)
CREATE agents/task_management_agent.py:
  - MIRROR pattern from: 7.3-MultiAgentIntro/agents/email_agent.py
  - IMPLEMENT TaskManagementAgentDependencies dataclass
  - CREATE distinct Pydantic AI agent with Asana tools for project and task CRUD operations
  - FOCUS on appending to shared_state list in SupervisorAgentState
  - INCLUDE comprehensive logging and error handling
  - TOOLS: Project creation/listing, task creation/updating/listing within projects

Task 3: Create Web Research Agent (Distinct Pydantic AI Agent)
CREATE agents/web_research_agent.py:
  - MIRROR pattern from: 7.3-MultiAgentIntro/agents/research_agent.py
  - IMPLEMENT WebResearchAgentDependencies dataclass
  - CREATE distinct Pydantic AI agent with Brave Search tools
  - FOCUS on appending research summaries to shared_state list
  - REMOVE email creation functionality (supervisor handles delegation)
  - PRESERVE Brave API integration patterns from existing tools/brave_tools.py

Task 4: Create Email Draft Agent (Distinct Pydantic AI Agent)
CREATE agents/email_draft_agent.py:
  - MIRROR pattern from: 7.3-MultiAgentIntro/agents/email_agent.py
  - IMPLEMENT EmailDraftAgentDependencies dataclass
  - CREATE distinct Pydantic AI agent with Gmail tools
  - FOCUS on appending email summaries to shared_state list
  - PRESERVE Gmail API integration patterns from existing tools/gmail_tools.py
  - UPDATE to work with simplified SupervisorAgentState

Task 5: Create Supervisor Agent with Structured Output
CREATE agents/supervisor_agent.py:
  - IMPLEMENT SupervisorAgentDependencies with session management
  - CREATE agent with SupervisorDecision output_type for structured streaming
  - IMPLEMENT intelligent delegation through system prompt and structured output (no separate logic functions)
  - INCLUDE iteration tracking and 20-iteration limit enforcement in system prompt
  - FOCUS on sophisticated reasoning that adapts delegation based on shared_state content
  - PATTERN: Use Pydantic AI structured output streaming from ai.pydantic.dev/output/

Task 6: Update State Management
MODIFY graph/state.py:
  - REPLACE SequentialAgentState with SupervisorAgentState
  - IMPLEMENT simplified shared_state list for all agent coordination
  - PRESERVE message history management patterns
  - REMOVE complex state tracking fields

Task 7: Overhaul Workflow Orchestration
MODIFY graph/workflow.py:
  - REPLACE sequential workflow with supervisor pattern
  - IMPLEMENT supervisor_node with structured output streaming
  - IMPLEMENT web_research_node, task_management_node, email_draft_node  
  - ADD conditional routing based on SupervisorDecision.delegate_to
  - INCLUDE iteration limit enforcement
  - PRESERVE streaming patterns from 7.6-SequentialAgents
  - FOCUS on simple delegation routing, not complex logic

Task 8: Update API Models and Endpoints
MODIFY api/models.py:
  - ADD SupervisorRequest and SupervisorResponse models
  - PRESERVE existing API compatibility for frontend integration
  - ADD supervisor-specific metadata fields

MODIFY api/endpoints.py:
  - UPDATE endpoint to use supervisor workflow instead of sequential
  - PRESERVE authentication, streaming, and response patterns
  - MAINTAIN backward compatibility with existing API clients

Task 9: Create Comprehensive Test Suite
CREATE tests/test_supervisor_agent.py:
  - TEST structured output streaming functionality
  - TEST delegation decision making with various input types
  - TEST iteration limit enforcement
  - INCLUDE mock dependencies for isolated testing

CREATE tests/test_task_management_agent.py:
  - TEST Asana API integration with mocked responses
  - TEST project and task CRUD operations
  - TEST error handling for API failures

CREATE tests/test_supervisor_workflow.py:
  - TEST end-to-end supervisor pattern workflow
  - TEST multi-agent coordination through shared state
  - TEST complex scenarios requiring multiple agent delegations
  - INCLUDE integration tests with real API dependencies

CREATE tests/test_asana_tools.py:
  - TEST all Asana tool functions with mocked API responses
  - TEST authentication and configuration patterns
  - TEST error handling and edge cases

Task 10: Update Documentation and Examples
MODIFY README.md:
  - COMPLETE overhaul for supervisor pattern architecture
  - UPDATE installation instructions with Asana dependency
  - ADD supervisor pattern workflow examples and use cases
  - UPDATE API documentation and example requests
  - ADD troubleshooting section for multi-agent coordination

MODIFY .env.example:
  - ADD ASANA_API_KEY configuration
  - ADD ASANA_WORKSPACE_ID configuration
  - UPDATE comments and examples for supervisor pattern
```

### Supervisor Agent Pseudocode

```python
# agents/supervisor_agent.py - Simplified intelligent delegation
SUPERVISOR_SYSTEM_PROMPT = """
You are an intelligent supervisor agent coordinating web research, task management, and email drafting agents.

Your job is to analyze requests and shared state, then either:
1. Delegate to a sub-agent: web_research, task_management, or email_draft
2. Provide final response by synthesizing information from shared_state

Key Intelligence Patterns:
- Research may inform task creation which may require more research
- Tasks may need research before email drafting  
- Some requests don't need all agents - be selective
- Agents can be called multiple times as understanding evolves
- Maximum 20 iterations to prevent infinite loops

Current shared state summary: {shared_state}
Current iteration: {iteration_count}/20

Analyze the request and shared state to make your next intelligent decision.
"""

# PATTERN: Supervisor node with streaming fallback strategy
async def supervisor_node(state: SupervisorAgentState, writer) -> dict:
    """
    CRITICAL: Stream messages field when providing final response, with fallback
    """
    try:
        deps = create_supervisor_deps(session_id=state.get("session_id"))
        
        # PATTERN: Pass current state context to supervisor agent
        enhanced_query = f"""
        User Request: {state["query"]}
        Shared State: {state.get("shared_state", [])}
        Iteration: {state.get("iteration_count", 0)}/20
        """
        
        full_response = ""
        decision_data = None
        
        try:
            # ATTEMPT: Streaming structured output (preferred)
            async with supervisor_agent.iter(enhanced_query, deps=deps) as run:
                async for node in run:
                    if Agent.is_model_request_node(node):
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                # SIMPLIFIED: Stream everything, extract structured fields after
                                if isinstance(event, PartStartEvent):
                                    content = event.part.content
                                    writer(content)
                                    full_response += content
                                elif isinstance(event, PartDeltaEvent):
                                    delta = event.delta.content_delta
                                    writer(delta)
                                    full_response += delta
            
            # Extract structured decision from streaming result
            decision_data = run.result.data
            
        except Exception as stream_error:
            # FALLBACK: Non-streaming structured output
            print(f"Streaming failed, using fallback: {stream_error}")
            writer("\n[Streaming unavailable, generating decision...]\n")
            
            result = await supervisor_agent.run(enhanced_query, deps=deps)
            decision_data = result.data
            
            # Use only the messages field if present for final response
            if decision_data.messages:
                writer(decision_data.messages)
                full_response = decision_data.messages
        
        # PATTERN: Use structured decision for workflow control
        final_response = decision_data.messages if decision_data.final_response else ""
        
        return {
            "supervisor_reasoning": decision_data.reasoning,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "final_response": final_response,
            "workflow_complete": decision_data.final_response,
            "delegate_to": decision_data.delegate_to,
            "agent_type": "supervisor"
        }
        
    except Exception as e:
        error_msg = f"Supervisor error: {str(e)}"
        writer(error_msg)
        return {
            "final_response": error_msg,
            "workflow_complete": True,
            "agent_type": "error"
        }

# PATTERN: Sub-agent nodes append to shared_state
async def web_research_node(state: SupervisorAgentState, writer) -> dict:
    # Execute web research agent, append summary to shared_state
    summary = "Web Research: Found competitor analysis data..."
    current_shared = state.get("shared_state", [])
    return {"shared_state": current_shared + [summary]}

async def task_management_node(state: SupervisorAgentState, writer) -> dict:
    # Execute task management agent, append summary to shared_state  
    summary = "Task Management: Created project 'Analysis' with 3 tasks..."
    current_shared = state.get("shared_state", [])
    return {"shared_state": current_shared + [summary]}

async def email_draft_node(state: SupervisorAgentState, writer) -> dict:
    # Execute email draft agent, append summary to shared_state
    summary = "Email Draft: Created outreach email draft in Gmail..."
    current_shared = state.get("shared_state", [])
    return {"shared_state": current_shared + [summary]}
```

### Integration Points

```yaml
DATABASE:
  - table: "conversations" - No schema changes needed, supervisor metadata in response
  - table: "messages" - No schema changes needed, maintains existing message storage
  
CONFIG:
  - add to: .env.example
  - pattern: "ASANA_API_KEY=your_asana_personal_access_token_here"
  - pattern: "ASANA_WORKSPACE_ID=your_default_workspace_gid"
  
ROUTES:
  - modify: api/endpoints.py
  - pattern: Replace sequential workflow with supervisor workflow in langgraph-supervisor-agents endpoint
  - preserve: Authentication, streaming, and response format compatibility
  
DEPENDENCIES:
  - add to: requirements.txt  
  - pattern: "asana>=3.2.0"
```

## Validation Loop

### Level 0: Streaming Foundation Validation (CRITICAL)
```bash
# MANDATORY FIRST STEP - validate streaming before workflow integration
source venv_linux/bin/activate
python test_streaming_poc.py

# Expected: Successful streaming structured output with SupervisorDecision
# If streaming fails, fix streaming logic before proceeding
# Must validate fallback to non-streaming works correctly
```

### Level 1: Syntax & Style
```bash
# Run these AFTER streaming validation passes
source venv_linux/bin/activate  # Use project virtual environment
ruff check agents/supervisor_agent.py --fix
ruff check agents/task_management_agent.py --fix  
ruff check tools/asana_tools.py --fix
mypy agents/supervisor_agent.py
mypy agents/task_management_agent.py
mypy tools/asana_tools.py

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE test_supervisor_agent.py with these test cases:
def test_supervisor_structured_output():
    """Supervisor agent returns valid SupervisorDecision structure"""
    # Test structured output format and streaming capability

def test_delegation_logic():
    """Supervisor makes correct delegation decisions based on query analysis"""
    # Test different query types route to appropriate agents

def test_iteration_limit_enforcement():
    """Supervisor enforces 20-iteration limit to prevent infinite loops"""
    # Test with mock state showing high iteration count

def test_state_synthesis():
    """Supervisor synthesizes final response from accumulated agent outputs"""
    # Test final response generation from multi-agent state

# CREATE test_task_management_agent.py with these test cases:
def test_asana_task_creation():
    """Task management agent creates tasks successfully"""
    # Test with mocked Asana API responses

def test_task_status_updates():
    """Agent can update task status and details"""
    # Test task modification operations

def test_asana_api_error_handling():
    """Graceful handling of Asana API failures"""
    # Test with simulated API errors

# CREATE test_supervisor_workflow.py with these test cases:
def test_complete_supervisor_workflow():
    """End-to-end workflow with multiple agent delegations"""
    # Test complex query requiring research -> task creation -> email draft

def test_shared_state_management():
    """Agents properly update and read from shared LangGraph state"""
    # Test state accumulation and agent coordination

def test_workflow_completion_detection():
    """Workflow properly detects completion and provides final response"""
    # Test various completion scenarios
```

```bash
# Run and iterate until passing:
source venv_linux/bin/activate
pytest tests/test_supervisor_agent.py -v
pytest tests/test_task_management_agent.py -v
pytest tests/test_supervisor_workflow.py -v
pytest tests/test_asana_tools.py -v

# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start the service with virtual environment
source venv_linux/bin/activate
python -m uvicorn api.endpoints:app --host 0.0.0.0 --port 8040 --reload

# Test supervisor workflow endpoint
curl -X POST http://localhost:8040/api/langgraph-supervisor-agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-jwt-token" \
  -d '{
    "query": "Research competitor analysis for AI startups and create tasks in Asana, then draft follow-up email",
    "user_id": "test123",
    "request_id": "req456", 
    "session_id": "session789"
  }'

# Expected: Supervisor delegates to research -> task management -> email agents
# Should return comprehensive response with all agent summaries

# Test simple query routing
curl -X POST http://localhost:8040/api/langgraph-supervisor-agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-jwt-token" \
  -d '{
    "query": "What is machine learning?",
    "user_id": "test123",
    "request_id": "req789",
    "session_id": "session123" 
  }'

# Expected: Direct response without delegation, workflow_complete: true

# If error: Check logs for stack trace and state management issues
```

## Final Validation Checklist
- [ ] **CRITICAL: Streaming foundation validated**: `python test_streaming_poc.py` passes completely
- [ ] **Streaming fallback works**: Non-streaming structured output works when streaming fails
- [ ] All tests pass: `source venv_linux/bin/activate && pytest tests/ -v`
- [ ] No linting errors: `ruff check agents/ tools/ graph/ api/`
- [ ] No type errors: `mypy agents/ tools/ graph/ api/`
- [ ] Supervisor structured output streaming works: Manual test with streamlit_app.py
- [ ] Asana integration creates real tasks: Test with valid API credentials
- [ ] Multi-agent coordination through shared state: Integration test
- [ ] 20-iteration limit prevents infinite loops: Edge case testing
- [ ] API endpoint backward compatibility: Test with existing frontend
- [ ] Error handling graceful at all levels: Test with invalid inputs/credentials
- [ ] Documentation updated and accurate: README reflects supervisor pattern
- [ ] Environment variables properly configured: .env.example complete

---

## Anti-Patterns to Avoid
- ❌ Don't create sequential workflow when supervisor pattern is required
- ❌ Don't skip structured output validation - supervisor decisions must be type-safe  
- ❌ Don't allow infinite delegation loops - iteration limits are critical
- ❌ Don't return full agent outputs in state - use concise summaries only
- ❌ Don't break backward compatibility with existing API clients
- ❌ Don't hardcode agent delegation logic - make it query-content aware
- ❌ Don't skip Asana API error handling - external APIs can fail
- ❌ Don't ignore streaming performance - structured output streaming must be responsive

## PRP Quality Score: 10/10

**Confidence Level**: 10/10 for one-pass implementation success

**Reasoning**: 
- ✅ Comprehensive context from existing codebase patterns
- ✅ Detailed Asana API research and integration plan  
- ✅ **Streaming complexity risk mitigated**: Isolated validation + fallback strategy + simplified implementation
- ✅ Clear supervisor pattern architecture design with intelligent orchestration philosophy
- ✅ Executable validation gates and testing strategy with streaming foundation validation
- ✅ Backward compatibility preservation plan
- ✅ **Task 0 streaming validation** eliminates primary complexity risk before workflow integration

**Key Success Factors**:
1. **Streaming Risk Eliminated**: Task 0 validates streaming foundation before complexity integration
2. **Graceful Fallback Strategy**: Non-streaming structured output fallback prevents implementation failures
3. Leverages proven patterns from 7.6-SequentialAgents and 7.3-MultiAgentIntro
4. Follows CLAUDE.md guidelines for modularity and testing
5. **Intelligent Orchestration Focus**: System prompt drives sophisticated agent interleaving, not rigid logic
6. **Simplified State Management**: Single shared_state list enables flexible multi-agent coordination
7. Includes comprehensive error handling and validation gates
8. Provides clear migration path from existing sequential implementation
9. Maintains API compatibility while enabling architectural evolution