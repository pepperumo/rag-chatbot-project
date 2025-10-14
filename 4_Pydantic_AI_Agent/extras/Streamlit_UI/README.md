# Streamlit UI for Pydantic AI Agent

This directory contains Streamlit-based user interfaces for the Pydantic AI web search agent. There are two versions available:

1. `streamlit_ui_simple.py` - A basic implementation that displays complete responses
2. `streamlit_ui_streaming.py` - An enhanced version that streams tokens in real-time

Both UIs provide a chat interface to interact with the Pydantic AI agent, which can search the web using either Brave Search API or SearXNG based on your environment configuration.

## Prerequisites

- Python 3.11+
- Streamlit
- Pydantic AI
- Access to either Brave Search API or SearXNG

## Setup Instructions

### 1. Set up the virtual environment

```bash
# Navigate to the Streamlit_UI directory
cd extras/Streamlit_UI

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `Basic_Pydantic_AI_Agent` directory with the following variables:

```
# Set this to either openai, openrouter, or ollama
LLM_PROVIDER=openai

# Base URL for the OpenAI compatible instance
LLM_BASE_URL=https://api.openai.com/v1

# API key for OpenAI or OpenRouter (no need to set for Ollama)
LLM_API_KEY=your_api_key_here

# The LLM you want to use for the agents
LLM_CHOICE=gpt-4o-mini

# Set your Brave API key if using Brave for agent web search (leave empty if using SearXNG)
BRAVE_API_KEY=your_brave_api_key_here

# Set the SearXNG endpoint if using SearXNG for agent web search (leave empty if using Brave)
SEARXNG_BASE_URL=http://your-searxng-instance.com
```

**Note:** You must set either `BRAVE_API_KEY` or `SEARXNG_BASE_URL` for the web search functionality to work. If both are set, the agent will prioritize using Brave Search.

### 3. Running the Streamlit UI

Make sure your virtual environment is activated, then run one of the following commands:

```bash
# Run the simple UI (no streaming)
streamlit run streamlit_ui_simple.py

# OR run the streaming UI
streamlit run streamlit_ui_streaming.py
```

The Streamlit app will start and open in your default web browser, typically at http://localhost:8501.

## UI Features

### Simple UI (`streamlit_ui_simple.py`)

- Basic chat interface
- Displays complete responses after processing
- Shows user and assistant messages
- Maintains conversation history during the session

### Streaming UI (`streamlit_ui_streaming.py`)

- Enhanced chat interface with real-time streaming
- Shows tokens as they are generated
- Provides a more interactive experience
- Maintains conversation history during the session
