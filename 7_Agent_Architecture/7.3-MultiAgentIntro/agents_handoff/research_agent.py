"""
Research Agent with TRUE handoff capability using Union output types.

This agent can either respond directly with text OR call an output function
that hands off to the email agent. The handoff is a true handoff - control
does NOT return to the research agent after the email agent runs.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from agents_delegation.providers import get_llm_model
from agents_delegation.tools import search_web_tool
from .email_agent import email_agent, EmailAgentDependencies

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an expert research assistant with the ability to search the web and handle email requests. Your primary goal is to help users find relevant information and facilitate email communications.

Your capabilities:
1. **Web Search**: Use Brave Search to find current, relevant information on any topic
2. **Research Analysis**: Synthesize information from multiple sources with clear summaries
3. **Email Handoffs**: Hand off email creation requests to a specialized email agent

When conducting research:
- Use specific, targeted search queries
- Analyze search results for relevance and credibility
- Synthesize information from multiple sources
- Provide clear, well-organized summaries
- Include source URLs for reference

**CRITICAL DECISION MAKING**:

**For research/analysis requests** - Respond directly with your research findings:
- "What is the latest AI research?"
- "Analyze the stock market trends"  
- "Summarize information about quantum computing"
- "Find information about..."
- "Tell me about..."

**For email creation requests** - Use the email_handoff function:
- "Create an email to john@example.com about..."
- "Draft an email with my research findings to..."
- "Send this information to someone via email"
- "Compose an email about..."
- "Email the results to..."

When you use email_handoff, you are COMPLETELY handing off control to the email agent. Do NOT respond with text when creating emails - use the function instead.

You have access to web search tools to gather information for your responses.

Always strive to provide accurate, helpful, and actionable information.
"""


@dataclass
class ResearchAgentDependencies:
    """Dependencies for the research agent - only configuration, no tool instances."""
    brave_api_key: str
    gmail_credentials_path: str
    gmail_token_path: str
    session_id: Optional[str] = None


# Email handoff output function - TRUE handoff, control does NOT return
async def email_handoff(
    ctx: RunContext[ResearchAgentDependencies],
    recipient_email: str,
    subject: str,
    context: str,
    research_summary: Optional[str] = None
) -> str:
    """
    Email handoff output function - when called, completely hands off to email agent.
    
    This is a TRUE handoff - the email agent takes over completely and the
    research agent does NOT get control back. The email agent's response becomes
    the final response to the user.
    
    Args:
        ctx: Runtime context with dependencies and message history
        recipient_email: Email address of the recipient
        subject: Email subject line for the email
        context: Context or purpose for the email
        research_summary: Optional research findings to include
    
    Returns:
        str: The final response from the email agent (this ends the conversation)
    """
    try:
        logger.info(f"🔄 Email handoff initiated for {recipient_email}")
        
        # Prepare comprehensive prompt for email agent
        if research_summary:
            email_prompt = f"""
Create a professional email to {recipient_email} with the subject "{subject}".

Context: {context}

Research Summary to Include:
{research_summary}

Please create a well-structured email that:
1. Has an appropriate greeting
2. Provides clear context about why you're writing
3. Incorporates the research findings professionally
4. Includes actionable next steps if appropriate
5. Ends with a professional closing

The email should be informative but concise, maintaining a professional yet friendly tone.
"""
        else:
            email_prompt = f"""
Create a professional email to {recipient_email} with the subject "{subject}".

Context: {context}

Please create a well-structured email that addresses the context provided.
"""
        
        # Create email agent dependencies
        email_deps = EmailAgentDependencies(
            gmail_credentials_path=ctx.deps.gmail_credentials_path,
            gmail_token_path=ctx.deps.gmail_token_path,
            session_id=ctx.deps.session_id
        )
        
        logger.info("📧 Handing off to email agent...")
        
        # HANDOFF: Email agent takes over completely
        result = await email_agent.run(
            email_prompt,
            deps=email_deps,
            message_history=ctx.messages[:-1]  # Pass conversation context
        )
        
        logger.info(f"✅ Email handoff completed successfully for {recipient_email}")
        
        # The email agent's response becomes the final response
        return f"📧 **Email Draft Created for {recipient_email}:**\n\n{result.output}"
        
    except Exception as e:
        logger.error(f"❌ Email handoff failed: {e}")
        return f"❌ Failed to create email for {recipient_email}: {str(e)}"


# Research agent with Union output type: str OR email_handoff function
research_agent = Agent(
    get_llm_model(),
    deps_type=ResearchAgentDependencies,
    output_type=[str, email_handoff],  # type: ignore
    system_prompt=SYSTEM_PROMPT
)


# Tools for the research agent (web search and research summarization)
# Note: NO email tools here - email creation is handled via output function handoff

@research_agent.tool
async def search_web(
    ctx: RunContext[ResearchAgentDependencies],
    query: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search the web using Brave Search API.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return (1-20)
    
    Returns:
        List of search results with title, URL, description, and score
    """
    try:        
        # Ensure max_results is within valid range
        max_results = min(max(max_results, 1), 20)
        
        results = await search_web_tool(
            api_key=ctx.deps.brave_api_key,
            query=query,
            count=max_results
        )
        
        logger.info(f"Found {len(results)} results for query: {query}")
        return results
        
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return [{"error": f"Search failed: {str(e)}"}]


@research_agent.tool
async def summarize_research(
    ctx: RunContext[ResearchAgentDependencies],
    search_results: List[Dict[str, Any]],
    topic: str,
    focus_areas: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a comprehensive summary of research findings.
    
    Args:
        search_results: List of search result dictionaries
        topic: Main research topic
        focus_areas: Optional specific areas to focus on
    
    Returns:
        Dictionary with research summary
    """
    try:
        if not search_results:
            return {
                "summary": "No search results provided for summarization.",
                "key_points": [],
                "sources": []
            }
        
        # Extract key information
        sources = []
        descriptions = []
        
        for result in search_results:
            if "title" in result and "url" in result:
                sources.append(f"- {result['title']}: {result['url']}")
                if "description" in result:
                    descriptions.append(result["description"])
        
        # Create summary content
        content_summary = "\n".join(descriptions[:5])  # Limit to top 5 descriptions
        sources_list = "\n".join(sources[:10])  # Limit to top 10 sources
        
        focus_text = f"\nSpecific focus areas: {focus_areas}" if focus_areas else ""
        
        summary = f"""
Research Summary: {topic}{focus_text}

Key Findings:
{content_summary}

Sources:
{sources_list}
"""
        
        return {
            "summary": summary,
            "topic": topic,
            "sources_count": len(sources),
            "key_points": descriptions[:5]
        }
        
    except Exception as e:
        logger.error(f"Failed to summarize research: {e}")
        return {
            "summary": f"Failed to summarize research: {str(e)}",
            "key_points": [],
            "sources": []
        }


# Convenience function to create research agent with dependencies
def create_research_agent(
    brave_api_key: str,
    gmail_credentials_path: str,
    gmail_token_path: str,
    session_id: Optional[str] = None
) -> Agent:
    """
    Create a research agent with specified dependencies.
    
    Args:
        brave_api_key: Brave Search API key
        gmail_credentials_path: Path to Gmail credentials.json
        gmail_token_path: Path to Gmail token.json
        session_id: Optional session identifier
        
    Returns:
        Configured research agent
    """
    return research_agent