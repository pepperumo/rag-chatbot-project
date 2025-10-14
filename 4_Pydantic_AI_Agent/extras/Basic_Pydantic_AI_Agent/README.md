# Pydantic AI Web Search Agent

A versatile web search agent built with Pydantic AI that can search the web using either Brave Search API or SearXNG based on environment configuration. Interact with the agent through a simple command-line interface.

## Features

- Search the web using Brave Search API or SearXNG
- Configurable search provider through environment variables
- Simple command-line interface for easy interaction
- Comprehensive error handling and response formatting
- Support for multiple LLM providers (OpenAI, OpenRouter, Ollama)

## Project Structure

```
Basic_Pydantic_AI_Agent/
├── .env.example          # Example environment variables
├── PLANNING.md           # Project planning document
├── README.md             # This file
├── TASK.md               # Task list and progress tracking
└── src/                  # Source code
    ├── __init__.py       # Package initialization
    ├── agent.py          # Main agent implementation
    ├── cli.py            # Command-line interface
    ├── prompt.py         # System prompts for the agent
    ├── tools.py          # Web search tools implementation
    └── tests/            # Unit tests
        ├── __init__.py
        └── test_tools.py # Tests for the tools module
```

## Prerequisites

- Python 3.10+
- Brave Search API key (for Brave search) or SearXNG instance (for SearXNG search)
- OpenAI API key, OpenRouter API key, or Ollama instance (depending on chosen LLM provider)

## Installation

1. Change your directory after cloning this repo:

```bash
cd Basic_Pydantic_AI_Agent
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
```

5. Edit the `.env` file with your configuration:

```
# Set this to either openai, openrouter, or ollama
LLM_PROVIDER=openai

# Base URL for the OpenAI compatible instance
LLM_BASE_URL=https://api.openai.com/v1

# API key for OpenAI or OpenRouter (no need to set for Ollama)
LLM_API_KEY=your_api_key_here

# The LLM you want to use for the agents.
LLM_CHOICE=gpt-4o-mini

# Set your Brave API key if using Brave for agent web search (leave empty if using SearXNG)
BRAVE_API_KEY=your_brave_api_key_here

# Set the SearXNG endpoint if using SearXNG for agent web search (leave empty if using Brave)
SEARXNG_BASE_URL=https://your-searxng-instance.com
```

## Usage

### Using the Command-Line Interface

To start the CLI:

```bash
# From the project root
python -m src.cli

# Or from the src directory
cd src
python -m cli
```

Once started, you'll see a prompt where you can enter search queries:

```
Web Search Agent CLI
--------------------
Type 'exit' or 'quit' to exit the program.
Type 'help' for help.

Using Brave Search API for web searches

Enter your search query: What is Pydantic AI?

Searching...

Response:
[Agent's response with search results]
```

### CLI Commands

- Enter any text to search the web for that query
- Type `help` to display help information
- Type `exit` or `quit` to exit the program
- Press `Ctrl+C` to force exit

## Configuration Options

### LLM Providers

- **OpenAI**: Set `LLM_PROVIDER=openai`, `LLM_API_KEY=your_api_key`, and `LLM_CHOICE=model_name` (e.g., `gpt-4o-mini`)
- **OpenRouter**: Set `LLM_PROVIDER=openrouter`, `LLM_API_KEY=your_api_key`, and `LLM_CHOICE=model_name`
- **Ollama**: Set `LLM_PROVIDER=ollama`, `LLM_BASE_URL=http://localhost:11434` (or your Ollama URL), and `LLM_CHOICE=model_name` (e.g., `llama3`)

### Search Providers

- **Brave Search**: Set `BRAVE_API_KEY=your_api_key` and leave `SEARXNG_BASE_URL` empty
- **SearXNG**: Set `SEARXNG_BASE_URL=your_searxng_url` and leave `BRAVE_API_KEY` empty

## Running Tests

To run the unit tests:

```bash
cd src
pytest tests/
```

## Troubleshooting

### Import Errors

- **Issue**: `ModuleNotFoundError` when running the agent or tests
- **Solution**: Make sure you're running commands from the correct directory. For relative imports to work, run commands from the project root or use the `-m` flag (e.g., `python -m src.cli`)

### API Key Issues

- **Issue**: `Error searching the web with Brave: HTTP Error`
- **Solution**: Verify your Brave API key is correct and not expired

### SearXNG Connection Issues

- **Issue**: `Error searching the web with SearXNG: Connection Error`
- **Solution**: Check that your SearXNG instance is running and accessible from your environment

### LLM Provider Configuration

- **Issue**: `Error: No LLM provider configured`
- **Solution**: Make sure your `.env` file has the correct LLM_PROVIDER, LLM_BASE_URL, and LLM_API_KEY values

## Dependencies

- pydantic-ai: The core agent framework
- python-dotenv: For environment variable management
- pytest: For unit testing
