# Dynamous AI Agent Mastery - Module 5: Agent Application

A full-stack application that combines a React frontend with a FastAPI backend to create a production-ready AI agent interface. This module builds upon the Pydantic AI agent from Module 4, transforming it into a complete web application with a modern UI, conversation history, and real-time streaming responses. Optionally, you can use one of the n8n agents built in module 3 as well - see n8n_apis/.

## Project Overview

This agentic application demonstrates how to:

1. Build a production-ready AI agent API with FastAPI
2. Create a modern React frontend with Shadcn UI components
3. Implement real-time streaming of AI responses
4. Store and retrieve conversation history
5. Manage user sessions and conversations

## Project Structure

```
5_Agent_Application/
├── backend/                    # FastAPI backend
│   ├── agent_api.py            # Main API endpoint for the AI agent
│   ├── db_utils.py             # Database utility functions
│   ├── requirements.txt        # Backend dependencies
│   └── sql/                    # SQL scripts for database setup
│
└── frontend/                   # React frontend (Vite + TypeScript)
    ├── src/                    # Frontend source code
    ├── package.json            # Frontend dependencies
    └── .env.example            # Example environment variables that can be exposed in the frontend
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Supabase (locally hosted or managed)
- Module 4 setup completed (the backend API uses the agent from Module 4)
- Optional - you can use n8n instead of Python if you wish for the backend, see n8n_apis/

### Backend Setup

1. Navigate to the backend directory:

```bash
cd 5_Agent_Application/backend
```

2. Create and activate a virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate
```

3. Install the backend dependencies:

```bash
pip install -r requirements.txt
```

4. **Important**: Make sure Module 4 is properly set up:
   - The backend uses the agent from Module 4
   - Ensure the `.env` file in the `4_Pydantic_AI_Agent` directory is configured correctly
   - All Module 4 dependencies must be installed

5. Start the FastAPI server:

```bash
uvicorn agent_api:app --reload --port 8001
```

The API will be available at `http://localhost:8001` by default, this port might change if 8001 is already in use.

Port 8001 is specified because port 8000 is the default and that is taken by the Supabase dashboard if you are using the local AI package or just self-hosting Supabase.

### Frontend Setup

1. Open a new terminal and navigate to the frontend directory:

```bash
cd 5_Agent_Application/frontend
```

2. Install the frontend dependencies:

```bash
npm install
```

3. Set up the environment variables:

```bash
# On Windows
copy .env.example .env
# On macOS/Linux
# cp .env.example .env
```

4. Open the newly created `.env` file in your editor and update the values:

```
# Supabase credentials
VITE_SUPABASE_URL=https://your-supabase-project-url.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
VITE_AGENT_ENDPOINT=http://localhost:8001/api/pydantic-agent
VITE_ENABLE_STREAMING=true
```

   - `VITE_SUPABASE_URL`: Your Supabase project URL (same as used in Module 4)
   - `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key (same as used in Module 4)
   - `VITE_AGENT_ENDPOINT`: The endpoint for the agent API (either Python with FastAPI or n8n)
   - `VITE_ENABLE_STREAMING`: Keep as `true` to enable real-time streaming of responses for a Python agent. Make sure this is set to false if using an n8n agent!

5. Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:8081` by default.

## How It Works

### Backend

The `agent_api.py` file serves as the main entry point for the backend. It:

1. Imports the AI agent from Module 4 (`4_Pydantic_AI_Agent/agent.py`)
2. Uses the environment variables from Module 4's `.env` file
3. Provides a FastAPI endpoint at `/api/pydantic-agent` for agent interactions
4. Implements streaming responses for real-time AI output
5. Manages conversation history in the database

Key features:
- Real-time streaming of AI responses
- Automatic conversation title generation
- Session management for multiple conversations
- Database storage of conversation history

### Frontend

The React frontend provides a modern user interface built with:
- Vite for fast development and building
- React for UI components
- Shadcn UI for a polished design system
- TypeScript for type safety
- Supabase for database interactions

Key features:
- Real-time streaming of AI responses
- Conversation history management
- Modern, responsive UI
- Code syntax highlighting
- Markdown rendering
- Admin dashboard to manage conversations and users

### How They Work Together

1. The frontend sends requests to the backend API endpoint
2. The backend processes these requests using the AI agent from Module 4
3. The agent's responses are streamed back to the frontend in real-time
4. Conversation history is stored in the database and can be retrieved later

## Environment Configuration

The backend uses the same environment variables as Module 4. Make sure the `.env` file in the `4_Pydantic_AI_Agent` directory is properly configured with:

- LLM configuration (provider, API key, model choice)
- Embedding configuration
- Database configuration (Supabase)
- Web search configuration (Brave API or SearXNG)

## Database Setup

The application uses Supabase for database storage. The SQL scripts in the `backend/sql` directory create the necessary tables for:

- Storing conversations
- Storing messages within conversations
- Managing user sessions

## Development Notes

- The backend imports the agent from Module 4, so any changes to the agent in Module 4 will affect this application
- The frontend communicates with the backend through the `/api/pydantic-agent` endpoint
- Both the frontend and backend must be running simultaneously for the application to work

## Troubleshooting

- If you encounter import errors in the backend, ensure that Module 4 is properly set up and its dependencies are installed
- If the frontend can't connect to the backend, check that both servers are running and the API endpoint is correct
- For database issues, verify your Supabase configuration in the Module 4 `.env` file and make sure you are using the same Supabase project for the backend and the frontend!
