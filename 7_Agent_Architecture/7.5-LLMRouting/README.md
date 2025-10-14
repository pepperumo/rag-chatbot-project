# LLM Routing Multi-Agent System

A cost-optimized multi-agent routing system using Pydantic AI and LangGraph. This system intelligently routes user queries to specialized agents (web search, email search, or RAG) based on content analysis, optimizing both performance and cost.

## Features

- **Intelligent Routing**: Lightweight router agent determines the best specialized agent for each query
- **Cost Optimization**: Router uses minimal dependencies for fast, inexpensive routing decisions
- **Specialized Agents**: Dedicated agents for web search (Brave API), email search (Gmail readonly), and RAG
- **Streaming Support**: Real-time response streaming with graceful fallback to non-streaming
- **Multiple Interfaces**: Streamlit UI, FastAPI with authentication, and comprehensive API
- **Modular Design**: Separate concerns between routing, search agents, and workflow orchestration

## Architecture

```
User Query → Router Agent → Conditional Routing → Specialized Agent → Response
                ↓
   web_search / email_search / rag_search / fallback
```

1. **Router Agent**: Analyzes query content and makes routing decisions (lightweight, fast)
2. **Web Search Agent**: Handles current events, news, and general web content via Brave API
3. **Email Search Agent**: Searches Gmail with readonly permissions for email-related queries
4. **RAG Search Agent**: Searches document knowledge base for internal information
5. **Fallback Agent**: Handles unclear or general assistant queries

### Cost Optimization Strategy

- **Minimal Router Dependencies**: Router agent uses only session ID for fast decisions
- **Targeted Agent Activation**: Only the selected specialized agent loads full dependencies
- **Streaming with Fallback**: Reduces latency while maintaining reliability
- **Efficient Conditional Routing**: LangGraph routes to exactly one agent per query

## Installation

1. **Navigate to this directory**:

```bash
cd 7_Agent_Architecture/7.5-LLMRouting
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

# ===== Gmail Configuration =====
# IMPORTANT: Uses readonly scope for Gmail access
GMAIL_CREDENTIALS_PATH=./credentials/credentials.json

# ===== Langfuse Configuration (Optional) =====
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://us.cloud.langfuse.com

# ===== Application Configuration =====
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=false
PORT=8002
```

**Required Services:**
- **OpenAI API**: For LLM models and embeddings
- **Supabase**: For document storage and conversation history
- **Brave Search API**: For web search functionality
- **Gmail API**: For email search (readonly scope)

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
- **Intelligent routing metadata**

**API Endpoints:**
- `POST /api/langgraph-agent-routing` - Main routing endpoint (requires auth)
- `GET /health` - Health check
- `GET /` - System information

**Example API call:**
```bash
curl -X POST http://localhost:8040/api/langgraph-agent-routing \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "query": "What are the latest AI developments?",
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
VITE_AGENT_ENDPOINT=http://localhost:8040/api/langgraph-agent-routing
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
- **Intelligent routing indicators**
- **Clean, simple interface**
- **Session management**

## Routing Logic

The router agent analyzes queries and routes to:

### Web Search (`web_search`)
- Current events and news
- General information requiring web search
- Research topics and trends
- **Example**: "What's the latest AI news?"

### Email Search (`email_search`)
- Finding emails and conversations
- Searching inbox content
- Email-related queries
- **Example**: "Find emails from John about the project"

### RAG Search (`rag_search`)
- Document and knowledge base queries
- Company policies and procedures
- Internal documentation
- **Example**: "What does our policy say about remote work?"

### Fallback (`fallback`)
- General assistant queries
- Unclear or ambiguous requests
- Personal questions
- **Example**: "How are you today?"

## Response Format

All interfaces return responses with routing metadata:

```json
{
  "text": "Based on the latest web search results, AI developments in 2024 include...",
  "session_id": "session789",
  "routing_decision": "web_search",
  "agent_type": "web_search",
  "streaming_success": true,
  "complete": true
}
```

## System Components

### Agents (`agents/`)
- **Router Agent**: Lightweight routing decisions with minimal dependencies
- **Web Search Agent**: Brave API integration for web content
- **Email Search Agent**: Gmail readonly integration for email search
- **RAG Search Agent**: Document search with vector embeddings
- **Dependencies**: Shared dependency injection patterns

### Tools (`tools/`)
- **Web Tools**: Brave API search with error handling
- **Email Tools**: Gmail readonly search and content retrieval
- **RAG Tools**: Document retrieval and embedding search

### Workflow (`graph/`)
- **State Management**: Router state for workflow coordination
- **Workflow Orchestration**: LangGraph-based routing and execution

### API (`api/`)
- **Models**: Pydantic models for requests/responses
- **Endpoints**: FastAPI endpoints with authentication
- **Streaming**: Real-time response streaming utilities
- **Database Utils**: Supabase integration for conversations

## Gmail Configuration

**Important**: This system uses readonly Gmail scope for security.

1. **Set up Gmail API credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable Gmail API
   - Create OAuth2 credentials
   - Download `credentials.json`

2. **Ensure readonly scope**:
   ```
   https://www.googleapis.com/auth/gmail.readonly
   ```

3. **Place credentials**:
   ```bash
   mkdir credentials
   cp path/to/credentials.json credentials/
   ```

## Observability & Monitoring

The system includes **LangFuse integration** for comprehensive observability:

### LangFuse Features
- **Complete Routing Tracing**: Full visibility into routing decisions and agent execution
- **Cost Analysis**: Track routing efficiency and agent usage patterns
- **Performance Metrics**: Response times and success rates per agent type
- **User & Session Tracking**: Analyze routing patterns by user
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
pytest tests/test_router_agent.py -v
pytest tests/test_web_agent.py -v
pytest tests/test_email_agent.py -v
pytest tests/test_rag_agent.py -v

# Run with coverage
pytest tests/ --cov=agents --cov=tools --cov=graph --cov=api
```

### Project Structure

```
agents/
├── __init__.py
├── deps.py                 # Dependency injection patterns
├── prompts.py             # Centralized system prompts
├── router_agent.py        # Lightweight routing agent
├── web_search_agent.py    # Brave API web search
├── email_search_agent.py  # Gmail readonly search
└── rag_search_agent.py    # Document search agent

tools/
├── __init__.py
├── web_tools.py           # Brave API integration
├── email_tools.py         # Gmail readonly tools
└── rag_tools.py          # Document search tools

graph/
├── __init__.py
├── state.py              # Router state management
└── workflow.py           # LangGraph routing workflow

api/
├── __init__.py
├── endpoints.py          # FastAPI server with routing
├── models.py            # Pydantic models
├── streaming.py         # Streaming utilities
└── db_utils.py          # Supabase integration

tests/
├── __init__.py
├── test_router_agent.py
├── test_web_agent.py
├── test_email_agent.py
├── test_rag_agent.py
└── test_workflow.py

streamlit_app.py          # Streamlit interface
requirements.txt          # Dependencies
.env.example             # Environment template
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and virtual environment is activated
2. **Environment Variables**: Check `.env` file configuration
3. **Supabase Connection**: Verify Supabase credentials and connection
4. **Brave API**: Verify Brave Search API key is valid
5. **Gmail Setup**: Ensure OAuth2 credentials and readonly scope configuration
6. **Port Conflicts**: Default port is 8002 for the API server

### Debug Mode

Enable debug output:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### Routing Issues

Check routing decisions:
- **Web queries**: Should include current events, news, research
- **Email queries**: Should mention emails, inbox, messages, conversations
- **RAG queries**: Should mention documents, policies, knowledge base
- **Fallback**: General or unclear queries

## Cost Optimization Notes

- **Router Efficiency**: Minimal token usage for routing decisions
- **Agent Specialization**: Only load dependencies when agent is selected
- **Streaming Strategy**: Reduce perceived latency with real-time responses
- **Conditional Execution**: No unnecessary agent calls or tool loading

This architecture provides both cost efficiency and response quality by routing intelligently to specialized agents.