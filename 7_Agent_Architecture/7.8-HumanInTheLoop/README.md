# Human-in-the-Loop Email Agent System

A sophisticated email management system using Pydantic AI and LangGraph with human-in-the-loop approval for email sending operations. The agent autonomously handles email reading and drafting but requires explicit human approval before sending any email, using LangGraph's interrupt mechanism for state persistence.

## Features

- **Human-in-the-Loop Email Sending**: Autonomous reading and drafting with mandatory approval for sending
- **Real-Time Streaming**: Live token streaming with approval UI integration using Pydantic AI `.run_stream()`
- **LangGraph Interrupt Mechanism**: State persistence across human approval workflows
- **PostgreSQL Checkpointer**: Reliable state management for interrupt resumption
- **Gmail API Integration**: Complete email operations (read, draft, send) with proper OAuth2 scopes
- **Approval Pattern Detection**: Intelligent parsing of "yes-/no-" approval responses
- **Comprehensive Testing**: Full unit and integration test suite covering all components

## Architecture

```
User Query → Email Agent (with streaming)
                     ↓
            [Email Operation Analysis]
                     ↓
    ┌────────────────┼────────────────┐
    ↓                ↓                ↓
Read Inbox     Create Drafts     Request Send
(Autonomous)   (Autonomous)      (Requires Approval)
    ↓                ↓                ↓
    └────────────────┼────────────────┘
                     ↓
            Human Approval (Interrupt)
                     ↓
            [Approved/Declined Decision]
                     ↓
            Send Email / Return to Agent
```

### Human-in-the-Loop Email Flow:
1. **Email Agent**: Analyzes request and performs autonomous operations (read/draft)
2. **Send Detection**: Detects when user wants to send an email
3. **Approval Request**: Interrupts workflow and presents email for human review
4. **State Persistence**: Maintains full context using PostgreSQL checkpointer
5. **Human Decision**: User approves ("yes-feedback") or declines ("no-feedback")
6. **Workflow Resumption**: Continues with sending or returns to agent with feedback

### Key Innovations:
- **Interrupt-Based Approval**: Uses LangGraph's native interrupt mechanism for human input
- **State Persistence**: PostgreSQL checkpointer ensures reliable state across restarts
- **Structured Email Output**: Dual-purpose response with message streaming and email preview
- **Command Resumption**: Seamless workflow continuation with approval decisions

## Installation

1. **Navigate to this directory**:

```bash
cd 7_Agent_Architecture/7.8-HumanInTheLoop
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

# ===== Human-in-the-Loop Configuration =====
# Postgres database URL for LangGraph checkpointer and store
# Format: postgresql://[user]:[password]@[host]:[port]/[database]
# Supabase example (direct connection): postgresql://postgres:password@db.fkfltevvnmzyrcptwlyg.supabase.co:5432/postgres
DATABASE_URL=

# ===== Gmail Configuration =====
# Gmail OAuth2 credentials for human-in-the-loop email management
# Required scopes: gmail.readonly, gmail.compose, gmail.send
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
- **Supabase**: For conversation history and message storage
- **PostgreSQL Database**: For LangGraph checkpointer state persistence
- **Gmail API**: For complete email operations (read, draft, send) with OAuth2

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
- **Human-in-the-loop approval workflow**
- **Real-time streaming responses with approval UI**
- **PostgreSQL checkpointer for state persistence**

**API Endpoints:**
- `POST /api/human-in-the-loop-agent` - Main email agent endpoint with HITL approval (requires auth)
- `GET /health` - Health check
- `GET /` - System information

**Example API call:**
```bash
curl -X POST http://localhost:8040/api/human-in-the-loop-agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "query": "Send an email to colleague@company.com about the project update",
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
VITE_AGENT_ENDPOINT=http://localhost:8040/api/human-in-the-loop-agent
```

4. **Start the frontend**:
```bash
npm run dev
```

5. **Access the interface** at `http://localhost:8080` (or check the terminal for the exact port)

### 🎯 **Streamlit Web Interface** (Quick Testing)

The easiest way to see the human-in-the-loop email agent in action:

```bash
# Make sure you're in the project directory and virtual environment is activated
streamlit run streamlit_app.py
```

- **Real-time streaming email agent responses**
- **Interactive approval workflow visualization**
- **Email preview and approval UI**
- **Clean, intuitive interface**

### Example Queries:

**Email Reading Requests (Autonomous):**
```
"Check my inbox for unread emails"
"Show me emails from john@company.com"
"Find emails about the quarterly report"
"List emails with attachments from this week"
```

**Email Drafting Requests (Autonomous):**
```
"Draft a thank you email to the client"
"Create a follow-up email for the meeting"
"Prepare a professional response to the inquiry"
"Write a draft email about the project update"
```

**Email Sending Requests (Requires Approval):**
```
"Send an email to team@company.com about the meeting"
"Send that draft to the client we just created"
"Send a follow-up email to john@example.com"
"Send the project update email to stakeholders"
```

**General Email Questions:**
```
"How many unread emails do I have?"
"What's the status of my email drafts?"
"Summarize my recent emails from the CEO"
```

## Email Agent Operation Logic

The email agent intelligently determines which operations require human approval:

### Autonomous Operations (No Approval Required)
**Email Reading:**
- Reading inbox emails with optional filtering
- Searching emails by sender, date, or content
- Listing email summaries and metadata
- **Example**: "Check my inbox for emails from john@company.com"

**Email Drafting:**
- Creating draft emails in Gmail
- Preparing email content with proper formatting
- Saving drafts for later review
- **Example**: "Draft a thank you email to the client"

**Email Management:**
- Listing existing draft emails
- Organizing email information
- Providing email statistics
- **Example**: "Show me my draft emails"

### Restricted Operations (Human Approval Required)
**Email Sending:**
- Any request to send an email triggers approval workflow
- Email preview is presented to human for review
- User can approve ("yes-feedback") or decline ("no-feedback")
- **Example**: "Send this email to team@company.com" → Requires approval

## Response Format

The email agent provides streaming responses with approval workflow integration:

### Normal Conversation Response
```json
{
  "text": "I found 5 emails from john@company.com in your inbox...",
  "session_id": "session789",
  "complete": true
}
```

### Email Approval Request
```json
{
  "type": "approval_request",
  "email_preview": {
    "recipients": ["team@company.com"],
    "subject": "Weekly Project Update",
    "body": "Hi team,\n\nHere's our weekly update..."
  }
}
```

### Approval Patterns
- **Approve**: `"yes"` or `"yes-looks great"`
- **Decline**: `"no"` or `"no-please revise the tone"`
- **Feedback**: Anything after `-` is treated as feedback

## System Components

### Email Agent (`agents/email_agent.py`)
- **Pydantic AI Agent**: Core email management with structured output
- **Streaming Support**: Real-time response streaming with `.run_stream()`
- **Structured Output**: EmailAgentDecision model for approval requests
- **Tool Integration**: Gmail tools for read/draft/send operations

### Gmail Tools (`tools/gmail_tools.py`)
- **OAuth2 Authentication**: Secure Gmail API access
- **Read Inbox Tool**: Email retrieval with filtering capabilities
- **Create Draft Tool**: Professional email draft creation
- **Send Email Tool**: Secure email sending with validation
- **List Drafts Tool**: Draft management functionality

### LangGraph Workflow (`graph/workflow.py`)
- **Email Agent Node**: Main processing with send detection
- **Human Approval Node**: Interrupt-based approval mechanism
- **Email Send Node**: Final sending after approval
- **Routing Logic**: Intelligent flow control based on agent decisions

### State Management (`graph/state.py`)
- **EmailAgentState**: Typed state for workflow persistence
- **Approval Fields**: Recipients, subject, body for preview
- **Decision Fields**: Approval status and feedback

## Streaming Architecture

### Email Agent Streaming
```python
async with email_agent.run_stream(query, deps=deps, message_history=history) as result:
    async for partial in result.stream():
        # Stream conversational message
        if partial.get('message'):
            writer(partial['message'])
    
    # Get final structured decision
    decision = await result.get_output()
    if decision.get('request_send'):
        # Trigger approval workflow
        return approval_state
```

### EmailAgentDecision Model
```python
class EmailAgentDecision(TypedDict, total=False):
    message: Optional[str]        # Conversational response (streamed)
    recipients: Optional[List[str]]  # Email recipients
    subject: Optional[str]           # Email subject
    body: Optional[str]              # Email body
    request_send: bool              # True when requesting approval
```

## Development

### Running Tests

```bash
# Run all tests
source venv_linux/bin/activate
pytest tests/ -v

# Test specific components
pytest tests/test_email_agent.py -v
pytest tests/test_workflow_hitl.py -v
pytest tests/test_gmail_tools.py -v

# Run with coverage
pytest tests/ --cov=agents --cov=tools --cov=graph --cov=api
```

### Project Structure

```
agents/
├── __init__.py
├── deps.py                     # Dependency injection for email agent
├── prompts.py                  # Email management system prompt
└── email_agent.py              # Pydantic AI email agent

tools/
├── __init__.py
└── gmail_tools.py              # Complete Gmail API toolkit

graph/
├── __init__.py
├── state.py                    # EmailAgentState management
└── workflow.py                 # Human-in-the-loop workflow

api/
├── __init__.py
├── models.py                   # API request/response models
├── streaming.py                # Streaming utilities
├── db_utils.py                 # Database operations
└── endpoints.py                # FastAPI endpoints

tests/
├── __init__.py
├── test_email_agent.py         # Email agent tests
├── test_gmail_tools.py         # Gmail tools tests
├── test_workflow_hitl.py       # Workflow tests
├── test_api_endpoints.py       # API endpoint tests
├── test_integration_email_flow.py  # Integration tests
└── test_simple_email_logic.py  # Core logic tests

streamlit_app.py               # Streamlit interface
requirements.txt               # Dependencies
.env.example                   # Environment template
```

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure DATABASE_URL is properly configured for checkpointer
2. **Gmail Authentication**: Verify OAuth2 credentials and scopes
3. **Environment Variables**: Check all required variables in `.env`
4. **State Persistence**: Ensure PostgreSQL is running for checkpointer
5. **Approval Pattern**: Use "yes-" or "no-" prefix for feedback

### Debug Mode

Enable debug output:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### Human-in-the-Loop Issues

Check approval workflow:
- **Approval Detection**: Verify "yes-/no-" pattern parsing
- **State Persistence**: Check PostgreSQL checkpointer connection
- **Interrupt Handling**: Ensure LangGraph interrupt mechanism works
- **Command Resumption**: Verify workflow continues after approval

### Gmail API Setup

1. **Create Google Cloud Project**
2. **Enable Gmail API**
3. **Create OAuth2 credentials**
4. **Download credentials.json**
5. **Set required scopes**: `gmail.readonly`, `gmail.compose`, `gmail.send`

## Architecture Evolution

This system represents a focused implementation of human-in-the-loop patterns:

### Traditional Email Automation
- **Full Automation**: All operations without human oversight
- **Security Risk**: Potential for unwanted email sending
- **Limited Control**: No approval mechanism

### Human-in-the-Loop Email Agent
- **Selective Automation**: Autonomous read/draft, manual send approval
- **Security First**: Mandatory approval for all sending operations
- **State Persistence**: Reliable interrupt-based workflow
- **Real-Time Streaming**: Live feedback during processing

The system prioritizes security and user control while maintaining automation efficiency for non-sensitive operations.

## Example Workflow

### Complete Email Approval Flow

**Input:**
```
"Send an email to team@company.com about tomorrow's meeting"
```

**Flow:**
1. **Agent Processing**: Detects send request, creates email draft
2. **Approval Request**: Interrupts workflow, presents email preview
3. **Human Review**: User sees recipients, subject, body
4. **Decision**: User responds "yes-looks good" or "no-please revise"
5. **Workflow Resumption**: Sends email or returns to agent with feedback
6. **Completion**: Confirms successful send or processes revisions

**State Persistence:**
- Workflow state maintained across interrupts
- Conversation history preserved
- Email content persisted for approval
- Seamless resumption after human input

This system demonstrates sophisticated human-AI collaboration while maintaining security and user control over email communications.