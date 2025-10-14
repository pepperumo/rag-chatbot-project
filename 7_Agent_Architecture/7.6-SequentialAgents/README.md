# Sequential Research & Outreach Agent System

A specialized multi-agent system using Pydantic AI and LangGraph for automated research and professional outreach. This system executes a sequential workflow: guardrail → research → enrichment → email draft creation, optimizing for lead research and outreach automation.

## Features

- **Guardrail Routing**: Lightweight agent determines if requests are for research/outreach or normal conversation
- **Sequential Workflow**: Research → Data Enrichment → Email Draft creation in a coordinated flow
- **Intelligent Research**: Brave API integration for comprehensive web research on people and companies
- **Data Enrichment**: Secondary agent fills gaps in initial research (location, company details, education)
- **Gmail Integration**: Automated email draft creation and storage in Gmail drafts folder
- **Streaming Support**: Real-time response streaming throughout the sequential workflow
- **Cost Optimization**: Small model for guardrail decisions, larger models for execution
- **Conversation Management**: Only final agents update conversation history

## Architecture

```
User Query → Guardrail Agent → Research/Outreach Detection
                ↓                              ↓
    Normal Conversation              Sequential Research Flow
            ↓                               ↓
    Fallback Agent           Research → Enrichment → Email Draft
```

### Sequential Research Flow:
1. **Guardrail Agent**: Detects research/outreach requests vs normal conversation (lightweight, fast)
2. **Research Agent**: Performs comprehensive web research using Brave Search API
3. **Enrichment Agent**: Fills gaps in research data (location, company details, education, etc.)
4. **Email Draft Agent**: Creates professional outreach emails and saves to Gmail drafts
5. **Fallback Agent**: Handles normal conversational requests

### Conversation History Strategy:
- **Intermediate Agents**: Stream responses to user but don't update conversation history
- **Final Agents**: Only email draft and fallback agents update conversation history
- **State Flow**: Each agent adds its summary to state for the next agent to use

### Cost Optimization Strategy:
- **Minimal Guardrail Dependencies**: Guardrail agent uses only session ID for fast decisions
- **Sequential Execution**: Agents execute in order, each building on previous results
- **Streaming with Fallback**: Reduces latency while maintaining reliability
- **Efficient State Flow**: LangGraph manages state transitions efficiently

## Installation

1. **Navigate to this directory**:

```bash
cd 7_Agent_Architecture/7.6-SequentialAgents
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
LLM_CHOICE_SMALL=gpt-4o-nano  # For guardrail agent
LLM_BASE_URL=https://api.openai.com/v1

# ===== Supabase Configuration =====
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key

# ===== Brave Search Configuration =====
BRAVE_API_KEY=BSA-your-brave-search-api-key-here

# ===== Gmail Configuration =====
# IMPORTANT: Uses compose and send scope for Gmail draft creation
GMAIL_CREDENTIALS_PATH=./credentials/credentials.json
GMAIL_TOKEN_PATH=./credentials/token.json

# ===== Langfuse Configuration (Optional) =====
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://us.cloud.langfuse.com

# ===== Application Configuration =====
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=false
PORT=8040
```

**Required Services:**
- **OpenAI API**: For LLM models and embeddings
- **Supabase**: For document storage and conversation history
- **Brave Search API**: For web search functionality
- **Gmail API**: For email draft creation (compose/send scope)

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
- **Sequential workflow metadata**

**API Endpoints:**
- `POST /api/langgraph-sequential-agents` - Main sequential workflow endpoint (requires auth)
- `GET /health` - Health check
- `GET /` - System information

**Example API call:**
```bash
curl -X POST http://localhost:8040/api/langgraph-sequential-agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "query": "Research Jane Doe at InnovateCorp and draft an outreach email",
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
VITE_AGENT_ENDPOINT=http://localhost:8040/api/langgraph-sequential-agents
```

4. **Start the frontend**:
```bash
npm run dev
```

5. **Access the interface** at `http://localhost:8080` (or check the terminal for the exact port)

### 🎯 **Streamlit Web Interface** (Quick Testing)

A simple way to quickly test the agent with a basic UI:

```bash
# Make sure you're in the project directory and virtual environment is activated
streamlit run streamlit_app.py
```

- **No authentication required**
- **Real-time streaming responses**
- **Sequential workflow indicators**
- **Clean, simple interface**
- **Session management**

### Example Queries:

**Research & Outreach Requests:**
```
"Research John Doe at TechCorp and draft an outreach email"
"Find information about Sarah Smith at Microsoft and create an email draft"
"Look up details about ABC Company and write a business development email"
"Research the CEO of XYZ startup and draft a partnership proposal"
```

**Normal Conversation:**
```
"How are you today?"
"What's the weather like?"
"Explain machine learning to me"
"Help me understand this concept"
```


## Sequential Workflow Logic

The guardrail agent analyzes queries and routes to:

### Research/Outreach Flow (`research_request`)
Triggers the complete sequential workflow for requests involving:
- Researching people or companies
- Creating professional outreach emails
- Lead research and business development
- **Example**: "Research John Doe at TechCorp and draft an outreach email"

**Sequential Steps:**
1. **Research Agent**: Gathers initial information using Brave Search
2. **Enrichment Agent**: Fills data gaps (location, company details, education)
3. **Email Draft Agent**: Creates professional email and saves to Gmail drafts

### Normal Conversation (`conversation`)
Routes directly to fallback agent for:
- General assistant queries
- Casual conversation
- System help and guidance
- **Example**: "How are you today?"

## Response Format

All interfaces return responses with sequential workflow metadata:

```json
{
  "text": "I've completed research on John Doe and created a professional email draft...",
  "session_id": "session789",
  "is_research_request": true,
  "routing_reason": "This is a research and outreach request",
  "research_summary": "John Doe is a Senior Engineer at TechCorp...",
  "enrichment_summary": "Additional research found he graduated from Stanford...",
  "email_draft_created": true,
  "agent_type": "email_draft",
  "complete": true
}
```

## System Components

### Agents (`agents/`)
- **Guardrail Agent**: Lightweight routing decisions with minimal dependencies
- **Research Agent**: Brave API integration for comprehensive web research
- **Enrichment Agent**: Data gap filling and additional research
- **Email Draft Agent**: Gmail integration for professional email creation
- **Fallback Agent**: Normal conversation handling
- **Dependencies**: Shared dependency injection patterns

### Tools (`tools/`)
- **Brave Tools**: Brave API search with error handling and relevance scoring
- **Gmail Tools**: Gmail draft creation and management

### Workflow (`graph/`)
- **State Management**: Sequential agent state for workflow coordination
- **Workflow Orchestration**: LangGraph-based sequential execution

### API (`api/`)
- **Models**: Pydantic models for requests/responses
- **Endpoints**: FastAPI endpoints with authentication
- **Streaming**: Real-time response streaming utilities
- **Database Utils**: Supabase integration for conversations

## Gmail Configuration

**Important**: This system uses compose/send Gmail scope but **only creates drafts** - no emails are sent automatically.

1. **Set up Gmail API credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable Gmail API
   - Create OAuth2 credentials
   - Download `credentials.json`

2. **Required scopes**:
   ```
   https://www.googleapis.com/auth/gmail.compose
   https://www.googleapis.com/auth/gmail.send
   ```

3. **Place credentials**:
   ```bash
   mkdir credentials
   cp path/to/credentials.json credentials/
   ```

4. **First run**: The system will prompt for OAuth consent and save a token file

## Observability & Monitoring

The system includes **LangFuse integration** for comprehensive observability:

### LangFuse Features
- **Sequential Workflow Tracing**: Full visibility into each agent in the workflow
- **Cost Analysis**: Track efficiency of guardrail routing and agent usage
- **Performance Metrics**: Response times and success rates per workflow step
- **User & Session Tracking**: Analyze workflow patterns by user
- **Optional Setup**: Works seamlessly when configured, gracefully disabled when not

### Setup LangFuse (Optional)
1. Sign up at [LangFuse Cloud](https://us.cloud.langfuse.com/)
2. Create a new project and get your keys
3. Add to your `.env` file:
   ```env
   LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
   LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
   LANGFUSE_HOST=https://us.cloud.langfuse.com
   ```
4. Restart your application - tracing will automatically begin

## Development

### Running Tests

```bash
# Run all tests
source venv_linux/bin/activate  # or venv_windows\Scripts\activate
pytest tests/ -v

# Run specific agent tests
pytest tests/test_guardrail_agent.py -v
pytest tests/test_research_agent.py -v
pytest tests/test_enrichment_agent.py -v
pytest tests/test_email_draft_agent.py -v
pytest tests/test_fallback_agent.py -v

# Run workflow tests
pytest tests/test_sequential_workflow.py -v

# Run with coverage
pytest tests/ --cov=agents --cov=tools --cov=graph --cov=api
```

### Project Structure

```
agents/
├── __init__.py
├── deps.py                    # Dependency injection patterns
├── prompts.py                # Centralized system prompts
├── guardrail_agent.py        # Research/conversation routing
├── research_agent.py         # Brave API web research
├── enrichment_agent.py       # Data gap filling
├── email_draft_agent.py      # Gmail draft creation
└── fallback_agent.py         # Normal conversation

tools/
├── __init__.py
├── brave_tools.py            # Brave API integration
└── gmail_tools.py            # Gmail draft creation tools

graph/
├── __init__.py
├── state.py                  # Sequential agent state management
└── workflow.py               # LangGraph sequential workflow

api/
├── __init__.py
├── endpoints.py              # FastAPI server with sequential workflow
├── models.py                 # Pydantic models
├── streaming.py              # Streaming utilities
└── db_utils.py               # Supabase integration

tests/
├── __init__.py
├── test_guardrail_agent.py   # Guardrail routing tests
├── test_research_agent.py    # Research agent tests
├── test_enrichment_agent.py  # Enrichment agent tests
├── test_email_draft_agent.py # Email draft agent tests
├── test_fallback_agent.py    # Fallback agent tests
├── test_tools.py             # Tool function tests
└── test_sequential_workflow.py # Workflow integration tests

streamlit_app.py              # Streamlit interface
requirements.txt              # Dependencies
.env.example                  # Environment template
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and virtual environment is activated
2. **Environment Variables**: Check `.env` file configuration
3. **Supabase Connection**: Verify Supabase credentials and connection
4. **Brave API**: Verify Brave Search API key is valid
5. **Gmail Setup**: Ensure OAuth2 credentials and compose/send scope configuration
6. **Port Conflicts**: Default port is 8040 for the API server

### Debug Mode

Enable debug output:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### Workflow Issues

Check guardrail routing decisions:
- **Research Requests**: Should include research + email creation intent
- **Normal Conversation**: General questions, explanations, casual chat
- **State Flow**: Verify research data passes correctly between agents
- **Email Creation**: Check Gmail credentials and permissions

### Common Workflow Patterns

**Successful Research Flow:**
1. Guardrail detects research intent → `is_research_request: true`
2. Research agent gathers initial data → `research_summary` populated
3. Enrichment agent fills gaps → `enrichment_summary` populated  
4. Email draft agent creates email → `email_draft_created: true`

**Conversation Flow:**
1. Guardrail detects conversation → `is_research_request: false`
2. Routes directly to fallback agent → `agent_type: "fallback"`

### Rate Limiting & API Usage

**Brave Search API:**
- Built-in 1-second delay between API calls to prevent quota issues
- Research flow makes 2 sequential API calls (research + enrichment)
- Rate limiting helps avoid 429 errors during sequential execution

## Cost Optimization Notes

- **Guardrail Efficiency**: Uses smaller model for fast routing decisions
- **Sequential Execution**: Each agent builds on previous results, no redundant work
- **Streaming Strategy**: Reduce perceived latency with real-time responses
- **State Management**: Efficient data flow between agents without redundant API calls

This architecture provides both cost efficiency and comprehensive research capabilities by executing agents sequentially with intelligent state management.

## Examples

### Research & Outreach Example

**Input:**
```
"Research Sarah Chen at DataFlow Inc and draft a partnership email"
```

**Workflow:**
1. **Guardrail**: Detects research + email intent
2. **Research**: Finds Sarah's role, company background, recent news
3. **Enrichment**: Discovers education, location, recent achievements
4. **Email Draft**: Creates personalized outreach email saved to Gmail drafts

**Output:**
```
✉️ I've researched Sarah Chen at DataFlow Inc and created a professional outreach email draft in your Gmail drafts folder.

Research Summary: Sarah Chen is the VP of Engineering at DataFlow Inc, a fast-growing data analytics startup...

Enrichment Data: Additional research shows she graduated from MIT with a CS degree and recently spoke at the Data Summit 2024...

Email Draft: A personalized partnership proposal highlighting relevant synergies has been created and saved to your Gmail drafts.
```

### Conversation Example

**Input:**
```
"How does machine learning work?"
```

**Workflow:**
1. **Guardrail**: Detects conversation intent
2. **Fallback**: Provides educational explanation

**Output:**
```
Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed...
```

This system optimizes for professional research and outreach automation while maintaining natural conversation capabilities.