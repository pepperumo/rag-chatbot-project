# Multi-Agent Research & Email System

A production-ready multi-agent system built with Pydantic AI that combines web research capabilities with intelligent email drafting. The system demonstrates two advanced multi-agent patterns: **Agent-as-Tool** and **Agent Handoff**, with intuitive Streamlit web interfaces for easy interaction.

Built with:

- **Pydantic AI** for the AI Agent Framework
- **Brave Search API** for web research
- **Gmail API** for email draft creation
- **Streamlit** for modern web-based user interfaces
- **Real-time streaming** for responsive user experience
- **Comprehensive Testing** with pytest and coverage

## Overview

This system includes two main AI agents that collaborate to provide intelligent research and communication capabilities:

1. **Research Agent**: Conducts web searches using Brave Search API and handles email requests
2. **Email Draft Agent**: Creates professional Gmail drafts based on research findings and context
3. **Two Collaboration Patterns**: Agent-as-Tool (sub-agent) and Agent Handoff approaches
4. **Two Streamlit Interfaces**: Web-based UIs for both collaboration patterns with real-time streaming

## Agent Collaboration Patterns

### 1. Agent-as-Tool Pattern (`agents_delegation/`)

In this pattern, the Email Agent is invoked as a tool by the Research Agent:

- The Research Agent maintains control throughout the interaction
- Email creation is a function call within the Research Agent's workflow
- The Research Agent provides the final response to the user
- Best for: Workflows where the primary agent needs to maintain context and control

### 2. Agent Handoff Pattern (`agents_handoff/`)

In this pattern, the Research Agent completely hands off control to the Email Agent:

- Uses Pydantic AI's Union output types for true handoff
- The Email Agent takes over and provides the final response
- Control does NOT return to the Research Agent
- Best for: Clear task delegation where specialized agents handle specific domains

### When to Use Each Pattern

**Use Agent-as-Tool when:**
- You need the primary agent to maintain conversation context
- Multiple sub-tasks need coordination by a primary agent
- The response requires synthesis from multiple agent actions
- You want centralized error handling and recovery

**Use Agent Handoff when:**
- Tasks have clear domain boundaries (research vs. email)
- You want specialized agents to own their responses
- Simpler architecture with less coupling is preferred
- Each agent should be independently responsible for its domain

## Prerequisites

- Python 3.11 or higher
- Gmail account with API access
- Brave Search API key
- LLM Provider API key (OpenAI, Anthropic, etc.)

## Installation

### 1. Navigate to this directory

```bash
cd 7_Agent_Architecture/7.3-MultiAgentIntro
```

### 2. Set up a virtual environment

```bash
# Create and activate virtual environment
python -m venv venv       # python3 on Linux
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate     # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This includes all necessary packages:
- `streamlit` for the web interfaces
- `pydantic-ai` for the agent framework
- `httpx` for API calls
- `google-auth` and related packages for Gmail
- Other dependencies for search and utilities

### 4. Set up Gmail API

#### Step 1: Enable Gmail API
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to APIs & Services > Library
   - Search for "Gmail API" and enable it

#### Step 2: Create OAuth2 Credentials
1. Go to APIs & Services > Credentials
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Desktop Application" as the application type
4. Download the credentials file as `credentials.json`
5. Place `credentials.json` in the `credentials/` directory

### 5. Set up Brave Search API

1. Visit [Brave Search API](https://api.search.brave.com/register)
2. Create an account and get your API key
3. Note: Free tier includes 2,000 requests per month

### 6. Configure environment variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-api-key-here
LLM_MODEL=gpt-4

# Brave Search
BRAVE_API_KEY=BSA-your-brave-search-api-key-here

# Gmail (path to credentials.json)
GMAIL_CREDENTIALS_PATH=./credentials/credentials.json

# Application
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=false
```

## Quick Start

### 1. Launch the Streamlit Interface

The system provides two Streamlit web interfaces for different agent collaboration patterns:

#### Agent-as-Tool (Delegation) Pattern Interface
```bash
streamlit run streamlit_ui_tool_subagent.py
```

This interface features:
- The Research Agent maintains control throughout the interaction
- Email creation is handled as a tool within the Research Agent's workflow
- Real-time streaming of responses including tool usage
- Persistent conversation history

#### Agent Handoff Pattern Interface
```bash
streamlit run streamlit_ui_agent_handoff.py
```

This interface features:
- Automatic handoff to the Email Agent when email tasks are detected
- The Email Agent takes complete control and provides the final response
- Seamless streaming across agent transitions
- Clean separation of agent responsibilities

### 2. First Run Authentication

When you first use the email functionality, the system will open a web browser for Gmail OAuth2 authentication:

1. Click on any email-related action in the Streamlit interface
2. Your browser will open for Gmail authentication
3. Sign in to your Gmail account
4. Grant permission for email composition and sending
5. The authentication token will be saved locally

### 3. Using the Streamlit Interfaces

Both interfaces provide a clean, modern chat experience:

#### Agent-as-Tool Interface Example

1. Open the interface at `http://localhost:8501`
2. You'll see the title "🔬 Original Research Agent"
3. Type your query in the chat input, for example:
   - "Research the latest developments in AI safety"
   - "Create an email draft about quantum computing to colleague@company.com"
4. Watch the response stream in real-time
5. The Research Agent will handle everything, using tools as needed

#### Agent Handoff Interface Example

1. Open the interface at `http://localhost:8501`
2. You'll see the title "🔬 Multi-Agent Research & Email System (with Handoffs)"
3. Type your query in the chat input, for example:
   - "Create an email to john@example.com about AI safety developments"
   - "Research renewable energy and draft an email summary"
4. Watch as the Research Agent automatically hands off to the Email Agent
5. The appropriate agent will handle each part of your request

### 4. Interface Features

Both Streamlit interfaces include:

- **Real-time Streaming**: See responses as they're generated
- **Conversation History**: Full chat history maintained during your session
- **Configuration Display**: View current LLM settings in the sidebar
- **Session Management**: Unique session IDs for each conversation
- **Error Handling**: Clear error messages if something goes wrong
- **Responsive Design**: Works on desktop and mobile browsers

## System Architecture

### Multi-Agent Design

The system implements two distinct patterns for agent collaboration, both accessible through modern Streamlit web interfaces:

#### Agent-as-Tool Pattern (`streamlit_ui_tool_subagent.py`)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│  Research Agent │◄───┤ Streamlit Web UI │    │ Email Agent     │
│                 │    │                  │    │  (as tool)      │
│ • Brave Search  │    │ • Chat Interface │    │ • Gmail API     │
│ • Email Tool    │    │ • Real-time      │    │ • Draft Creation│
│ • Coordination  │    │   Streaming      │    │ • Returns to    │
│                 │    │ • Session State  │    │   Research Agent│
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                                              ▲
        │                                              │
        └──────────── Invokes as Tool ─────────────────┘
```

In this pattern:
- User interacts with a clean Streamlit chat interface
- Research Agent maintains control throughout the conversation
- Email creation is a tool call that returns control to Research Agent
- All responses stream in real-time to the web UI

#### Agent Handoff Pattern (`streamlit_ui_agent_handoff.py`)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│  Research Agent │◄───┤ Streamlit Web UI │───►│ Email Agent     │
│                 │    │                  │    │  (handoff)      │
│ • Brave Search  │    │ • Chat Interface │    │ • Gmail API     │
│ • Handoff Logic │    │ • Seamless       │    │ • Takes Control │
│ • Union Output  │    │   Transitions    │    │ • Final Response│
│                 │    │ • Auto-detection │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                                              ▲
        │                                              │
        └────────── Complete Handoff ──────────────────┘
```

In this pattern:
- User interacts with the same familiar Streamlit interface
- Research Agent automatically detects email requests
- Control is completely handed off to the Email Agent
- The UI seamlessly streams responses from whichever agent is active

### Key Features

- **Dual Collaboration Patterns**: Both Agent-as-Tool and Agent Handoff implementations
- **Token Tracking**: Proper usage tracking across agent invocations
- **Streaming Responses**: Real-time CLI output with tool visibility
- **Error Handling**: Comprehensive error handling and retry logic
- **Configuration Management**: Flexible LLM provider support
- **OAuth2 Integration**: Secure Gmail authentication flow

## Project Structure

```
7.3-MultiAgentIntro/
├── agents/                     # Agent-as-Tool implementation
│   ├── __init__.py
│   ├── models.py              # Pydantic data models
│   ├── providers.py           # LLM provider configuration
│   ├── research_agent.py      # Research agent with email tool
│   ├── email_agent.py         # Email agent (invoked as tool)
│   └── tools.py               # Shared tool implementations
├── agents_handoff/            # Agent Handoff implementation
│   ├── __init__.py
│   ├── research_agent.py      # Research agent with handoff capability
│   ├── email_agent.py         # Email agent (receives handoff)
│   ├── cli_interface.py       # CLI for handoff pattern
│   └── models.py              # Data models for handoff
├── config/                    # Configuration management
│   ├── __init__.py
│   └── settings.py            # Environment settings
├── tests/                     # Comprehensive test suite
│   ├── __init__.py
│   ├── test_research_agent.py
│   ├── test_brave_search.py
│   ├── test_gmail_tool.py
│   ├── test_handoff_*.py      # Handoff pattern tests
│   └── test_dotenv_integration.py
├── credentials/               # OAuth2 credentials (gitignored)
│   └── .gitkeep
├── streamlit_ui_tool_subagent.py    # 🌐 Streamlit UI for Agent-as-Tool pattern
├── streamlit_ui_agent_handoff.py    # 🌐 Streamlit UI for Agent Handoff pattern
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Advanced Usage

### Custom LLM Providers

The system supports multiple LLM providers. Configure in your `.env`:

```bash
# OpenAI (default)
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-key
LLM_MODEL=gpt-4

# Anthropic Claude
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-your-key
LLM_MODEL=claude-3-opus-20240229

# Local Ollama
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama2
```

### Running Multiple Streamlit Apps

If you want to run both interfaces simultaneously for comparison:

```bash
# Terminal 1 - Agent-as-Tool Interface
streamlit run streamlit_ui_tool_subagent.py --server.port 8501

# Terminal 2 - Agent Handoff Interface
streamlit run streamlit_ui_agent_handoff.py --server.port 8502
```

Now you can access:
- Agent-as-Tool: `http://localhost:8501`
- Agent Handoff: `http://localhost:8502`

### Customizing the Streamlit Interfaces

Both interfaces can be customized by modifying the respective files:

#### Customize UI Appearance
```python
# In either streamlit_ui_*.py file
st.set_page_config(
    page_title="Your Custom Title",
    page_icon="🤖",
    layout="wide",  # or "centered"
    initial_sidebar_state="expanded"
)
```

#### Add Custom Sidebar Features
```python
# Add to the sidebar section
st.sidebar.header("Quick Actions")
if st.sidebar.button("Clear History"):
    st.session_state.messages = []
    st.rerun()
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Use a different port
   streamlit run streamlit_ui_tool_subagent.py --server.port 8503
   ```

2. **Gmail Authentication Issues**
   - Delete `credentials/token.json` and re-authenticate
   - Ensure `credentials.json` is in the correct location
   - Check that Gmail API is enabled in Google Cloud Console

3. **Streaming Not Working**
   - Ensure you're using a compatible LLM provider
   - Check browser console for WebSocket errors
   - Try refreshing the page

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=agents --cov=agents_handoff --cov-report=html

# Run specific test files
pytest tests/test_research_agent.py -v
pytest tests/test_handoff_integration.py -v
```
