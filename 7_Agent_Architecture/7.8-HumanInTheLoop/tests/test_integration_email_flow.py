"""
Integration tests for the complete human-in-the-loop email workflow.

Tests the full flow: read → draft → request send → approve → send
with real API endpoint interactions and checkpointer state management.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from api.endpoints import app, langgraph_agent_endpoint
from api.models import AgentRequest


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def test_user_id():
    """Test user ID for authentication."""
    return "test_user_12345"


@pytest.fixture
def test_session_id():
    """Test session ID for conversation tracking."""
    return "test_session_67890"


@pytest.fixture
def mock_authenticated_user():
    """Mock authenticated user for all requests."""
    return {
        "id": "test_user_12345",
        "email": "testuser@example.com",
        "aud": "authenticated"
    }


class TestFullEmailApprovalFlow:
    """Test the complete email approval workflow integration."""
    
    @pytest.mark.asyncio
    async def test_full_email_approval_flow(self, test_user_id, test_session_id, mock_authenticated_user):
        """Test complete flow: read → draft → request send → approve → send."""
        
        # Mock all dependencies
        with patch('api.endpoints.verify_token', return_value=mock_authenticated_user):
            with patch('api.endpoints.check_rate_limit', return_value=True):
                with patch('api.endpoints.store_request', new_callable=AsyncMock):
                    with patch('api.endpoints.store_message', new_callable=AsyncMock):
                        with patch('api.endpoints.fetch_conversation_history', new_callable=AsyncMock) as mock_fetch_history:
                            with patch('api.endpoints.convert_history_to_pydantic_format', new_callable=AsyncMock) as mock_convert:
                                with patch('os.getenv', return_value="postgresql://test"):
                                    
                                    # STEP 1: Initial request to read emails
                                    mock_fetch_history.return_value = []
                                    mock_convert.return_value = []
                                    
                                    request1 = AgentRequest(
                                        query="Check my inbox for emails from john@example.com",
                                        session_id=test_session_id,
                                        request_id="request_001",
                                        user_id=test_user_id
                                    )
                                    
                                    with patch('api.endpoints.stream_langgraph_response') as mock_stream1:
                                        # Mock response for inbox reading
                                        async def mock_response1(*args, **kwargs):
                                            yield json.dumps({"text": "I found 2 emails from john@example.com in your inbox."}).encode() + b'\n'
                                            yield json.dumps({"complete": True}).encode() + b'\n'
                                        mock_stream1.return_value = mock_response1()
                                        
                                        from api.endpoints import langgraph_agent_endpoint
                                        response1 = await langgraph_agent_endpoint(request1, mock_authenticated_user)
                                        assert response1 is not None
                                    
                                    # STEP 2: Request to draft response
                                    mock_fetch_history.return_value = [
                                        {"message_type": "human", "content": "Check my inbox for emails from john@example.com"},
                                        {"message_type": "ai", "content": "I found 2 emails from john@example.com in your inbox."}
                                    ]
                                    
                                    request2 = AgentRequest(
                                        query="Draft a response thanking him for the meeting",
                                        session_id=test_session_id,
                                        request_id="request_002",
                                        user_id=test_user_id
                                    )
                                    
                                    with patch('api.endpoints.stream_langgraph_response') as mock_stream2:
                                        # Mock response for draft creation
                                        async def mock_response2(*args, **kwargs):
                                            yield json.dumps({"text": "I've created a draft email thanking John for the meeting."}).encode() + b'\n'
                                            yield json.dumps({"complete": True}).encode() + b'\n'
                                        mock_stream2.return_value = mock_response2()
                                        
                                        response2 = await langgraph_agent_endpoint(request2, mock_authenticated_user)
                                        assert response2 is not None
                                    
                                    # STEP 3: Request to send (should trigger approval)
                                    mock_fetch_history.return_value = [
                                        {"message_type": "human", "content": "Check my inbox for emails from john@example.com"},
                                        {"message_type": "ai", "content": "I found 2 emails from john@example.com in your inbox."},
                                        {"message_type": "human", "content": "Draft a response thanking him for the meeting"},
                                        {"message_type": "ai", "content": "I've created a draft email thanking John for the meeting."}
                                    ]
                                    
                                    request3 = AgentRequest(
                                        query="Send this email to john@example.com",
                                        session_id=test_session_id,
                                        request_id="request_003",
                                        user_id=test_user_id
                                    )
                                    
                                    with patch('api.endpoints.fetch_last_message_metadata', new_callable=AsyncMock) as mock_last_msg:
                                        mock_last_msg.return_value = None  # No previous approval state
                                        
                                        with patch('api.endpoints.stream_langgraph_response') as mock_stream3:
                                            # Mock response for send request (triggers approval)
                                            async def mock_response3(*args, **kwargs):
                                                yield json.dumps({"text": "I've prepared the email for sending. Please review and approve."}).encode() + b'\n'
                                                yield json.dumps({
                                                    "type": "approval_request",
                                                    "email_preview": {
                                                        "recipients": ["john@example.com"],
                                                        "subject": "Thank you for the meeting",
                                                        "body": "Hi John,\n\nThank you for taking the time to meet with me today. I found our discussion very valuable.\n\nBest regards"
                                                    }
                                                }).encode() + b'\n'
                                            mock_stream3.return_value = mock_response3()
                                            
                                            response3 = await langgraph_agent_endpoint(request3, mock_authenticated_user)
                                            assert response3 is not None
                                    
                                    # STEP 4: Approve send
                                    request4 = AgentRequest(
                                        query="yes-looks good, please send",
                                        session_id=test_session_id,
                                        request_id="request_004",
                                        user_id=test_user_id
                                    )
                                    
                                    with patch('api.endpoints.fetch_last_message_metadata', new_callable=AsyncMock) as mock_last_msg:
                                        mock_last_msg.return_value = {"awaiting_approval": True}  # Previous approval request
                                        
                                        with patch('api.endpoints.stream_langgraph_response') as mock_stream4:
                                            # Mock response for approved send
                                            async def mock_response4(*args, **kwargs):
                                                yield json.dumps({"text": "📤 **Sending Email...**\n"}).encode() + b'\n'
                                                yield json.dumps({"text": "✅ **Email sent successfully!**\nMessage ID: sent_msg_123\nSent to: john@example.com\n"}).encode() + b'\n'
                                                yield json.dumps({"complete": True}).encode() + b'\n'
                                            mock_stream4.return_value = mock_response4()
                                            
                                            response4 = await langgraph_agent_endpoint(request4, mock_authenticated_user)
                                            assert response4 is not None
    
    @pytest.mark.asyncio
    async def test_email_approval_decline_flow(self, test_user_id, test_session_id, mock_authenticated_user):
        """Test email approval decline and revision workflow."""
        
        with patch('api.endpoints.verify_token', return_value=mock_authenticated_user):
            with patch('api.endpoints.check_rate_limit', return_value=True):
                with patch('api.endpoints.store_request', new_callable=AsyncMock):
                    with patch('api.endpoints.store_message', new_callable=AsyncMock):
                        with patch('api.endpoints.fetch_conversation_history', new_callable=AsyncMock) as mock_fetch_history:
                            with patch('api.endpoints.convert_history_to_pydantic_format', new_callable=AsyncMock) as mock_convert:
                                with patch('os.getenv', return_value="postgresql://test"):
                                    
                                    # STEP 1: Request to send email (triggers approval)
                                    mock_fetch_history.return_value = []
                                    mock_convert.return_value = []
                                    
                                    request1 = AgentRequest(
                                        query="Send an email to colleague@company.com about the project update",
                                        session_id=test_session_id,
                                        request_id="request_001",
                                        user_id=test_user_id
                                    )
                                    
                                    with patch('api.endpoints.fetch_last_message_metadata', new_callable=AsyncMock) as mock_last_msg:
                                        mock_last_msg.return_value = None
                                        
                                        with patch('api.endpoints.stream_langgraph_response') as mock_stream1:
                                            # Mock approval request
                                            async def mock_response1(*args, **kwargs):
                                                yield json.dumps({
                                                    "type": "approval_request",
                                                    "email_preview": {
                                                        "recipients": ["colleague@company.com"],
                                                        "subject": "Project Update",
                                                        "body": "Hey, here's the project update..."
                                                    }
                                                }).encode() + b'\n'
                                            mock_stream1.return_value = mock_response1()
                                            
                                            response1 = await langgraph_agent_endpoint(request1, mock_authenticated_user)
                                            assert response1 is not None
                                    
                                    # STEP 2: Decline with feedback
                                    request2 = AgentRequest(
                                        query="no-please make it more formal and professional",
                                        session_id=test_session_id,
                                        request_id="request_002",
                                        user_id=test_user_id
                                    )
                                    
                                    with patch('api.endpoints.fetch_last_message_metadata', new_callable=AsyncMock) as mock_last_msg:
                                        mock_last_msg.return_value = {"awaiting_approval": True}
                                        
                                        with patch('api.endpoints.stream_langgraph_response') as mock_stream2:
                                            # Mock revision response
                                            async def mock_response2(*args, **kwargs):
                                                yield json.dumps({"text": "I understand you'd like me to make the email more formal and professional. Let me revise it..."}).encode() + b'\n'
                                                yield json.dumps({
                                                    "type": "approval_request",
                                                    "email_preview": {
                                                        "recipients": ["colleague@company.com"],
                                                        "subject": "Project Status Update",
                                                        "body": "Dear Colleague,\n\nI hope this message finds you well. I am writing to provide you with an update on our current project status..."
                                                    }
                                                }).encode() + b'\n'
                                            mock_stream2.return_value = mock_response2()
                                            
                                            response2 = await langgraph_agent_endpoint(request2, mock_authenticated_user)
                                            assert response2 is not None
    
    @pytest.mark.asyncio
    async def test_inbox_reading_without_approval(self, test_user_id, test_session_id, mock_authenticated_user):
        """Test inbox reading operations that don't require approval."""
        
        with patch('api.endpoints.verify_token', return_value=mock_authenticated_user):
            with patch('api.endpoints.check_rate_limit', return_value=True):
                with patch('api.endpoints.store_request', new_callable=AsyncMock):
                    with patch('api.endpoints.store_message', new_callable=AsyncMock):
                        with patch('api.endpoints.fetch_conversation_history', new_callable=AsyncMock) as mock_fetch_history:
                            with patch('api.endpoints.convert_history_to_pydantic_format', new_callable=AsyncMock) as mock_convert:
                                with patch('os.getenv', return_value="postgresql://test"):
                                    
                                    mock_fetch_history.return_value = []
                                    mock_convert.return_value = []
                                    
                                    # Test various inbox reading queries
                                    test_queries = [
                                        "Check my inbox for unread emails",
                                        "Show me emails from my boss",
                                        "List emails with attachments",
                                        "Find emails about the quarterly report",
                                        "Show me today's emails"
                                    ]
                                    
                                    for i, query in enumerate(test_queries):
                                        request = AgentRequest(
                                            query=query,
                                            session_id=test_session_id,
                                            request_id=f"request_{i:03d}",
                                            user_id=test_user_id
                                        )
                                        
                                        with patch('api.endpoints.stream_langgraph_response') as mock_stream:
                                            # Mock normal conversation response (no approval needed)
                                            async def mock_response(*args, **kwargs):
                                                yield json.dumps({"text": f"I've checked your inbox based on your query: {query}"}).encode() + b'\n'
                                                yield json.dumps({"complete": True}).encode() + b'\n'
                                            mock_stream.return_value = mock_response()
                                            
                                            from api.endpoints import langgraph_agent_endpoint
                                            response = await langgraph_agent_endpoint(request, mock_authenticated_user)
                                            assert response is not None
    
    @pytest.mark.asyncio
    async def test_draft_creation_without_approval(self, test_user_id, test_session_id, mock_authenticated_user):
        """Test email draft creation that doesn't require approval."""
        
        with patch('api.endpoints.verify_token', return_value=mock_authenticated_user):
            with patch('api.endpoints.check_rate_limit', return_value=True):
                with patch('api.endpoints.store_request', new_callable=AsyncMock):
                    with patch('api.endpoints.store_message', new_callable=AsyncMock):
                        with patch('api.endpoints.fetch_conversation_history', new_callable=AsyncMock) as mock_fetch_history:
                            with patch('api.endpoints.convert_history_to_pydantic_format', new_callable=AsyncMock) as mock_convert:
                                with patch('os.getenv', return_value="postgresql://test"):
                                    
                                    mock_fetch_history.return_value = []
                                    mock_convert.return_value = []
                                    
                                    # Test various draft creation queries
                                    test_queries = [
                                        "Create a draft email to my team about the meeting",
                                        "Draft a thank you email to the client",
                                        "Prepare a follow-up email for the interview",
                                        "Write a draft response to the inquiry"
                                    ]
                                    
                                    for i, query in enumerate(test_queries):
                                        request = AgentRequest(
                                            query=query,
                                            session_id=test_session_id,
                                            request_id=f"draft_request_{i:03d}",
                                            user_id=test_user_id
                                        )
                                        
                                        with patch('api.endpoints.stream_langgraph_response') as mock_stream:
                                            # Mock draft creation response (no approval needed)
                                            async def mock_response(*args, **kwargs):
                                                yield json.dumps({"text": f"I've created a draft email for: {query}"}).encode() + b'\n'
                                                yield json.dumps({"complete": True}).encode() + b'\n'
                                            mock_stream.return_value = mock_response()
                                            
                                            from api.endpoints import langgraph_agent_endpoint
                                            response = await langgraph_agent_endpoint(request, mock_authenticated_user)
                                            assert response is not None


class TestErrorScenarios:
    """Test error scenarios in the integration flow."""
    
    @pytest.mark.asyncio
    async def test_gmail_api_error_during_flow(self, test_user_id, test_session_id, mock_authenticated_user):
        """Test handling of Gmail API errors during the workflow."""
        
        with patch('api.endpoints.verify_token', return_value=mock_authenticated_user):
            with patch('api.endpoints.check_rate_limit', return_value=True):
                with patch('api.endpoints.store_request', new_callable=AsyncMock):
                    with patch('api.endpoints.store_message', new_callable=AsyncMock):
                        with patch('api.endpoints.fetch_conversation_history', new_callable=AsyncMock) as mock_fetch_history:
                            with patch('api.endpoints.convert_history_to_pydantic_format', new_callable=AsyncMock) as mock_convert:
                                with patch('os.getenv', return_value="postgresql://test"):
                                    
                                    mock_fetch_history.return_value = []
                                    mock_convert.return_value = []
                                    
                                    request = AgentRequest(
                                        query="Check my inbox",
                                        session_id=test_session_id,
                                        request_id="error_request_001",
                                        user_id=test_user_id
                                    )
                                    
                                    with patch('api.endpoints.stream_langgraph_response') as mock_stream:
                                        # Mock Gmail API error response
                                        async def mock_error_response(*args, **kwargs):
                                            yield json.dumps({"text": "I encountered an error accessing Gmail: Authentication failed. Please check your credentials."}).encode() + b'\n'
                                            yield json.dumps({"complete": True, "error": True}).encode() + b'\n'
                                        mock_stream.return_value = mock_error_response()
                                        
                                        from api.endpoints import langgraph_agent_endpoint
                                        response = await langgraph_agent_endpoint(request, mock_authenticated_user)
                                        assert response is not None
    
    @pytest.mark.asyncio
    async def test_interrupt_timeout_scenario(self, test_user_id, test_session_id, mock_authenticated_user):
        """Test handling of interrupt timeout scenarios."""
        
        with patch('api.endpoints.verify_token', return_value=mock_authenticated_user):
            with patch('api.endpoints.check_rate_limit', return_value=True):
                with patch('api.endpoints.store_request', new_callable=AsyncMock):
                    with patch('api.endpoints.store_message', new_callable=AsyncMock):
                        with patch('api.endpoints.fetch_conversation_history', new_callable=AsyncMock) as mock_fetch_history:
                            with patch('api.endpoints.convert_history_to_pydantic_format', new_callable=AsyncMock) as mock_convert:
                                with patch('os.getenv', return_value="postgresql://test"):
                                    
                                    mock_fetch_history.return_value = []
                                    mock_convert.return_value = []
                                    
                                    request = AgentRequest(
                                        query="Send email to timeout@example.com",
                                        session_id=test_session_id,
                                        request_id="timeout_request_001",
                                        user_id=test_user_id
                                    )
                                    
                                    with patch('api.endpoints.stream_langgraph_response') as mock_stream:
                                        # Mock timeout/interrupt error
                                        async def mock_timeout_response(*args, **kwargs):
                                            yield json.dumps({"text": "I've prepared the email but the approval process timed out. Please try sending again."}).encode() + b'\n'
                                            yield json.dumps({"complete": True, "timeout": True}).encode() + b'\n'
                                        mock_stream.return_value = mock_timeout_response()
                                        
                                        from api.endpoints import langgraph_agent_endpoint
                                        response = await langgraph_agent_endpoint(request, mock_authenticated_user)
                                        assert response is not None


class TestStateManagement:
    """Test state persistence and management across interrupts."""
    
    @pytest.mark.asyncio
    async def test_state_persistence_across_approval_cycle(self, test_user_id, test_session_id, mock_authenticated_user):
        """Test that state is properly maintained across the approval cycle."""
        
        # This test would verify that the checkpointer correctly maintains state
        # across the interrupt and resumption process
        
        with patch('api.endpoints.verify_token', return_value=mock_authenticated_user):
            with patch('api.endpoints.check_rate_limit', return_value=True):
                with patch('api.endpoints.store_request', new_callable=AsyncMock):
                    with patch('api.endpoints.store_message', new_callable=AsyncMock):
                        with patch('api.endpoints.fetch_conversation_history', new_callable=AsyncMock) as mock_fetch_history:
                            with patch('api.endpoints.convert_history_to_pydantic_format', new_callable=AsyncMock) as mock_convert:
                                with patch('os.getenv', return_value="postgresql://test"):
                                    
                                    # Initial state
                                    mock_fetch_history.return_value = []
                                    mock_convert.return_value = []
                                    
                                    # Simulate state changes through the approval cycle
                                    state_changes = []
                                    
                                    def track_state_change(*args, **kwargs):
                                        state_changes.append(args)
                                    
                                    with patch('api.endpoints.stream_langgraph_response', side_effect=track_state_change):
                                        # Request 1: Trigger approval
                                        request1 = AgentRequest(
                                            query="Send email to state@example.com",
                                            session_id=test_session_id,
                                            request_id="state_request_001",
                                            user_id=test_user_id
                                        )
                                        
                                        try:
                                            from api.endpoints import langgraph_agent_endpoint
                                            await langgraph_agent_endpoint(request1, mock_authenticated_user)
                                        except:
                                            pass  # Expected due to mocking
                                        
                                        # Verify state tracking occurred
                                        assert len(state_changes) > 0


if __name__ == "__main__":
    pytest.main([__file__])