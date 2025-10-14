## FEATURE:

LangGraph Workflow with Pydantic AI - Parallel Research & Synthesis Agents
Build a LangGraph workflow with 5 agents using Pydantic AI:

Input Guardrail Agent (uses llm_choice_small from .env): Determines if user request is for research/outreach flow via structured output. Routes to either a fallback agent (normal conversation with conversation history and knows how to guide the user to leverage the parallel research workflow) or the parallel research workflow.
SEO Research Agent (Brave API): SEO analysis and keyword research on the target/topic, receives conversation history but doesn't add to it. Outputs SEO research summary to LangGraph state and streams to user.
Social Media Research Agent (Brave API): Social media presence and engagement research. Runs in parallel with other research agents. Receives conversation history, outputs social media research summary to state and streams to user.
Competitor Research Agent (Brave API): Competitive landscape and market positioning research. Runs in parallel with other research agents. Receives conversation history, outputs competitor research summary to state and streams to user.
Synthesis Agent: LLM-only agent (no tools) that waits for all three parallel research agents to complete, then synthesizes all research data from LangGraph state into a comprehensive email draft. Receives conversation history AND adds its response to conversation history as final step. Notifies user to check drafts.

State Flow: Input → Route Decision → (if research flow) [SEO Research Agent || Social Media Research Agent || Competitor Research Agent] → Synthesis Agent.

All three research agents execute in parallel using Brave API, streaming their findings without updating conversation history. The synthesis agent only runs after all three parallel agents complete, then creates the final email draft and updates conversation history.
Models: Small model for guardrail, normal LLM_choice for all three parallel research agents and synthesis agent (and fallback agent) via get_model function in clients.py.

For the 3 research agents, just have a single tool to search with the Brave API like you can see in the existing examples, and then in the system prompts tell the agents how to use this tool to do an initial search and then refine with more searches or to dig deeper based on their specific role. We are keeping it very simple here.

Important: Adapt from 7.6-SequentialAgents structure but completely overhaul for parallel execution with three specialized research agents running simultaneously. The 3 research agents NEED to actually run in parallel!

## EXAMPLES AND DOCUMENTATION:

7.6-SequentialAgents - This is the template in which our current directory is based off of. Just so that you know exactly how to set up an API endpoint to work with LangGraph, how to build the LangGraph workflows, how to work with the user input, how to set up the different nodes, how to create the Pydantic AI agents, this is your reference point. And so you still need to completely overhaul things, just using this as your inspiration, as your structure, as your guidance and documentation. Obviously, a lot is different here because we have different agents. We have a different flow for LangGraph. I will say, though, that the API endpoint will remain pretty much the same. And so it's still important for you to read through all of the files that we have here to understand the agents and the workflows and also to understand the testing and the API. But the API, you probably won't have to change that much. Most of the things, though, including the README, you're going to have to do a very big overhaul on, just using what we already have as your starting point. This starting point also shows you how to use the Brave API within the agents for web research.

## OTHER CONSIDERATIONS:

- All agents in the workflow need message history, but only the last agent will actually add on to the message history with the final result of the task being executed.
- Each parallel research agent will need to stream out text just saying that it is starting (hardcoded text) and then the final synthesis agent will need to stream out the final response based on all the research done
- Update the project structure in the README and basically do a big overhaul of the README after overhauling the existing codebase for the new graph.
- Virtual environment has already been set up with the necessary dependencies.
- .env.example has already been set up with all necessary values/credentials.
- Use python_dotenv and load_env() for environment variables.
