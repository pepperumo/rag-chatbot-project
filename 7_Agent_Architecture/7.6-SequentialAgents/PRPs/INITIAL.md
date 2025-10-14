## FEATURE:

LangGraph Workflow with Pydantic AI - Sequential Research & Outreach Agents
Build a LangGraph workflow with 5 agents using Pydantic AI:

- Input Guardrail Agent (uses llm_choice_small from .env - see .env.example): Determines if user request is for research/outreach flow via structured output. Routes to either a fallback agent (normal conversation with conversation history and knows how to guide the user to leverage the actual sequential agent workflow) or the sequential agent workflow.
- Research Agent (Brave API): Web research on lead, receives conversation history but doesn't add to it. Outputs research summary to LangGraph state and streams to user.
- Data Enrichment Agent (Brave API): Follow-up research to fill gaps (location, company, education) based on previous agent's summary. Also receives conversation history, outputs enrichment summary to state and streams to user.
- Email Draft Agent: Synthesizes all research from LangGraph state, drafts email, receives conversation history AND adds its response to conversation history as final step. Notifies user to check drafts.

State Flow: Input → Route Decision → (if research flow) Research → Data Enrichment → Email Draft. Research and enrichment agents stream summaries without updating conversation history, while final agent both streams and updates conversation history.
Models: Small model for guardrail, normal LLM_choice for sequential agents (and the fallback agent for a normal conversation) (via get_model function in clients.py).

It is absolutely crucial that you dive deep into 7.5-LLMRouting. Because you're going to be pulling directly from this implementation for basically everything that you're doing. In fact, the current folder structure is the same right now as 7.5-LLMRouting. You just have to tweak everything to work with this new sequential agents workflow. 

So, you're going to be changing a lot of existing files here and creating some new ones for the new agents. And so, we don't want any remnant of the old workflow specific to the LangGraph LLM routing flow. It all has to be completely overhauled, like a lot of changes that you're going to be making here to make it so that it's for this new LLM routing workflow. 

## EXAMPLES AND DOCUMENTATION:

7.3-MultiAgentIntro - analyze the email agent and tools to see how this agent is able to create Gmail drafts and the research agent to see how the agent does research with the Brave API

7.5-LLMRouting - This is the template in which our current directory is based off of. Just so that you know exactly how to set up an API endpoint to work with LangGraph, how to build the LangGraph workflows, how to work with the user input, how to set up the different nodes, how to create the Pydantic AI agents, this is your reference point. And so you still need to completely overhaul things, just using this as your inspiration, as your structure, as your guidance and documentation. Obviously, a lot is different here because we have different agents. We have a different flow for LangGraph. I will say, though, that the API endpoint will remain pretty much the same. And so it's still important for you to read through all of the files that we have here to understand the agents and the workflows and also to understand the testing and the API. But the API, you probably won't have to change that much. Most of the things, though, including the README, you're going to have to do a very big overhaul on, just using what we already have as your starting point. This starting point also shows you how to use the Brave and Gmail APIs within the agents for web research and email drafting.

## OTHER CONSIDERATIONS:

- All agents in the workflow need message history, but only the last agent will actually add on to the message history with the final result of the task being executed.
- Each agent will need to stream out a summary of what it did, and then pass that summary on to the next agent to be included as a part of the prompt for the next agent.
- Update the project structure in the README and basically do a big overhaul of the README after overhauling the existing codebase for the new graph.
- Virtual environment has already been set up with the necessary dependencies.
- .env.example has already been set up with all necessary values/credentials.
- Use python_dotenv and load_env() for environment variables.
