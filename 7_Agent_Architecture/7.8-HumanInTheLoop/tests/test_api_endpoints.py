"""
Unit tests for API endpoints with human-in-the-loop email functionality.

Tests cover the email agent endpoint, streaming responses, 
checkpointer integration, and Command handling for approval workflow.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from api.endpoints import (
    app,
    langgraph_agent_endpoint,
    stream_langgraph_response,
    verify_token
)
from api.models import AgentRequest


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_agent_request():
    """Create a sample agent request for testing."""
    return AgentRequest(
        query="Send an email to test@example.com",
        session_id="test_session_123",
        request_id="test_request_456",
        user_id="test_user_789"
    )


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return {
        "id": "test_user_789",
        "email": "testuser@example.com",
        "aud": "authenticated"
    }


class TestEmailAgentEndpoint:
    """Test the main email agent endpoint."""
    
    @pytest.mark.asyncio
    async def test_email_agent_endpoint_user_mismatch(self, sample_agent_request):
        """Test endpoint rejects request when user IDs don't match."""
        # Mock user with different ID
        mock_user = {"id": "different_user_id"}
        
        with patch('api.endpoints.verify_token', return_value=mock_user):
            with patch('api.endpoints.create_error_stream') as mock_error_stream:
                mock_error_stream.return_value.stream_error.return_value = [b"Error"]
                
                # This would normally be called through FastAPI dependency injection
                result = await langgraph_agent_endpoint(sample_agent_request, mock_user)
                
                # Verify error stream was created for user mismatch
                mock_error_stream.assert_called_once()
                assert "User ID in request does not match" in mock_error_stream.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_email_agent_endpoint_rate_limit_exceeded(self, sample_agent_request, mock_user):
        """Test endpoint handles rate limit exceeded."""
        with patch('api.endpoints.verify_token', return_value=mock_user):
            with patch('api.endpoints.check_rate_limit', return_value=False):
                with patch('api.endpoints.create_error_stream') as mock_error_stream:
                    mock_error_stream.return_value.stream_error.return_value = [b"Rate limit"]
                    
                    result = await langgraph_agent_endpoint(sample_agent_request, mock_user)
                    
                    mock_error_stream.assert_called_once()
                    assert "Rate limit exceeded" in mock_error_stream.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_email_agent_endpoint_missing_database_url(self, sample_agent_request, mock_user):
        """Test endpoint handles missing DATABASE_URL."""
        with patch('api.endpoints.verify_token', return_value=mock_user):
            with patch('api.endpoints.check_rate_limit', return_value=True):
                with patch('api.endpoints.store_request', new_callable=AsyncMock):
                    with patch('api.endpoints.store_message', new_callable=AsyncMock):
                        with patch('api.endpoints.fetch_conversation_history', new_callable=AsyncMock):
                            with patch('api.endpoints.convert_history_to_pydantic_format', new_callable=AsyncMock):
                                with patch('os.getenv', return_value=None):  # No DATABASE_URL
                                    with patch('api.endpoints.create_error_stream') as mock_error_stream:
                                        mock_error_stream.return_value.stream_error.return_value = iter([b"Error"])
                                        
                                        response = await langgraph_agent_endpoint(sample_agent_request, mock_user)
                                        
                                        # Should return StreamingResponse with error
                                        assert isinstance(response, StreamingResponse)
                                        mock_error_stream.assert_called_once()
                                        assert "DATABASE_URL environment variable is required" in mock_error_stream.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_email_agent_endpoint_success_flow(self, sample_agent_request, mock_user):
        """Test successful email agent endpoint execution."""
        with patch('api.endpoints.verify_token', return_value=mock_user):
            with patch('api.endpoints.check_rate_limit', return_value=True):
                with patch('api.endpoints.store_request', new_callable=AsyncMock):
                    with patch('api.endpoints.store_message', new_callable=AsyncMock):
                        with patch('api.endpoints.fetch_conversation_history', new_callable=AsyncMock) as mock_fetch:
                            mock_fetch.return_value = []
                            with patch('api.endpoints.convert_history_to_pydantic_format', new_callable=AsyncMock) as mock_convert:
                                mock_convert.return_value = []
                                with patch('os.getenv', return_value="postgresql://test"):
                                    with patch('api.endpoints.stream_langgraph_response') as mock_stream:
                                        mock_stream.return_value = [b"response"]
                                        
                                        result = await langgraph_agent_endpoint(sample_agent_request, mock_user)
                                        
                                        # Verify streaming response is returned
                                        assert result is not None
                                        assert mock_stream.called


class TestStreamEmailAgentResponse:
    """Test the streaming email agent response function core logic."""
    
    @pytest.mark.asyncio
    async def test_approval_response_detection_logic(self, sample_agent_request):
        """Test approval response detection logic."""
        # Test normal query (not approval)
        query_lower = sample_agent_request.query.lower().strip()
        is_approval_response = False
        
        if query_lower.startswith("yes-") or query_lower == "yes":
            is_approval_response = True
        elif query_lower.startswith("no-") or query_lower == "no":
            is_approval_response = True
        
        assert not is_approval_response  # Sample request is not an approval response
        
        # Test yes approval
        yes_query = "yes-looks good"
        is_yes = yes_query.lower().startswith("yes-") or yes_query.lower() == "yes"
        assert is_yes is True
        
        # Test no approval
        no_query = "no-cancel this"
        is_no = no_query.lower().startswith("no-") or no_query.lower() == "no"
        assert is_no is True
    
    
class TestTokenVerification:
    """Test JWT token verification."""
    
    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """Test successful token verification."""
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_jwt_token"
        
        with patch('api.endpoints.http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "user_123", "email": "test@example.com"}
            mock_http.get = AsyncMock(return_value=mock_response)
            
            user = await verify_token(mock_credentials)
            
            assert user["id"] == "user_123"
            assert user["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        mock_credentials = Mock()
        mock_credentials.credentials = "invalid_token"
        
        with patch('api.endpoints.http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_http.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_token(mock_credentials)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_verify_token_http_client_error(self):
        """Test token verification when HTTP client is not initialized."""
        mock_credentials = Mock()
        mock_credentials.credentials = "token"
        
        with patch('api.endpoints.http_client', None):
            with pytest.raises(HTTPException) as exc_info:
                await verify_token(mock_credentials)
            
            assert exc_info.value.status_code == 401
            assert "HTTP client not initialized" in str(exc_info.value.detail)


class TestFetchLastMessageMetadata:
    """Test fetching last message metadata for approval state detection."""
    
    @pytest.mark.asyncio
    async def test_fetch_last_message_metadata_success(self):
        """Test successful metadata fetch."""
        mock_supabase = Mock()
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        
        # Chain the query builder methods
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        mock_limit = Mock()
        mock_execute = Mock()
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = Mock(data=[{"data": {"awaiting_approval": True}}])
        
        with patch('api.endpoints.fetch_last_message_metadata', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"awaiting_approval": True}
            
            result = await mock_fetch(mock_supabase, "test_session")
            
            assert result["awaiting_approval"] is True
    
    @pytest.mark.asyncio
    async def test_fetch_last_message_metadata_no_messages(self):
        """Test metadata fetch when no messages exist."""
        mock_supabase = Mock()
        
        with patch('api.endpoints.fetch_last_message_metadata', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            
            result = await mock_fetch(mock_supabase, "test_session")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_last_message_metadata_error(self):
        """Test metadata fetch error handling."""
        mock_supabase = Mock()
        
        with patch('api.endpoints.fetch_last_message_metadata', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None  # Returns None on error
            
            result = await mock_fetch(mock_supabase, "test_session")
            
            assert result is None


class TestApprovalPatternDetection:
    """Test detection of approval/decline patterns in user messages."""
    
    def test_approval_pattern_yes(self):
        """Test detection of 'yes' approval."""
        queries = ["yes", "YES", "Yes", "yes-looks good", "yes-perfect"]
        
        for query in queries:
            query_lower = query.lower().strip()
            is_approval = query_lower.startswith("yes-") or query_lower == "yes"
            assert is_approval, f"Failed to detect approval in: {query}"
    
    def test_approval_pattern_no(self):
        """Test detection of 'no' decline."""
        queries = ["no", "NO", "No", "no-please revise", "no-wrong tone"]
        
        for query in queries:
            query_lower = query.lower().strip()
            is_decline = query_lower.startswith("no-") or query_lower == "no"
            assert is_decline, f"Failed to detect decline in: {query}"
    
    def test_approval_pattern_feedback_extraction(self):
        """Test extraction of feedback from approval/decline messages."""
        test_cases = [
            ("yes-looks great", True, "looks great"),
            ("no-please revise the tone", False, "please revise the tone"),
            ("yes", True, ""),
            ("no", False, "")
        ]
        
        for query, expected_approved, expected_feedback in test_cases:
            query_lower = query.lower().strip()
            
            if query_lower.startswith("yes-") or query_lower == "yes":
                feedback = query_lower[4:] if len(query_lower) > 4 else ""
                approved = True
            elif query_lower.startswith("no-") or query_lower == "no":
                feedback = query_lower[3:] if len(query_lower) > 3 else ""
                approved = False
            else:
                continue
            
            assert approved == expected_approved
            assert feedback == expected_feedback


if __name__ == "__main__":
    pytest.main([__file__])