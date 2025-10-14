"""
Unit tests for the email search agent functionality.

Tests Gmail search, mock API responses, and verify readonly scope.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from googleapiclient.errors import HttpError
from typing import List, Dict, Any

from agents.email_search_agent import email_search_agent
from agents.deps import AgentDependencies
from tools.email_tools import search_emails_tool, get_email_content_tool


@pytest.fixture
def mock_agent_deps():
    """Create mock agent dependencies for email search"""
    return AgentDependencies(
        brave_api_key="test-brave-api-key",
        gmail_credentials_path="test/credentials.json",
        gmail_token_path="test/token.json",
        supabase=MagicMock(),
        embedding_client=MagicMock(),
        http_client=MagicMock(),
        session_id="test-session-123"
    )


@pytest.fixture
def mock_gmail_service():
    """Create mock Gmail service"""
    service = MagicMock()
    
    # Mock messages().list() chain
    service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [
            {"id": "msg1"},
            {"id": "msg2"},
            {"id": "msg3"}
        ]
    }
    
    # Mock messages().get() chain for metadata
    def mock_get_message(userId, id, format):
        if id == "msg1":
            return MagicMock(execute=MagicMock(return_value={
                "id": "msg1",
                "snippet": "This is the first email snippet",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Project Update"},
                        {"name": "From", "value": "john@example.com"},
                        {"name": "Date", "value": "Mon, 01 Jan 2024 10:00:00 +0000"}
                    ]
                }
            }))
        elif id == "msg2":
            return MagicMock(execute=MagicMock(return_value={
                "id": "msg2",
                "snippet": "This is the second email snippet",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Meeting Notes"},
                        {"name": "From", "value": "sarah@example.com"},
                        {"name": "Date", "value": "Tue, 02 Jan 2024 14:30:00 +0000"}
                    ]
                }
            }))
        else:
            return MagicMock(execute=MagicMock(return_value={
                "id": "msg3",
                "snippet": "This is the third email snippet",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Budget Review"},
                        {"name": "From", "value": "finance@example.com"},
                        {"name": "Date", "value": "Wed, 03 Jan 2024 09:15:00 +0000"}
                    ]
                }
            }))
    
    service.users.return_value.messages.return_value.get.side_effect = mock_get_message
    
    return service


@pytest.fixture
def mock_email_search_results():
    """Create mock email search results"""
    return [
        {
            "id": "msg1",
            "subject": "Project Update",
            "from": "john@example.com",
            "date": "Mon, 01 Jan 2024 10:00:00 +0000",
            "snippet": "This is the first email snippet"
        },
        {
            "id": "msg2",
            "subject": "Meeting Notes",
            "from": "sarah@example.com",
            "date": "Tue, 02 Jan 2024 14:30:00 +0000",
            "snippet": "This is the second email snippet"
        }
    ]


class TestEmailSearchAgent:
    """Test cases for email search agent functionality"""

    @pytest.mark.asyncio
    async def test_search_emails_tool_success(self, mock_gmail_service):
        """Test successful email search using Gmail API"""
        query = "from:john@example.com subject:project"
        
        with patch('tools.email_tools._get_gmail_service', return_value=mock_gmail_service):
            result = await search_emails_tool(
                credentials_path="test/credentials.json",
                token_path="test/token.json",
                query=query,
                max_results=10
            )
            
            assert result["success"] is True
            assert result["count"] == 3
            assert len(result["results"]) == 3
            
            # Check first result
            first_result = result["results"][0]
            assert first_result["id"] == "msg1"
            assert first_result["subject"] == "Project Update"
            assert first_result["from"] == "john@example.com"
            assert "snippet" in first_result

    @pytest.mark.asyncio
    async def test_search_emails_tool_readonly_scope(self):
        """Test that Gmail search uses readonly scope"""
        query = "test query"
        
        with patch('tools.email_tools._get_gmail_service') as mock_service_func:
            mock_service = MagicMock()
            mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
                "messages": []
            }
            mock_service_func.return_value = mock_service
            
            await search_emails_tool(
                credentials_path="test/credentials.json",
                token_path="test/token.json",
                query=query
            )
            
            # Verify readonly scope was used
            mock_service_func.assert_called_once()
            call_args = mock_service_func.call_args[0]
            scopes = call_args[2]  # Third argument is scopes
            assert scopes == ["https://www.googleapis.com/auth/gmail.readonly"]

    @pytest.mark.asyncio
    async def test_search_emails_tool_query_validation(self):
        """Test email search tool validates query"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_emails_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                query=""
            )
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_emails_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                query="   "
            )

    @pytest.mark.asyncio
    async def test_search_emails_tool_max_results_limit(self, mock_gmail_service):
        """Test email search tool enforces max results limit"""
        query = "test query"
        
        with patch('tools.email_tools._get_gmail_service', return_value=mock_gmail_service):
            # Test max_results gets clamped to 50
            await search_emails_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                query=query,
                max_results=100
            )
            
            # Verify maxResults was clamped to 50
            call = mock_gmail_service.users.return_value.messages.return_value.list.call_args[1]
            assert call["maxResults"] == 50

    @pytest.mark.asyncio
    async def test_search_emails_tool_http_error(self):
        """Test email search tool handles Gmail API errors"""
        query = "test query"
        
        with patch('tools.email_tools._get_gmail_service') as mock_service_func:
            mock_service = MagicMock()
            mock_service.users.return_value.messages.return_value.list.return_value.execute.side_effect = HttpError(
                resp=MagicMock(status=403), content=b"Forbidden"
            )
            mock_service_func.return_value = mock_service
            
            result = await search_emails_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                query=query
            )
            
            assert result["success"] is False
            assert "Gmail API error" in result["error"]
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_search_emails_tool_general_error(self):
        """Test email search tool handles general errors"""
        query = "test query"
        
        with patch('tools.email_tools._get_gmail_service', side_effect=Exception("Service error")):
            result = await search_emails_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                query=query
            )
            
            assert result["success"] is False
            assert "Service error" in result["error"]
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_email_content_tool_success(self):
        """Test successful email content retrieval"""
        message_id = "test-message-id"
        
        mock_service = MagicMock()
        mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": message_id,
            "snippet": "Email snippet",
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Date", "value": "Mon, 01 Jan 2024 12:00:00 +0000"}
                ],
                "body": {
                    "data": "VGVzdCBlbWFpbCBjb250ZW50"  # Base64 encoded "Test email content"
                }
            }
        }
        
        with patch('tools.email_tools._get_gmail_service', return_value=mock_service):
            result = await get_email_content_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                message_id=message_id
            )
            
            assert result["success"] is True
            assert result["message_id"] == message_id
            assert result["subject"] == "Test Subject"
            assert result["from"] == "sender@example.com"
            assert result["to"] == "recipient@example.com"
            assert result["body"] == "Test email content"

    @pytest.mark.asyncio
    async def test_get_email_content_tool_validation(self):
        """Test email content tool validates message ID"""
        with pytest.raises(ValueError, match="Message ID cannot be empty"):
            await get_email_content_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                message_id=""
            )

    @pytest.mark.asyncio
    async def test_email_search_agent_tool_integration(self, mock_agent_deps):
        """Test email search agent tool integration"""
        query = "from:john project"
        max_results = 5
        
        mock_results = {
            "success": True,
            "results": [
                {"id": "msg1", "subject": "Project Update", "from": "john@example.com"}
            ],
            "count": 1
        }
        
        with patch('agents.email_search_agent.search_emails_tool', return_value=mock_results) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_agent_deps
            
            from agents.email_search_agent import search_emails
            result = await search_emails(mock_ctx, query, max_results)
            
            mock_search.assert_called_once_with(
                credentials_path=mock_agent_deps.gmail_credentials_path,
                token_path=mock_agent_deps.gmail_token_path,
                query=query,
                max_results=max_results
            )
            
            assert result == mock_results

    @pytest.mark.asyncio
    async def test_email_search_agent_tool_error_handling(self, mock_agent_deps):
        """Test email search agent tool error handling"""
        query = "test query"
        
        with patch('agents.email_search_agent.search_emails_tool', side_effect=Exception("Gmail Error")) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_agent_deps
            
            from agents.email_search_agent import search_emails
            result = await search_emails(mock_ctx, query, 10)
            
            assert result["success"] is False
            assert "Gmail Error" in result["error"]
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_email_content_agent_tool(self, mock_agent_deps):
        """Test get email content agent tool"""
        message_id = "test-msg-id"
        
        mock_result = {
            "success": True,
            "message_id": message_id,
            "subject": "Test Email",
            "body": "Email content"
        }
        
        with patch('agents.email_search_agent.get_email_content_tool', return_value=mock_result) as mock_get:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_agent_deps
            
            from agents.email_search_agent import get_email_content
            result = await get_email_content(mock_ctx, message_id)
            
            mock_get.assert_called_once_with(
                credentials_path=mock_agent_deps.gmail_credentials_path,
                token_path=mock_agent_deps.gmail_token_path,
                message_id=message_id
            )
            
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_format_email_results_tool(self, mock_agent_deps, mock_email_search_results):
        """Test email results formatting tool"""
        query = "test query"
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_agent_deps
        
        from agents.email_search_agent import format_email_results
        result = await format_email_results(mock_ctx, mock_email_search_results, query)
        
        assert isinstance(result, dict)
        assert "summary" in result
        assert "email_count" in result
        assert "formatted_results" in result
        assert "query" in result
        
        assert result["query"] == query
        assert result["email_count"] == len(mock_email_search_results)
        assert len(result["formatted_results"]) == len(mock_email_search_results)
        
        # Check formatting includes key fields
        summary = result["summary"]
        assert query in summary
        assert "Project Update" in summary
        assert "john@example.com" in summary

    @pytest.mark.asyncio
    async def test_format_email_results_empty(self, mock_agent_deps):
        """Test formatting with empty email results"""
        query = "no results query"
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_agent_deps
        
        from agents.email_search_agent import format_email_results
        result = await format_email_results(mock_ctx, [], query)
        
        assert result["summary"] == f"No emails found for query: '{query}'"
        assert result["email_count"] == 0
        assert result["formatted_results"] == []

    @pytest.mark.asyncio
    async def test_email_search_agent_configuration(self):
        """Test email search agent configuration"""
        # Test that email search agent can be imported
        from agents.email_search_agent import email_search_agent
        from agents.deps import AgentDependencies
        
        # Verify basic functionality
        assert email_search_agent is not None
        assert AgentDependencies is not None
        
        # Test that AgentDependencies has Gmail-related fields
        deps = AgentDependencies(
            brave_api_key="test",
            gmail_credentials_path="test/creds.json", 
            gmail_token_path="test/token.json",
            supabase=None,
            embedding_client=None,
            http_client=None
        )
        assert deps.gmail_credentials_path == "test/creds.json"
        assert deps.gmail_token_path == "test/token.json"

    @pytest.mark.asyncio
    async def test_gmail_query_syntax_support(self, mock_gmail_service):
        """Test that Gmail query syntax is properly passed through"""
        # Test various Gmail query operators
        test_queries = [
            "from:john@example.com",
            "subject:project",
            "from:john subject:project",
            "has:attachment",
            "before:2024/01/01",
            "after:2023/12/01",
            "is:unread"
        ]
        
        with patch('tools.email_tools._get_gmail_service', return_value=mock_gmail_service):
            for query in test_queries:
                result = await search_emails_tool(
                    credentials_path="test/creds.json",
                    token_path="test/token.json",
                    query=query
                )
                
                # Verify the query was passed through correctly
                call_args = mock_gmail_service.users.return_value.messages.return_value.list.call_args[1]
                assert call_args["q"] == query
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_email_search_agent_streaming_mock(self, mock_agent_deps):
        """Test email search agent streaming capabilities (mocked)"""
        query = "test streaming query"
        
        # Mock the agent's run_stream method
        mock_stream_result = MagicMock()
        mock_stream_result.stream_text.return_value = AsyncMock()
        mock_stream_result.stream_text.return_value.__aiter__ = AsyncMock(return_value=iter(["chunk1", "chunk2", "chunk3"]))
        
        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_stream_result)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(email_search_agent, 'run_stream', return_value=mock_context_manager):
            # Test that we can create the stream context
            stream_context = email_search_agent.run_stream(query, deps=mock_agent_deps)
            assert stream_context is not None

    @pytest.mark.asyncio
    async def test_gmail_service_authentication_flow(self):
        """Test Gmail service authentication flow and scope handling"""
        credentials_path = "test/credentials.json"
        token_path = "test/token.json"
        
        with patch('tools.email_tools.os.path.exists') as mock_exists, \
             patch('tools.email_tools.Credentials.from_authorized_user_file') as mock_from_file, \
             patch('tools.email_tools.build') as mock_build:
            
            # Test case: token exists and is valid
            mock_exists.return_value = True
            mock_creds = MagicMock()
            mock_creds.valid = True
            mock_from_file.return_value = mock_creds
            
            from tools.email_tools import _get_gmail_service
            service = _get_gmail_service(
                credentials_path, 
                token_path, 
                ["https://www.googleapis.com/auth/gmail.readonly"]
            )
            
            # Verify readonly scope was used
            mock_from_file.assert_called_once_with(
                token_path, 
                ["https://www.googleapis.com/auth/gmail.readonly"]
            )
            mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)

    @pytest.mark.asyncio
    async def test_email_message_header_parsing(self, mock_gmail_service):
        """Test proper parsing of email headers"""
        query = "test"
        
        # Modify mock to test header parsing edge cases
        mock_gmail_service.users.return_value.messages.return_value.get.side_effect = lambda userId, id, format: MagicMock(
            execute=MagicMock(return_value={
                "id": id,
                "snippet": "Test snippet",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Test Subject"},
                        {"name": "From", "value": "test@example.com"},
                        {"name": "Date", "value": "Mon, 01 Jan 2024 12:00:00 +0000"},
                        {"name": "Other-Header", "value": "Other Value"}
                    ]
                }
            })
        )
        
        with patch('tools.email_tools._get_gmail_service', return_value=mock_gmail_service):
            result = await search_emails_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                query=query
            )
            
            assert result["success"] is True
            assert len(result["results"]) > 0
            
            # Check that headers were parsed correctly
            email = result["results"][0]
            assert email["subject"] == "Test Subject"
            assert email["from"] == "test@example.com"
            assert email["date"] == "Mon, 01 Jan 2024 12:00:00 +0000"