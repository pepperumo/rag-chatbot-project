from pydantic_ai import Agent, RunContext

from .deps import AgentDeps
from clients import get_model
from tools.rag_tools import (
    retrieve_relevant_documents_tool,
    list_documents_tool,
    get_document_content_tool
)

# System prompt for primary agent with citation requirements
PRIMARY_AGENT_SYSTEM_PROMPT = """You are a RAG-enabled research assistant. When answering questions:

1. ALWAYS search for relevant information using your tools
2. ALWAYS cite your sources as Google Drive document URLs in this exact format: 
   "https://docs.google.com/document/d/[file_id]/"
3. Multiple sources should be cited as separate URLs
4. Only use information from the documents you retrieve
5. If you cannot find relevant information, say so explicitly
6. Include specific details from the documents to support your answers

Example response format:
"Based on the research data, the quarterly revenue increased by 15%. Source: https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/

For additional context, market trends show growth in the technology sector. Source: https://docs.google.com/document/d/9i8h7g6f5e4d3c2b1a0z/"

CRITICAL: You must include at least one citation in your response. If no relevant documents are found, explicitly state this."""

# Create primary agent
primary_agent = Agent(
    get_model(),
    system_prompt=PRIMARY_AGENT_SYSTEM_PROMPT,
    deps_type=AgentDeps,
    retries=2,
    instrument=True,
)

@primary_agent.system_prompt
async def add_feedback_to_prompt(ctx: RunContext[AgentDeps]) -> str:
    """Add feedback to system prompt if provided by guardrail agent"""
    if ctx.deps.feedback:
        return f"""
        
FEEDBACK FROM VALIDATION:
{ctx.deps.feedback}

Please address this feedback and provide a corrected response with proper citations.
Make sure to search for relevant documents and cite them accurately.
        """
    return ""

@primary_agent.tool
async def retrieve_relevant_documents(ctx: RunContext[AgentDeps], user_query: str) -> str:
    """
    Retrieve relevant document chunks based on the query with RAG.
    
    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The user's question or query
        
    Returns:
        A formatted string containing the top 4 most relevant documents chunks
    """
    print("Primary agent calling retrieve_relevant_documents tool")
    return await retrieve_relevant_documents_tool(
        ctx.deps.supabase, 
        ctx.deps.embedding_client, 
        user_query
    )

@primary_agent.tool
async def list_documents(ctx: RunContext[AgentDeps]) -> str:
    """
    Retrieve a list of all available documents.
    
    Args:
        ctx: The context including the Supabase client
        
    Returns:
        List of documents including their metadata (URL/path, schema if applicable, etc.)
    """
    print("Primary agent calling list_documents tool")
    return await list_documents_tool(ctx.deps.supabase)

@primary_agent.tool
async def get_document_content(ctx: RunContext[AgentDeps], document_id: str) -> str:
    """
    Retrieve the full content of a specific document by combining all its chunks.
    
    Args:
        ctx: The context including the Supabase client
        document_id: The ID (or file path) of the document to retrieve
        
    Returns:
        The full content of the document with all chunks combined in order
    """
    print("Primary agent calling get_document_content tool")
    return await get_document_content_tool(ctx.deps.supabase, document_id)