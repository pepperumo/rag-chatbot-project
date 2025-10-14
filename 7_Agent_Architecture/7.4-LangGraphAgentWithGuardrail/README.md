# RAG Guardrail Agent System

A multi-agent RAG system with citation validation using Pydantic AI and LangGraph. This system ensures all RAG responses include proper citations that are validated for accuracy and relevance.

## Features

- **Two-Agent Architecture**: Primary RAG agent → Guardrail agent → Validated output
- **Citation Enforcement**: Automatic validation of Google Drive document citations
- **Feedback Loop**: Failed validation triggers correction attempts (up to 3 iterations)
- **Streaming Support**: Real-time response streaming with validation feedback
- **Multiple Interfaces**: Streamlit UI, FastAPI with authentication, and simple API
- **Modular Design**: Separate concerns between agents, tools, and workflow orchestration

## Architecture

```
User Query → Primary Agent → Guardrail Agent → Validated Response
                ↑                 ↓
                └─── Feedback ─────┘
```

1. **Primary Agent**: Performs RAG queries and generates responses with citations
2. **Guardrail Agent**: Validates citations and content relevance
3. **Feedback Loop**: Invalid citations trigger correction attempts (max 3 iterations)

## Installation

1. **Navigate to this directory**:

```bash
cd 7_Agent_Architecture/7.4-LangGraphAgentWithGuardrail
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
LLM_CHOICE=gpt-4
LLM_BASE_URL=https://api.openai.com/v1

# ===== Supabase Configuration =====
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key

# ===== LangFuse Configuration (Optional) =====
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com

# ===== Optional Configuration =====
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=false
PORT=8000
```

**Required Services:**
- **OpenAI API**: For LLM and embedding models
- **Supabase**: For document storage and conversation history

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

**API Endpoints:**
- `POST /api/langgraph-rag-agents` - Main RAG query endpoint (requires auth)
- `GET /health` - Health check
- `GET /` - System information

**Example API call:**
```bash
curl -X POST http://localhost:8040/api/langgraph-rag-agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "query": "What are the key findings about AI safety?",
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
VITE_AGENT_ENDPOINT=http://localhost:8040/api/langgraph-rag-agents
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
- **Citation validation indicators**
- **Clean, simple interface**
- **Session management**

## Response Format

All interfaces return responses with:

```json
{
  "text": "Based on the research data, AI safety requires robust testing protocols. Source: https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/",
  "citations": ["https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/"],
  "validation_passed": true,
  "iterations": 1
}
```

## System Components

### Agents (`agents/`)
- **Primary Agent**: RAG-enabled agent that generates responses with required citations
- **Guardrail Agent**: Validates citations and content relevance
- **Dependencies**: Shared dependency injection for agents

### Tools (`tools/`)
- **RAG Tools**: Document retrieval and content access from Supabase
- **Validation Tools**: Citation extraction and validation

### Workflow (`graph/`)
- **State Management**: Manages workflow state and message history
- **Workflow Orchestration**: LangGraph-based agent coordination

### API (`api/`)
- **Models**: Pydantic models for requests/responses
- **Endpoints**: Full-featured FastAPI endpoints with auth
- **Streaming**: Real-time response streaming utilities
- **Database Utils**: Supabase integration for conversations

### Interfaces
- **Streamlit App**: Simple web interface (`streamlit_app.py`)
- **Simple API**: Basic FastAPI server (`main.py`)
- **Full API**: Advanced FastAPI server (`api/endpoints.py`)

## Citation Format

The system enforces this citation format:
```
Source: https://docs.google.com/document/d/[file_id]/
```

**Example Response**:
```
Based on the research data, AI safety requires robust testing protocols. 
Source: https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/

Additionally, continuous monitoring is essential for deployment safety.
Source: https://docs.google.com/document/d/9i8h7g6f5e4d3c2b1a0z/
```

## Validation Process

1. **URL Extraction**: Extract Google Drive URLs using regex
2. **Existence Check**: Verify documents exist in knowledge base
3. **Relevance Check**: Validate content relevance using embeddings
4. **Feedback Generation**: Provide specific feedback for corrections

## Observability & Monitoring

The system includes **LangFuse integration** for comprehensive observability of the entire multi-agent workflow:

### LangFuse Features
- **Complete LangGraph Tracing**: Full visibility into the workflow execution, including:
  - Primary agent RAG queries and responses
  - Guardrail validation steps and decisions
  - Iteration cycles and feedback loops
  - Tool usage and document retrievals
- **Pydantic AI Instrumentation**: Automatic tracing of both agents with `instrument=True`
- **User & Session Tracking**: All traces include user IDs and session IDs for analysis
- **Optional Setup**: Works seamlessly when configured, gracefully disabled when not

### Setup LangFuse (Optional)
1. Sign up at [LangFuse Cloud](https://us.cloud.langfuse.com/) or [self-host](https://langfuse.com/self-hosting)
2. Create a new project and get your keys
3. Add to your `.env` file:
   ```env
   LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
   LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
   LANGFUSE_HOST=your-langfuse-url
   ```
4. Restart your application - tracing will automatically begin

### What You'll See in LangFuse
- **Trace Timeline**: Complete workflow execution from user query to final response
- **Agent Interactions**: Each agent's input, processing, and output
- **Validation Cycles**: How many iterations were needed and why
- **Performance Metrics**: Response times, token usage, and success rates
- **Error Tracking**: Failed validations and their feedback
- **User Analytics**: Usage patterns and conversation flows

The system continues to work perfectly without LangFuse - observability is purely additive.

## Development

### Running Tests

```bash
# Run all tests
source venv_linux/bin/activate  # or venv_windows\Scripts\activate
pytest tests/ -v

# Run specific test file
pytest tests/test_primary_agent.py -v

# Run with coverage
pytest tests/ --cov=agents --cov=tools --cov=graph --cov=api
```

### Project Structure

```
agents/
├── __init__.py
├── deps.py              # Dependency injection
├── primary_agent.py     # RAG agent with citation requirements
└── guardrail_agent.py   # Citation validation agent

tools/
├── __init__.py
├── rag_tools.py         # RAG query tools
└── validation_tools.py  # Citation validation tools

graph/
├── __init__.py
├── state.py            # Workflow state management
└── workflow.py         # LangGraph orchestration

api/
├── __init__.py
├── endpoints.py        # Full FastAPI server with auth
├── models.py          # Pydantic models
├── streaming.py       # Streaming utilities
└── db_utils.py        # Supabase integration

tests/
├── __init__.py
├── test_primary_agent.py
├── test_guardrail_agent.py
├── test_workflow.py
└── test_api_integration.py

streamlit_app.py        # Simple Streamlit interface
main.py                 # Simple API server
requirements.txt        # Dependencies
.env.example           # Environment template
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and virtual environment is activated
2. **Environment Variables**: Check `.env` file configuration
3. **Supabase Connection**: Verify Supabase credentials and connection
4. **API Rate Limits**: Check OpenAI API quotas and rate limits
5. **Port Conflicts**: Default port based on README instructions for the API is 8040

### Debug Mode

Enable debug output:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```
