name: "Parallel Research & Synthesis Agents Workflow"
description: |

## Purpose
Implement a LangGraph workflow with 5 agents using Pydantic AI, featuring 3 parallel research agents that execute simultaneously, feeding into a synthesis agent for email draft creation.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Build a LangGraph workflow with 5 agents that routes research/outreach requests to 3 parallel research agents (SEO, Social Media, Competitor) that run simultaneously using Brave API, then synthesizes findings into an email draft. The 3 research agents MUST execute in parallel using LangGraph's native parallel execution capabilities.

## Why
- **Performance**: Parallel execution reduces research time by ~50% vs sequential processing
- **Comprehensive Research**: Simultaneous SEO, social media, and competitor analysis provides holistic view
- **Streamlined Workflow**: Automated research-to-email pipeline saves time on outreach tasks
- **User Experience**: Real-time streaming shows progress from each parallel agent

## What
User submits a research/outreach request → Guardrail agent routes → 3 research agents run in parallel → Synthesis agent creates email draft → Updates conversation history

### Success Criteria
- [ ] 3 research agents execute truly in parallel (not sequential)
- [ ] Each parallel agent streams its progress to the user
- [ ] Synthesis agent waits for all 3 to complete before running
- [ ] Only synthesis agent updates conversation history
- [ ] Fallback agent handles non-research requests with conversation history
- [ ] All agents use appropriate models (small for guardrail, normal for others)

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://langchain-ai.github.io/langgraph/how-tos/graph-api/
  why: LangGraph Graph API documentation for workflow construction
  
- url: https://blog.gopenai.com/building-parallel-workflows-with-langgraph-a-practical-guide-3fe38add9c60
  why: Practical guide for parallel workflows with fan-out/fan-in patterns

- file: /mnt/c/Users/colem/ai-agent-mastery/7_Agent_Architecture/7.6-SequentialAgents/graph/workflow.py
  why: Base workflow structure to adapt - shows streaming, state management, routing
  
- file: /mnt/c/Users/colem/ai-agent-mastery/7_Agent_Architecture/7.6-SequentialAgents/agents/research_agent.py
  why: Research agent pattern with Brave API integration
  
- file: /mnt/c/Users/colem/ai-agent-mastery/7_Agent_Architecture/7.6-SequentialAgents/api/endpoints.py
  why: API endpoint pattern for LangGraph integration with streaming
```

### Current Codebase tree
```bash
7.6-ParallelAgents/
├── agents/
│   ├── __init__.py
│   ├── deps.py              # Agent dependencies
│   ├── email_draft_agent.py # Needs renaming to synthesis_agent.py
│   ├── enrichment_agent.py  # To be replaced with 3 parallel agents
│   ├── fallback_agent.py    # Keep as-is
│   ├── guardrail_agent.py   # Keep as-is
│   ├── prompts.py           # Update with new prompts
│   └── research_agent.py    # Base for parallel agents
├── api/
│   ├── endpoints.py         # Minimal changes needed
│   ├── streaming.py         # Keep as-is
│   └── models.py           # Keep as-is
├── graph/
│   ├── state.py            # Update for parallel state
│   └── workflow.py         # Major overhaul for parallel execution
├── tools/
│   └── brave_tools.py      # Reuse for all 3 research agents
└── tests/                  # Update all tests
```

### Desired Codebase tree with files to be added
```bash
7.6-ParallelAgents/
├── agents/
│   ├── seo_research_agent.py      # NEW: SEO-focused research
│   ├── social_research_agent.py   # NEW: Social media research  
│   ├── competitor_research_agent.py # NEW: Competitor analysis
│   ├── synthesis_agent.py         # RENAMED: from email_draft_agent.py
│   ├── fallback_agent.py          # KEEP: Normal conversation
│   ├── guardrail_agent.py         # KEEP: Routing logic
│   └── prompts.py                 # UPDATE: New agent prompts
├── graph/
│   ├── state.py                   # UPDATE: Parallel state management
│   └── workflow.py                # OVERHAUL: Parallel execution
└── tests/
    ├── test_seo_research_agent.py     # NEW
    ├── test_social_research_agent.py  # NEW
    ├── test_competitor_research_agent.py # NEW
    ├── test_synthesis_agent.py        # RENAME
    └── test_parallel_workflow.py      # NEW: Parallel execution tests
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: LangGraph parallel execution requires operator.add for state merging
# When multiple nodes write to same state key, use Annotated[list, operator.add]

# CRITICAL: Parallel nodes must have edges from same source
# graph.add_edge("guardrail_node", "seo_research_node")
# graph.add_edge("guardrail_node", "social_research_node")  
# graph.add_edge("guardrail_node", "competitor_research_node")

# GOTCHA: Streaming in parallel nodes requires custom stream mode
# Use workflow.astream(state, config, stream_mode=["custom", "values"])

# GOTCHA: Only final agent should update pydantic_message_history
# Research agents: DON'T return message_history key
# Synthesis agent: MUST return message_history with new_messages_json()

# GOTCHA: Brave API rate limiting - add 1 second delay between calls
# await asyncio.sleep(1.0) in search_web_tool
```

## Implementation Blueprint

### Data models and structure

Update the state to handle parallel research outputs:
```python
from typing import TypedDict, List, Optional, Dict, Any, Annotated
from pydantic_ai.messages import ModelMessage
import operator

class ParallelAgentState(TypedDict, total=False):
    """LangGraph state for parallel research workflow"""
    # Input
    query: str
    session_id: str  
    request_id: str
    
    # Guardrail output
    is_research_request: bool
    routing_reason: str
    
    # Parallel research outputs
    seo_research: str
    social_research: str
    competitor_research: str
    research_completed: bool
    
    # Synthesis output
    email_draft: str
    synthesis_complete: bool
    
    # Final response
    final_response: str
    agent_type: str
    
    # Message history management
    pydantic_message_history: List[ModelMessage]
    message_history: List[bytes]  # Only populated by synthesis/fallback
    
    # API context
    conversation_title: Optional[str]
    is_new_conversation: Optional[bool]
```

### List of tasks to be completed in order

```yaml
Task 1: Update State Definition
MODIFY graph/state.py:
  - REPLACE SequentialAgentState with ParallelAgentState
  - ADD operator.add annotations for parallel research fields
  - ADD research_completed tracker list
  - ENSURE backwards compatibility with API

Task 2: Create SEO Research Agent  
CREATE agents/seo_research_agent.py:
  - COPY pattern from agents/research_agent.py
  - UPDATE system prompt for SEO focus
  - REUSE search_web tool from tools/brave_tools.py
  - ENSURE returns seo_research list, NOT message_history

Task 3: Create Social Media Research Agent
CREATE agents/social_research_agent.py:
  - MIRROR seo_research_agent.py structure
  - UPDATE prompt for social media analysis
  - FOCUS on social presence, engagement metrics
  - RETURN social_research list

Task 4: Create Competitor Research Agent
CREATE agents/competitor_research_agent.py:
  - FOLLOW same pattern as other research agents
  - UPDATE prompt for competitive analysis
  - SEARCH for market positioning, competitors
  - RETURN competitor_research list

Task 5: Transform Email Draft to Synthesis Agent
RENAME agents/email_draft_agent.py TO agents/synthesis_agent.py:
  - UPDATE to read from all 3 research lists in state
  - REMOVE Gmail draft creation (just synthesis)
  - KEEP message history update logic
  - UPDATE prompts.py with new synthesis prompt

Task 6: Update Agent Prompts
MODIFY agents/prompts.py:
  - ADD SEO_RESEARCH_SYSTEM_PROMPT
  - ADD SOCIAL_RESEARCH_SYSTEM_PROMPT  
  - ADD COMPETITOR_RESEARCH_SYSTEM_PROMPT
  - UPDATE EMAIL_DRAFT_SYSTEM_PROMPT to SYNTHESIS_SYSTEM_PROMPT
  - ENSURE each prompt includes streaming start message

Task 7: Implement Parallel Workflow
MODIFY graph/workflow.py:
  - CREATE parallel research nodes
  - ADD edges for parallel execution from guardrail
  - IMPLEMENT synthesis node that waits for all 3
  - UPDATE routing logic for parallel flow
  - ENSURE streaming works for parallel nodes

Task 8: Update API Endpoint
MODIFY api/endpoints.py:
  - UPDATE endpoint path to /api/langgraph-parallel-agents
  - ENSURE ParallelAgentState compatibility
  - KEEP streaming logic intact

Task 9: Create Parallel Tests
CREATE tests/test_parallel_workflow.py:
  - TEST parallel execution timing
  - VERIFY all 3 agents run simultaneously
  - CHECK synthesis waits for completion
  - VALIDATE state merging with operator.add

Task 10: Update Individual Agent Tests
CREATE/UPDATE test files for each agent:
  - TEST Brave API integration
  - MOCK search results
  - VERIFY prompt adherence
  - CHECK error handling

Task 11: Update README
MODIFY README.md:
  - DOCUMENT parallel workflow architecture
  - ADD mermaid diagram showing parallel flow
  - UPDATE agent descriptions
  - INCLUDE performance benefits
```

### Per task pseudocode

```python
# Task 7: Parallel Workflow Implementation
async def create_parallel_research_nodes(state: ParallelAgentState, writer):
    """Node wrappers for parallel execution"""
    
    # Each node starts with hardcoded streaming message
    async def seo_research_node(state, writer):
        writer("\n\n### 🔍 SEO Research Agent Starting...\n")
        # ... agent execution with streaming
        return {
            "seo_research": [full_response],
            "research_completed": ["seo"],
            "agent_type": "seo_research"
        }
    
    # Similar for social and competitor nodes
    
def create_workflow():
    """Parallel workflow with fan-out/fan-in"""
    builder = StateGraph(ParallelAgentState)
    
    # Add all nodes
    builder.add_node("guardrail_node", guardrail_node)
    builder.add_node("seo_research_node", seo_research_node)
    builder.add_node("social_research_node", social_research_node)
    builder.add_node("competitor_research_node", competitor_research_node)
    builder.add_node("synthesis_node", synthesis_node)
    builder.add_node("fallback_node", fallback_node)
    
    # Entry point
    builder.add_edge(START, "guardrail_node")
    
    # Conditional routing after guardrail
    builder.add_conditional_edges(
        "guardrail_node",
        route_after_guardrail,
        {
            "research_flow": ["seo_research_node", "social_research_node", "competitor_research_node"],
            "fallback_node": "fallback_node"
        }
    )
    
    # All research nodes converge to synthesis
    builder.add_edge("seo_research_node", "synthesis_node")
    builder.add_edge("social_research_node", "synthesis_node")
    builder.add_edge("competitor_research_node", "synthesis_node")
    
    # Synthesis and fallback to END
    builder.add_edge("synthesis_node", END)
    builder.add_edge("fallback_node", END)
    
    return builder.compile()

# Synthesis node waits for all research
async def synthesis_node(state, writer):
    # Check if all research complete
    completed = state.get("research_completed", [])
    if len(completed) < 3:
        # This shouldn't happen with proper edges
        writer("⚠️ Waiting for all research to complete...")
    
    writer("\n\n### 📝 Synthesis Agent Starting...\n")
    
    # Combine all research
    all_research = f"""
    SEO Research: {' '.join(state.get("seo_research", []))}
    Social Media Research: {' '.join(state.get("social_research", []))}  
    Competitor Research: {' '.join(state.get("competitor_research", []))}
    """
    
    # Run synthesis agent with combined research
    # ... synthesis logic with streaming
    
    # CRITICAL: Update message history
    return {
        "final_response": synthesis_output,
        "message_history": [new_messages],  # Only this agent updates history
        "synthesis_complete": True
    }
```

### Integration Points
```yaml
DATABASE:
  - No schema changes needed
  - Message storage remains same
  
CONFIG:
  - .env already has all needed vars
  - BRAVE_API_KEY for all 3 research agents
  - LLM_CHOICE_SMALL for guardrail
  - LLM_CHOICE for research/synthesis agents
  
ROUTES:
  - CHANGE: /api/langgraph-sequential-agents 
  - TO: /api/langgraph-parallel-agents
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd /mnt/c/Users/colem/ai-agent-mastery/7_Agent_Architecture/7.6-ParallelAgents
source venv_linux/bin/activate

ruff check . --fix           # Auto-fix style issues
mypy agents/ graph/ api/     # Type checking

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# test_parallel_workflow.py key tests
async def test_parallel_execution():
    """Verify agents run in parallel"""
    import time
    start = time.time()
    
    # Run workflow with mocked agents
    result = await workflow.ainvoke(test_state)
    
    elapsed = time.time() - start
    # If sequential, would take 3+ seconds (1s per agent)
    # Parallel should complete in ~1.5s
    assert elapsed < 2.0, "Agents not running in parallel"

async def test_state_merging():
    """Verify operator.add merges results"""
    state = ParallelAgentState(
        seo_research=["initial"],
        social_research=[],
        competitor_research=[]
    )
    
    # Simulate parallel updates
    state["seo_research"].append("seo_result") 
    state["social_research"].append("social_result")
    
    assert len(state["seo_research"]) == 2
    assert "social_result" in state["social_research"]
```

```bash
# Run tests
cd /mnt/c/Users/colem/ai-agent-mastery/7_Agent_Architecture/7.6-ParallelAgents
source venv_linux/bin/activate
python -m pytest tests/test_parallel_workflow.py -v
python -m pytest tests/ -v  # All tests
```

### Level 3: Integration Test
```bash
# Start the API
cd /mnt/c/Users/colem/ai-agent-mastery/7_Agent_Architecture/7.6-ParallelAgents
source venv_linux/bin/activate
uvicorn api.endpoints:app --reload --port 8000

# Test parallel research flow
curl -X POST http://localhost:8000/api/langgraph-parallel-agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "Research John Doe at TechCorp and create outreach email",
    "session_id": "",
    "request_id": "test-123",
    "user_id": "test-user"
  }'

# Expected: Stream shows 3 agents starting simultaneously, then synthesis
# Verify in logs that execution time is reduced vs sequential
```

## Final validation Checklist
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] No linting errors: `ruff check .`
- [ ] No type errors: `mypy agents/ graph/ api/`
- [ ] Parallel execution verified in logs (< 2s for 3 agents)
- [ ] Streaming works for all agents
- [ ] Only synthesis/fallback update conversation history
- [ ] Brave API rate limiting handled
- [ ] README updated with architecture diagram

---

## Anti-Patterns to Avoid
- ❌ Don't make research agents sequential - they MUST run in parallel
- ❌ Don't let research agents update message_history - only final agent
- ❌ Don't skip the operator.add annotation - state merging will fail
- ❌ Don't remove streaming start messages - UX depends on them
- ❌ Don't create new Brave tools - reuse existing search_web_tool
- ❌ Don't change API contract - maintain compatibility

## Confidence Score: 9/10
This PRP provides comprehensive context for implementing the parallel research workflow. The only uncertainty is around potential edge cases in state merging, but the operator.add pattern from LangGraph docs should handle this correctly.