## FEATURE:

LangGraph Workflow with Pydantic AI - Human-in-the-Loop Email Agent

Build a LangGraph workflow with a single Pydantic AI agent that manages email operations with human-in-the-loop approval for sending emails. The agent can autonomously read inbox emails and create drafts but requires explicit human approval before sending any email.

**Email Management Agent**: Single intelligent agent handling all email operations through Gmail API. Freely reads inbox emails and creates email drafts, but implements human-in-the-loop pattern requiring user approval for send operations. Uses structured output to communicate both conversational messages and email sending requests that trigger the approval workflow.

**Core Capabilities**: Autonomous inbox reading and analysis, intelligent email drafting with appropriate content and recipients, structured approval flow capturing all email details (recipients, subject, body), and feedback integration when email sending is declined. Normal agent tools for inbox reading and email drafting, human in the loop with special node for sending emails. Draft first then request to send is the flow for this agent and that should be made clear in the system prompt for the agent.

**Workflow Architecture**: 
State Flow: Input → Agent Processing → (Read/Draft Operations OR Send Approval Request) → Human Approval Node → (Send Execution OR Return to Agent) → Final Response

Node Structure: Agent Node (primary email processing), Human-in-the-Loop Node (interrupt-based approval system), Email Send Node (executes sending after approval), and conditional routing between autonomous and approval-required operations.

**Structured Output System**: Agent streams JSON with message field for conversational responses (streamed real-time) and optional email fields (recipients, subject, body, urgency) for send requests. When requesting email approval, populates email fields without message field. When responding conversationally, streams message field while leaving email fields undefined.

**Human-in-the-Loop Implementation**: Agent outputs structured email data and triggers LangGraph interrupt. Workflow pauses at approval node, presenting email details for user confirmation. System accepts approval (yes/no) with optional feedback. Approved emails proceed to send node; declined emails return to agent with feedback for revision. Utilizes LangGraph Command directive for proper workflow resumption after human input, maintaining conversation context throughout.

**State Management**: LangGraph state maintains conversation context, email operation history, and approval status. Email details, user preferences, and conversation history persist across approval cycles, enabling intelligent follow-up actions and consistent user experience.

**Key Innovation - Human-Centric Email Automation**: Balanced approach providing AI assistance while maintaining human oversight for sensitive operations. Users leverage AI for email management while maintaining complete control over outbound communications. Agent handles complex scenarios and understands inbox context while ensuring human review prevents miscommunications. Feedback mechanism creates collaborative email management that improves over time.

**Technical Requirements**: Agent uses LLM model specified by LLM_choice environment variable. Gmail API integration for reading, drafting, and sending with proper authentication. Real-time streaming of conversational messages while maintaining structured output format. LangGraph Command directive implementation in API endpoints for workflow interrupts and resumption.

## EXAMPLES AND DOCUMENTATION

**IMPORTANT FOR HITL: examples/arcade_agent_with_memory.py** - Look at this example only for understanding how to implement human in the loop with the Postgres memory saver with LangGraph. We're going to do the same thing here. You'll also probably need to update the .env.example in this project to include the database URL. So I'll have to include that along with the Supabase URL and Supabase key that we already have in the .env.example, because there's just a different way that we have to implement the connection to the database for the check pointer that we need for the interrupts that we have with human in the loop with LangGraph. 

**7.7-SupervisorAgent** - This is the template in which our current directory is based off of. Just so that you know exactly how to set up an API endpoint to work with LangGraph, how to build the LangGraph workflows, how to work with the user input, how to set up the different nodes, how to create the Pydantic AI agents, this is your reference point. And so you still need to completely overhaul things, just using this as your inspiration, as your structure, as your guidance and documentation. Obviously, a lot is different here because we have different agents. We have a different flow for LangGraph. I will say, though, that the API endpoint will remain pretty much the same besides adding in capabilities for human in the loop with LangGraph. And so it's still important for you to read through all of the files that we have here to understand the agents and the workflows and also to understand the testing and the API. But the API, you probably won't have to change that much. Most of the things, though, including the README, you're going to have to do a very big overhaul on, just using what we already have as your starting point. This starting point also shows you how to use the Brave and Gmail APIs within the agents for web research and email drafting. You will need to add actually sending emails too for the human in the loop component. One thing you will have to change with endpoints.py is adding in the creation of the Postgres connection to pass in to the graph to set as the checkpointer since we need the "with" keyword like you can see in the Arcade example to scope the Postgres connection properly.

Be sure to analyze the existing setup including endpoints.py, workflow.py, and the supervisor agent in supervisor_agent.py to understand the structure and what you are building off of and overhauling.

**API Endpoint Adaptation**: Minimal changes required to existing endpoints.py, primarily adding human-in-the-loop capabilities with LangGraph Command directive for workflow resumption after user approval responses.

**Structured Output Reference**: Follow the existing supervisor agent pattern for streaming structured JSON output, adapting the schema from supervisor delegation fields to email operation fields while maintaining the same real-time message streaming approach.

**Gmail API Integration**: Extend existing Gmail API implementation from email drafting to include inbox reading and email sending capabilities, ensuring proper authentication and error handling throughout the workflow.

## RESEARCH REQUIREMENTS

**LangGraph Human-in-the-Loop**: Comprehensive research on LangGraph interrupt mechanisms, Command directive usage, and workflow resumption patterns for implementing approval-based workflows.

**API Endpoint Updates**: Investigation of endpoints.py modifications required to handle LangGraph workflow resumption using Command directive when processing user approval responses.

**Workflow State Management**: Understanding of LangGraph state persistence and context maintenance across workflow interrupts and resumptions.

**Structured Output Streaming**: Analysis of existing streaming patterns to ensure seamless integration of approval workflow without disrupting real-time conversational responses.

## OTHER CONSIDERATIONS:

- The agent for this LangGraph workflow needs message history.
- Update the project structure in the README and basically do a big overhaul of the README after overhauling the existing codebase for the new graph.
- Virtual environment has already been set up with the necessary dependencies.
- .env.example has already been set up with all necessary values/credentials.
- Use python_dotenv and load_env() for environment variables.
