"""
Main API endpoints for the Human-in-the-Loop Email Agent System.

This provides a FastAPI endpoint that integrates with LangGraph workflows,
email management with human approval, and streaming responses.

IMPORTANT: Uncomment the line below for checkpointer.setup() for the first run then comment out again.
This sets things up in your database for the LangGraph Postgres checkpointer. You only have to run it once.
"""
from typing import Optional, Dict, Any, AsyncIterator, List
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager, nullcontext
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import json
import os

from clients import get_agent_clients, get_model, get_langfuse_client
from pydantic_ai import Agent
from langfuse import observe

# Import our models and utilities
from api.models import (
    AgentRequest, HealthCheckResponse
)
from api.streaming import create_error_stream
from graph.workflow import (
    create_email_workflow, 
    create_email_api_initial_state
)
from .db_utils import (
    fetch_conversation_history,
    create_conversation,
    update_conversation_title,
    generate_session_id,
    generate_conversation_title,
    store_message,
    convert_history_to_pydantic_format,
    check_rate_limit,
    store_request,
    fetch_last_message_metadata
)

# Check if we're in production
is_production = os.getenv("ENVIRONMENT") == "production"

if not is_production:
    # Development: prioritize .env file
    project_root = Path(__file__).resolve().parent
    dotenv_path = project_root / '.env'
    load_dotenv(dotenv_path, override=True)
else:
    # Production: use cloud platform env vars only
    load_dotenv()

# Global clients (initialized in lifespan)
embedding_client = None
supabase = None
http_client = None
title_agent = None
langfuse = None

# FastAPI app setup
security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Verify the JWT token from Supabase and return the user information.
    
    Args:
        credentials: The HTTP Authorization credentials containing the bearer token
        
    Returns:
        Dict[str, Any]: The user information from Supabase
        
    Raises:
        HTTPException: If the token is invalid or the user cannot be verified
    """
    try:
        # Get the token from the Authorization header
        token = credentials.credentials
        
        # Access the global HTTP client
        global http_client
        if not http_client:
            raise HTTPException(status_code=500, detail="HTTP client not initialized")
        
        # Get the Supabase URL and anon key from environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        # Make request to Supabase auth API to get user info
        response = await http_client.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": supabase_key
            }
        )
        
        # Check if the request was successful
        if response.status_code != 200:
            print(f"Auth response error: {response.text}")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Return the user information
        user_data = response.json()
        return user_data
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    global embedding_client, supabase, http_client, title_agent, langfuse
    
    # Startup: Initialize all clients
    embedding_client, supabase, http_client = get_agent_clients()
    title_agent = Agent(model=get_model())
    langfuse = get_langfuse_client()
    
    yield  # This is where the app runs
    
    # Shutdown: Clean up resources
    if http_client:
        await http_client.aclose()


# Initialize FastAPI app with lifespan
def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Human-in-the-Loop Email Agent System",
        version="1.0.0",
        description="Email management agent with human approval workflow using LangGraph and Pydantic AI",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


app = create_app()




@app.post("/api/human-in-the-loop-agent")
async def langgraph_agent_endpoint(
    request: AgentRequest, 
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    LangGraph human-in-the-loop email agent endpoint with checkpointer and interrupt handling.
    Supports autonomous email reading/drafting with human approval for sending.
    
    Args:
        request: Agent request with query, session info, and optional files
        user: Verified user information from JWT token
        
    Returns:
        StreamingResponse with human-in-the-loop workflow support
    """
    # Verify that the user ID in the request matches the user ID from the token
    if request.user_id != user.get("id"):
        error_stream = create_error_stream(
            "User ID in request does not match authenticated user", 
            request.session_id
        )
        return StreamingResponse(
                error_stream.stream_error(),
                media_type='text/plain'
            )
    
    try:
        # Check rate limit
        rate_limit_ok = await check_rate_limit(supabase, request.user_id)
        if not rate_limit_ok:
            error_msg = "Rate limit exceeded. Please try again later."
            error_stream = create_error_stream(error_msg, request.session_id)
            return StreamingResponse(
                error_stream.stream_error(),
                media_type='text/plain'
            )
        
        # Start request tracking in parallel
        request_tracking_task = asyncio.create_task(
            store_request(supabase, request.request_id, request.user_id, request.query)
        )
        
        session_id = request.session_id
        conversation_record = None
        
        # Check if session_id is empty, create a new conversation if needed
        if not session_id:
            session_id = generate_session_id(request.user_id)
            conversation_record = await create_conversation(supabase, request.user_id, session_id)
        
        # Store user's query immediately
        await store_message(
            supabase=supabase,
            session_id=session_id,
            message_type="human",
            content=request.query
        )
        
        # Fetch conversation history from the DB
        conversation_history = await fetch_conversation_history(supabase, session_id)
        
        # Convert conversation history to Pydantic AI format
        pydantic_messages = await convert_history_to_pydantic_format(conversation_history)
        
        # Start title generation in parallel if this is a new conversation
        title_task = None
        if conversation_record:
            title_task = asyncio.create_task(
                generate_conversation_title(title_agent, request.query)
            )
        
        # Get database URL for checkpointer
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required for human-in-the-loop workflow")
        
        # Return streaming response with checkpointer
        return StreamingResponse(
            stream_langgraph_response(
                request=request,
                session_id=session_id,
                pydantic_messages=pydantic_messages,
                database_url=database_url,
                title_task=title_task,
                request_tracking_task=request_tracking_task,
                user_id=request.user_id
            ),
            media_type="text/plain"
        )
    
    except Exception as e:
        print(f"Error processing email agent request: {str(e)}")
        
        # Store error message in conversation if session_id exists
        if session_id:
            await store_message(
                supabase=supabase,
                session_id=session_id,
                message_type="ai",
                content="I apologize, but I encountered an error processing your email request.",
                data={"error": str(e), "request_id": request.request_id}
            )
        
        # Return error response
        error_stream = create_error_stream(f"Error: {str(e)}", session_id)
        return StreamingResponse(
            error_stream.stream_error(),
            media_type='text/plain'
        )



async def stream_langgraph_response(
    request: AgentRequest,
    session_id: str,
    pydantic_messages: List,
    database_url: str,
    title_task: Optional[asyncio.Task] = None,
    request_tracking_task: Optional[asyncio.Task] = None,
    user_id: Optional[str] = None
) -> AsyncIterator[bytes]:
    """
    Stream email agent response with human-in-the-loop approval workflow.
    
    Args:
        request: The agent request
        session_id: Session ID for database operations
        pydantic_messages: Conversation history in Pydantic format
        database_url: PostgreSQL database URL for checkpointer
        title_task: Optional title generation task
        request_tracking_task: Optional request tracking task
        user_id: User ID for tracing
        
    Yields:
        Streaming response bytes with real-time tokens and approval UI
    """
    try:
        # Import required modules
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from langgraph.types import Command
        
        # Check if we need to resume from interrupt
        last_message = await fetch_last_message_metadata(supabase, session_id)
        is_approval_response = False
        approval_decision = None
        
        # Check for approval responses even without awaiting_approval flag
        # This handles the race condition where interrupt happens before flag is set
        query_lower = request.query.lower().strip()
        if query_lower.startswith("yes-") or query_lower == "yes":
            is_approval_response = True
            feedback = query_lower[4:] if len(query_lower) > 4 else ""
            approval_decision = {"approved": True, "feedback": feedback}
        elif query_lower.startswith("no-") or query_lower == "no":
            is_approval_response = True
            feedback = query_lower[3:] if len(query_lower) > 3 else ""
            approval_decision = {"approved": False, "feedback": feedback}
        
        # If we detected approval response but no awaiting_approval flag, still try to resume
        # This handles cases where the interrupt occurred before the flag was stored
        
        # Use checkpointer context manager
        async with AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
            # Run this once for first time setup then comment out
            try:
                await checkpointer.setup()
            except Exception as setup_error:
                # Tables might already exist, continue
                print(f"Checkpointer setup (tables might exist): {setup_error}")

            workflow = create_email_workflow(checkpointer=checkpointer)
            
            thread_id = f"email-hitl-{session_id}"
            config = {"configurable": {"thread_id": thread_id}}
            
            # Add LangFuse callback if available
            tracing_span = nullcontext()
            if langfuse:
                try:
                    from langfuse.langchain import CallbackHandler
                    langfuse_handler = CallbackHandler()
                    config["callbacks"] = [langfuse_handler]
                    
                    # Start the Langfuse trace
                    tracing_span = langfuse.start_as_current_span(
                        name="email-agent-hitl", 
                        input={"user_query": request.query}
                    )
                except Exception as e:
                    print(f"LangFuse tracing error: {e}")
            
            full_response = ""
            final_state = None
            
            with tracing_span as span:
                # Update Langfuse trace with user ID and session ID
                if langfuse and span:
                    span.update_trace(user_id=user_id, session_id=session_id)
                
                if is_approval_response:
                    # Resume from interrupt with Command - let the workflow handle it normally
                    command = Command(resume=approval_decision)
                    
                    async for stream_mode, chunk in workflow.astream(command, config, stream_mode=["custom", "values"]):
                        if stream_mode == "custom":
                            # Custom streaming content from writer() calls in nodes
                            if isinstance(chunk, str):
                                full_response += chunk
                                chunk_data = {"text": full_response}
                                yield json.dumps(chunk_data).encode('utf-8') + b'\n'
                            elif isinstance(chunk, bytes):
                                try:
                                    decoded = chunk.decode('utf-8')
                                    full_response += decoded
                                    chunk_data = {"text": full_response}
                                    yield json.dumps(chunk_data).encode('utf-8') + b'\n'
                                except Exception:
                                    yield chunk
                        elif stream_mode == "values":
                            final_state = chunk
                            # REMOVED: No approval UI checks in approval response branch
                            # The approval decision has already been made!
                else:
                    # Normal flow - create initial state and run
                    initial_state = create_email_api_initial_state(
                        query=request.query,
                        session_id=session_id,
                        request_id=request.request_id,
                        pydantic_message_history=pydantic_messages
                    )
                    
                    async for stream_mode, chunk in workflow.astream(initial_state, config, stream_mode=["custom", "values"]):
                        if stream_mode == "custom":
                            # Custom streaming content from writer() calls in nodes
                            if isinstance(chunk, str):
                                full_response += chunk
                                chunk_data = {"text": full_response}
                                yield json.dumps(chunk_data).encode('utf-8') + b'\n'
                            elif isinstance(chunk, bytes):
                                try:
                                    decoded = chunk.decode('utf-8')
                                    full_response += decoded
                                    chunk_data = {"text": full_response}
                                    yield json.dumps(chunk_data).encode('utf-8') + b'\n'
                                except Exception:
                                    yield chunk
                        elif stream_mode == "values":
                            final_state = chunk
                            
                            # DISABLED: Let workflow handle approval UI entirely via writer output
                            # Only store metadata for approval detection, don't generate UI here
                            if chunk.get("email_recipients") and chunk.get("email_subject") and not chunk.get("approval_granted"):
                                # Only store metadata - no UI generation
                                await store_message(
                                    supabase=supabase,
                                    session_id=session_id,
                                    message_type="ai",
                                    content="I've prepared the email for sending. Please approve or decline.",
                                    data={
                                        "request_id": request.request_id,
                                        "awaiting_approval": True,
                                        "email_preview": {
                                            "recipients": chunk.get("email_recipients", []),
                                            "subject": chunk.get("email_subject", ""),
                                            "body": chunk.get("email_body", "")
                                        }
                                    }
                                )
                
                # Update Langfuse trace with output
                if langfuse and span:
                    span.update(output={"agent_response": full_response})
        
        # Store agent's response in database (if not already stored during approval)
        if not (last_message and last_message.get("awaiting_approval")):
            try:
                # Handle message_history which contains bytes objects
                message_data = final_state.get("message_history", []) if final_state else []
                message_data_bytes = message_data[0] if message_data and isinstance(message_data[0], bytes) else None
                
                await store_message(
                    supabase=supabase,
                    session_id=session_id,
                    message_type="ai",
                    content=full_response or "No response generated",
                    message_data=message_data_bytes,
                    data={
                        "request_id": request.request_id,
                        "email_workflow": True,
                        "streaming_tokens_collected": len(full_response) if full_response else 0
                    }
                )
            except Exception as db_error:
                print(f"Database storage error: {db_error}")
        
        # Handle title generation if it's running
        if title_task:
            try:
                conversation_title = await title_task
                await update_conversation_title(supabase, session_id, conversation_title)
                
                # Send final chunk with title
                final_chunk = {
                    "session_id": session_id,
                    "conversation_title": conversation_title,
                    "complete": True,
                    "request_id": request.request_id,
                    "final_response": full_response
                }
                yield json.dumps(final_chunk).encode('utf-8') + b'\n'
            except Exception as e:
                print(f"Error processing title: {str(e)}")
        
        # Wait for request tracking task
        if request_tracking_task:
            try:
                await request_tracking_task
            except Exception as e:
                print(f"Error tracking request: {str(e)}")
        
    except Exception as e:
        print(f"Email agent streaming error: {e}")
        error_msg = f"Email agent error: {str(e)}"
        error_chunk = {"text": error_msg}
        yield json.dumps(error_chunk).encode('utf-8') + b'\n'


@app.get("/health")
async def health_check() -> HealthCheckResponse:
    """Health check endpoint for container orchestration and monitoring."""
    try:
        # Check if critical dependencies are initialized
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Human-in-the-Loop Email Agent System is running",
            "dependencies": {
                "embedding_client": "connected" if embedding_client else "disconnected",
                "supabase": "connected" if supabase else "disconnected", 
                "http_client": "connected" if http_client else "disconnected",
                "title_agent": "connected" if title_agent else "disconnected"
            }
        }
        
        # If any critical service is not initialized, mark as unhealthy
        if not all(v == "connected" for v in health_status["dependencies"].values()):
            health_status["status"] = "unhealthy"
            raise HTTPException(status_code=503, detail=health_status)
        
        return HealthCheckResponse(**health_status)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}"
            }
        )


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "system": "Human-in-the-Loop Email Agent System",
        "version": "1.0.0", 
        "description": "Email management agent with human approval workflow using LangGraph and Pydantic AI",
        "endpoints": {
            "POST /api/langgraph-agent": "Human-in-the-loop email agent endpoint with streaming",
            "GET /health": "Health check endpoint",
            "GET /": "System information"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)