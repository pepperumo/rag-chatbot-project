from pydantic_ai import Agent, RunContext

from .deps import AgentDeps
from clients import get_model
from tools.rag_tools import get_document_content_tool
from tools.validation_tools import (
    extract_google_drive_urls,
    extract_file_ids_from_urls,
    validate_all_citations
)

# System prompt for guardrail agent
GUARDRAIL_SYSTEM_PROMPT = """You are a citation validation specialist. Your job is to:

1. Extract all Google Drive document URLs from the response (format: https://docs.google.com/document/d/[file_id]/)
2. Verify each cited source contains relevant information for the query
3. Return structured validation results
4. Provide specific feedback if validation fails

Validation criteria:
- All citations must be valid Google Drive document URLs
- Cited content must be relevant to the original query
- No hallucinated or fake citations allowed
- Return "VALID" if all citations check out, otherwise provide specific feedback

When validating, check that:
- The URLs are properly formatted
- The documents exist in the knowledge base
- The content is actually relevant to the user's question
- The response accurately reflects the document contents

If validation fails, provide clear feedback about what needs to be corrected."""

# Create guardrail agent
guardrail_agent = Agent(
    get_model(),
    system_prompt=GUARDRAIL_SYSTEM_PROMPT,
    deps_type=AgentDeps,
    retries=2,
    instrument=True,
)

@guardrail_agent.tool
async def get_document_content(ctx: RunContext[AgentDeps], document_id: str) -> str:
    """
    Retrieve the full content of a specific document by combining all its chunks.
    
    Args:
        ctx: The context including the Supabase client
        document_id: The ID (or file path) of the document to retrieve
        
    Returns:
        The full content of the document with all chunks combined in order
    """
    print("Guardrail agent calling get_document_content tool")
    return await get_document_content_tool(ctx.deps.supabase, document_id)

@guardrail_agent.tool
async def extract_citations(ctx: RunContext[AgentDeps], response_text: str) -> str:
    """
    Extract Google Drive URLs from response text.
    
    Args:
        ctx: The context
        response_text: The response text to analyze
        
    Returns:
        List of extracted Google Drive URLs
    """
    print("Guardrail agent calling extract_citations tool")
    urls = extract_google_drive_urls(response_text)
    file_ids = extract_file_ids_from_urls(urls)
    
    return f"Found {len(urls)} citations with file IDs: {file_ids}"

@guardrail_agent.tool
async def validate_citations(ctx: RunContext[AgentDeps], response_text: str, original_query: str) -> str:
    """
    Validate all citations in a response against the original query.
    
    Args:
        ctx: The context including clients
        response_text: The response text containing citations
        original_query: The original user query
        
    Returns:
        Validation results as a string
    """
    print("Guardrail agent calling validate_citations tool")
    validation_result = await validate_all_citations(
        ctx.deps.supabase,
        ctx.deps.embedding_client,
        response_text,
        original_query
    )
    
    if validation_result["status"] == "valid":
        return "VALID - All citations are accurate and relevant"
    else:
        return f"INVALID - {validation_result['feedback']}"