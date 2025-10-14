## FEATURE:

Let's build an AI agent with Pydantic AI and LangGraph. I want to create a RAG Pydantic AI agent with a guardrail system. The primary agent will have RAG tools to search the knowledge base and will be given file IDs so it can cite its sources. The primary agent needs to have a part of the system prompt that instructs it to always cite sources when it retrieves knowledge from the knowledge base. This agent will run as a node in the LangGraph implementation. Then, the guardrail agent will run as a node after, so the flow is primary agent -> guardrail agent -> final output. The guardrail agent will check the output of the primary agent and ensure it cites sources. Then, it will also use a tool to pull the contents of the files cited to make sure the content in the files is actually useful for answering the question based on the answer the primary agent gave. If the primary agent didn't cite sources or what it cited was irrelevant, then the control will be passed to the primary agent to correct itself. The LangGraph state for the feedback will be updated by the guardrail agent to include context for what exactly went wrong and how to fix it.

## EXAMPLES:

`agent.py` and `tools.py` - A reference implementation of the primary agent, including tools for RAG. It's important to note that this agent is much more than we need for our agents, but see the tools for RAG here, specifically - retrieve_relevant_documents_tool, list_documents_tool, and get_document_content_tool. These are the tools that need to be available for the primary agent, and then get_document_content_tool is what needs to be available for the guardrail agent.

`agent_api.py` - A reference for how to stream output from Pydantic AI agents with .iter. Note that this file is pretty comprehensive for an agent API endpoint but the thing we really care about how is how the agent is invoked and the parameters + setting up the dependencies for the Pydantic AI agent.

`clients.py` - A reference for how to set up clients for the primary agent and guardrail agent. See how the environment variables are used here to set up the clients. It will be very import for you to document these clearly. .env.example is already made for you!

`archon_graph.py` - A reference (not super related but still LangGraph) for how to build LangGraph graphs that use Pydantic AI agents. The way the agents are invoked here isn't how we want to do that - that is in agent_api.py - but you can see how we create state in LangGraph, define nodes, connect them together, stream output, etc. Use this + Archon for the LangGraph documentation to understand how to build our multi agent workflow here with LangGraph.

## DOCUMENTATION:

Use the Archon MCP server to get up to date documentation for both Pydantic AI and LangGraph.
Make sure you research best practices for building AI agents with Pydantic AI and LangGraph as well.

## OTHER CONSIDERATIONS:

- Include a README with instructions for setup including env vars, configuring the environment, running things, etc.
- Include the project structure in the README.
- Virtual environment has already been set up with the necessary dependencies.
- Use python_dotenv and load_env() for environment variables.
