# Supervisor Pattern Multi-Agent System

A sophisticated multi-agent system using Pydantic AI and LangGraph with a supervisor pattern for intelligent task coordination. The supervisor agent analyzes requests and dynamically delegates to specialized sub-agents (web research, task management, email drafting) with real-time streaming structured output.

## Features

- **Intelligent Supervisor Agent**: Dynamic delegation with streaming structured output
- **Real-Time Streaming**: Messages field streams live during final responses using `.run_stream()`
- **Shared State Management**: Append-only list for efficient agent communication
- **Dynamic Delegation**: Smart routing based on request analysis, not rigid sequences
- **Specialized Sub-Agents**: Web research (Brave API), task management (Asana API), email drafting (Gmail API)
- **Iteration Control**: 20-iteration limit prevents infinite delegation loops
- **Comprehensive Testing**: 22 unit tests covering all components

## Architecture

```
User Query → Supervisor Agent (with streaming)
                     ↓
            [Intelligent Analysis]
                     ↓
    ┌────────────────┼────────────────┐
    ↓                ↓                ↓
Web Research    Task Management   Email Draft
(Brave API)     (Asana API)      (Gmail API)
    ↓                ↓                ↓
    └────────────────┼────────────────┘
                     ↓
            Supervisor Agent (final response)
```

### Supervisor Pattern Flow:
1. **Supervisor Agent**: Analyzes request with streaming structured output
2. **Dynamic Delegation**: Routes to appropriate sub-agent based on content analysis
3. **Sub-Agent Execution**: Specialized agents perform tasks and update shared state
4. **Coordination**: Supervisor decides next steps based on accumulated work
5. **Final Response**: Supervisor provides streaming response when work is complete

### Key Innovations:
- **Streaming Structured Output**: Supervisor uses `.run_stream()` for real-time SupervisorDecision streaming
- **Intelligent Orchestration**: Dynamic delegation patterns, not mechanical routing
- **Shared State Communication**: Append-only list enables efficient agent coordination
- **No Sub-Agent Streaming**: Only supervisor streams to users, sub-agents update shared state

## Installation

1. **Navigate to this directory**:

```bash
cd 7_Agent_Architecture/7.7-SupervisorAgent
```

2. **Create and activate virtual environment**:
```bash
# Linux/Mac
python -m venv venv_linux
source venv_linux/bin/activate

# Windows
python -m venv venv_windows
venv_windows\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# ===== LLM Configuration =====
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-api-key-here
LLM_CHOICE=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1

# ===== Supabase Configuration =====
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key

# ===== Brave Search Configuration =====
BRAVE_API_KEY=BSA-your-brave-search-api-key-here

# ===== Asana Configuration =====
ASANA_API_KEY=your_asana_personal_access_token_here
ASANA_WORKSPACE_GID=your_workspace_gid_here

# ===== Gmail Configuration =====
GMAIL_CREDENTIALS_PATH=./credentials/credentials.json

# ===== Langfuse Configuration (Optional) =====
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://us.cloud.langfuse.com

# ===== Application Configuration =====
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=false
```

**Required Services:**
- **OpenAI API**: For LLM models and structured output
- **Supabase**: For document storage and conversation history
- **Brave Search API**: For web research functionality
- **Asana API**: For task and project management
- **Gmail API**: For email drafting and management

**Optional Services:**
- **LangFuse**: For complete agent observability and tracing

## Usage

### 🚀 **Full API Server** (Recommended)

The recommended way to use the system for production:

```bash
# Start the full API server
python -m uvicorn api.endpoints:app --host 0.0.0.0 --port 8040 --reload
```

**Features:**
- **JWT Authentication** via Supabase
- **Conversation history** 
- **User management**
- **Rate limiting**
- **Supervisor workflow metadata**
- **Real-time streaming responses**

**API Endpoints:**
- `POST /api/langgraph-supervisor-agent` - Main supervisor workflow endpoint (requires auth)
- `GET /health` - Health check
- `GET /` - System information

**Example API call:**
```bash
curl -X POST http://localhost:8040/api/langgraph-supervisor-agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "query": "Research AI trends and create a project plan with email outreach",
    "user_id": "user123",
    "request_id": "req456", 
    "session_id": "session789"
  }'
```

### 🖥️ **Frontend Interface** (AI Agent Mastery Course Web Interface)

To interact with this API endpoint through the web interface:

1. **Open a new terminal** (keep the API server running in the first terminal)

2. **Navigate to the frontend directory**:
```bash
cd ../6_Agent_Deployment/frontend
```

3. **Update the agent endpoint in your `.env` file**:
```bash
# Update the VITE_AGENT_ENDPOINT variable to:
VITE_AGENT_ENDPOINT=http://localhost:8040/api/langgraph-supervisor-agent
```

4. **Start the frontend**:
```bash
npm run dev
```

5. **Access the interface** at `http://localhost:8080` (or check the terminal for the exact port)

### 🎯 **Streamlit Web Interface** (Quick Testing)

The easiest way to see the supervisor pattern in action:

```bash
# Make sure you're in the project directory and virtual environment is activated
streamlit run streamlit_app.py
```

- **Real-time streaming supervisor responses**
- **Dynamic delegation visualization**
- **Shared state management display**
- **Clean, intuitive interface**

### Example Queries:

**Web Research Requests:**
```
"Research the latest developments in AI safety"
"Find information about Tesla's latest earnings report"
"What are the current trends in renewable energy?"
```

**Task Management Requests:**
```
"Create a project plan for our Q1 product launch"
"Set up tasks for the marketing campaign"
"Organize a timeline for the development project"
```

**Email Drafting Requests:**
```
"Draft an email to our investors about Q4 results"
"Write a professional email to the client about project updates"
"Compose an outreach email for potential partners"
```

**General Questions (Final Response):**
```
"What is machine learning and how does it work?"
"Explain the difference between AI and machine learning"
"How does natural language processing work?"
```

## Supervisor Decision Logic

The supervisor agent uses intelligent analysis to make delegation decisions:

### Web Research Delegation
Triggers when requests involve:
- Current information research
- Market analysis
- News and trends
- Company research
- **Example**: "Research the latest AI developments"

### Task Management Delegation
Triggers when requests involve:
- Project planning
- Task organization
- Timeline creation
- Resource management
- **Example**: "Create a project plan for our Q1 launch"

### Email Draft Delegation
Triggers when requests involve:
- Email composition
- Professional communication
- Outreach messages
- Business correspondence
- **Example**: "Draft an email to investors"

### Final Response (No Delegation)
Handles directly when requests involve:
- Educational explanations
- General questions
- System information
- Casual conversation
- **Example**: "What is machine learning?"

## Response Format

The supervisor pattern provides rich metadata about the delegation process:

```json
{
  "response": "I've completed research on AI safety and created a comprehensive summary...",
  "session_id": "session789",
  "supervisor_reasoning": "User requested current AI safety research, delegated to web research agent",
  "shared_state": [
    "Web Research: Found 5 key developments in AI safety including new governance frameworks...",
    "Task Management: Created project 'AI Safety Initiative' with 8 prioritized tasks..."
  ],
  "iteration_count": 3,
  "workflow_complete": true,
  "agent_type": "supervisor"
}
```

## System Components

### Agents (`agents/`)
- **Supervisor Agent**: Intelligent coordinator with streaming structured output
- **Web Research Agent**: Brave API integration for comprehensive research
- **Task Management Agent**: Asana API integration for project management
- **Email Draft Agent**: Gmail integration for professional email composition
- **Fallback Agent**: Error handling and graceful degradation

### Tools (`tools/`)
- **Asana Tools**: Complete Asana API integration (projects, tasks, workspaces)
- **Brave Tools**: Brave API search with intelligent result processing
- **Gmail Tools**: Gmail API integration for drafting and management

### Workflow (`graph/`)
- **SupervisorAgentState**: Shared state with append-only communication list
- **Supervisor Workflow**: LangGraph orchestration with intelligent routing

### Streaming Foundation (`test_streaming_poc.py`)
- **Real-Time Validation**: Tests `.run_stream()` structured output streaming
- **Delegation Testing**: Validates supervisor decision logic
- **Streaming Performance**: Ensures messages field streams in real-time

## Streaming Architecture

### Supervisor Streaming (`.run_stream()`)
```python
async with supervisor_agent.run_stream(query, deps=deps) as result:
    async for partial_decision in result.stream():
        # Stream messages field for final responses
        if partial_decision.messages and partial_decision.final_response:
            writer(partial_decision.messages)
    
    # Get final structured decision
    decision = await result.get_output()
```

### SupervisorDecision Model
```python
class SupervisorDecision(BaseModel):
    messages: Optional[str] = None  # Only for final responses
    delegate_to: Optional[str] = None  # "web_research", "task_management", "email_draft"
    reasoning: str  # Decision explanation
    final_response: bool = False  # True for final response, False for delegation
```

## Development

### Running Tests

```bash
# Run all tests
source venv_linux/bin/activate
pytest tests/ -v

# Test supervisor workflow specifically
pytest tests/test_supervisor_workflow.py -v

# Test streaming foundation
python test_streaming_poc.py

# Run with coverage
pytest tests/ --cov=agents --cov=tools --cov=graph --cov=api
```

### Project Structure

```
agents/
├── __init__.py
├── deps.py                     # Dependency injection patterns
├── prompts.py                  # Centralized system prompts
├── supervisor_agent.py         # Intelligent coordinator with streaming
├── web_research_agent.py       # Brave API web research
├── task_management_agent.py    # Asana API integration
├── email_draft_agent.py        # Gmail API integration
└── fallback_agent.py           # Error handling

tools/
├── __init__.py
├── asana_tools.py              # Complete Asana API toolkit
├── brave_tools.py              # Brave API integration
└── gmail_tools.py              # Gmail API tools

graph/
├── __init__.py
├── state.py                    # SupervisorAgentState management
└── workflow.py                 # Supervisor pattern orchestration

tests/
├── __init__.py
├── test_supervisor_agent.py    # Supervisor agent tests
├── test_supervisor_workflow.py # Workflow integration tests
├── test_web_research_agent.py  # Web research tests
├── test_task_management_agent.py # Task management tests
├── test_email_draft_agent.py   # Email draft tests
├── test_asana_tools.py         # Asana tools tests
└── test_tools.py               # General tool tests

test_streaming_poc.py           # Streaming foundation validation
streamlit_app.py               # Streamlit interface
requirements.txt               # Dependencies
.env.example                   # Environment template
```

## Troubleshooting

### Common Issues

1. **Streaming Issues**: Ensure `.run_stream()` is properly implemented
2. **Environment Variables**: Check `.env` file configuration, especially new Asana variables
3. **Delegation Logic**: Verify supervisor decision patterns in streaming POC
4. **Shared State**: Check append-only list accumulation between agents
5. **API Keys**: Verify Asana API key and workspace GID

### Debug Mode

Enable debug output:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### Supervisor Pattern Issues

Check supervisor decision logic:
- **Delegation Decisions**: Should have `messages=None`, `delegate_to` set, `final_response=False`
- **Final Responses**: Should have `messages` populated, `delegate_to=None`, `final_response=True`
- **Shared State Flow**: Verify agent summaries accumulate correctly
- **Iteration Limits**: Ensure 20-iteration limit prevents infinite loops

### Streaming Validation

Test streaming foundation:
```bash
python test_streaming_poc.py
```

Should show:
- ✅ Real-time structured output streaming
- ✅ Messages field streaming for final responses  
- ✅ Correct delegation logic (no messages for delegations)
- ✅ All test scenarios passing

## Architecture Evolution

This supervisor pattern represents an evolution from traditional multi-agent systems:

### Traditional Approach
- **Rigid Routing**: Simple keyword-based delegation
- **Sequential Execution**: Fixed agent order
- **Limited Coordination**: Basic state passing

### Supervisor Pattern
- **Intelligent Orchestration**: Context-aware delegation decisions
- **Dynamic Coordination**: Flexible agent interaction patterns
- **Shared State Management**: Sophisticated inter-agent communication
- **Real-Time Streaming**: Live structured output for better UX

The supervisor agent demonstrates intelligent orchestration rather than mechanical routing, making delegation decisions based on accumulated context and work progress.

## Examples

### Research & Task Management Example

**Input:**
```
"Research the latest AI trends and create a project plan for implementing them"
```

**Supervisor Flow:**
1. **Analysis**: Detects both research and planning requirements
2. **Web Research**: Delegates to gather current AI trend information
3. **Task Management**: Delegates to create implementation project plan
4. **Final Response**: Synthesizes results into comprehensive response

**Shared State Evolution:**
```
Iteration 1: []
Iteration 2: ["Web Research: Found 5 key AI trends including enterprise adoption, ethical AI frameworks..."]
Iteration 3: ["Web Research: ...", "Task Management: Created project 'AI Implementation Strategy' with 12 tasks organized by priority..."]
Final: Supervisor provides comprehensive synthesis
```

### Direct Response Example

**Input:**
```
"What is the difference between AI and machine learning?"
```

**Supervisor Flow:**
1. **Analysis**: Recognizes educational question
2. **Direct Response**: Provides streaming explanation without delegation

This system optimizes for intelligent coordination and real-time user experience while maintaining sophisticated multi-agent capabilities.