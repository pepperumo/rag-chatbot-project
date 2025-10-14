"""
Unit tests for the tool functions (Brave search and Gmail).

Tests both Brave search and Gmail tool functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
import httpx

from tools.brave_tools import search_web_tool
from tools.gmail_tools import create_email_draft_tool, list_email_drafts_tool


class TestBraveSearchTool:
    """Test cases for Brave search tool functionality"""

    @pytest.mark.asyncio
    async def test_search_web_tool_success(self):
        """Test successful Brave search"""
        mock_response_data = {
            "web": {
                "results": [
                    {
                        "title": "Test Result 1",
                        "url": "https://example.com/1",
                        "description": "First test result"
                    },
                    {
                        "title": "Test Result 2", 
                        "url": "https://example.com/2",
                        "description": "Second test result"
                    }
                ]
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await search_web_tool(
                api_key="test-api-key",
                query="test query",
                count=2
            )
            
            # Verify results
            assert len(result) == 2
            assert result[0]["title"] == "Test Result 1"
            assert result[0]["url"] == "https://example.com/1"
            assert result[0]["description"] == "First test result"
            assert result[0]["score"] == 1.0  # First result gets highest score
            
            assert result[1]["score"] == 0.95  # Second result gets lower score

    @pytest.mark.asyncio
    async def test_search_web_tool_invalid_api_key(self):
        """Test Brave search with invalid API key"""
        with pytest.raises(ValueError, match="Brave API key is required"):
            await search_web_tool(
                api_key="",
                query="test query"
            )
        
        with pytest.raises(ValueError, match="Brave API key is required"):
            await search_web_tool(
                api_key=None,
                query="test query"
            )

    @pytest.mark.asyncio
    async def test_search_web_tool_empty_query(self):
        """Test Brave search with empty query"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_web_tool(
                api_key="test-api-key",
                query=""
            )
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_web_tool(
                api_key="test-api-key",
                query=None
            )

    @pytest.mark.asyncio
    async def test_search_web_tool_count_validation(self):
        """Test Brave search count parameter validation"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"web": {"results": []}}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test upper bound
            await search_web_tool(
                api_key="test-api-key",
                query="test",
                count=25
            )
            
            # Check that the actual API call used count=20
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            assert call_args[1]["params"]["count"] == 20
            
            # Test lower bound
            await search_web_tool(
                api_key="test-api-key", 
                query="test",
                count=0
            )
            
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            assert call_args[1]["params"]["count"] == 1

    @pytest.mark.asyncio
    async def test_search_web_tool_api_errors(self):
        """Test Brave search API error handling"""
        test_cases = [
            (401, "Invalid Brave API key"),
            (429, "Rate limit exceeded. Check your Brave API quota."),
            (500, "Brave API returned 500:")
        ]
        
        for status_code, expected_error in test_cases:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_response.text = "Error details"
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                with pytest.raises(Exception) as exc_info:
                    await search_web_tool(
                        api_key="test-api-key",
                        query="test query"
                    )
                
                assert expected_error in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_web_tool_request_error(self):
        """Test Brave search request error handling"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError("Network error")
            
            with pytest.raises(Exception, match="Request failed: Network error"):
                await search_web_tool(
                    api_key="test-api-key",
                    query="test query"
                )

    @pytest.mark.asyncio
    async def test_search_web_tool_with_filters(self):
        """Test Brave search with country and language filters"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"web": {"results": []}}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            await search_web_tool(
                api_key="test-api-key",
                query="test query",
                country="US",
                lang="en"
            )
            
            # Verify filters were included in request
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            params = call_args[1]["params"]
            assert params["country"] == "US"
            assert params["lang"] == "en"


class TestGmailTools:
    """Test cases for Gmail tool functionality"""

    @pytest.mark.asyncio
    async def test_create_email_draft_tool_success(self):
        """Test successful Gmail draft creation"""
        mock_draft_response = {
            "id": "draft_123",
            "message": {
                "id": "msg_456",
                "threadId": "thread_789"
            }
        }
        
        with patch('tools.gmail_tools._get_gmail_service') as mock_service:
            mock_service.return_value.users.return_value.drafts.return_value.create.return_value.execute.return_value = mock_draft_response
            
            result = await create_email_draft_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                to=["test@example.com"],
                subject="Test Subject",
                body="Test body content"
            )
            
            # Verify result structure
            assert result["success"] is True
            assert result["draft_id"] == "draft_123"
            assert result["message_id"] == "msg_456"
            assert result["thread_id"] == "thread_789"
            assert result["recipients"] == ["test@example.com"]
            assert result["subject"] == "Test Subject"

    @pytest.mark.asyncio
    async def test_create_email_draft_tool_validation(self):
        """Test Gmail draft creation input validation"""
        # Test empty recipients
        with pytest.raises(ValueError, match="At least one recipient is required"):
            await create_email_draft_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                to=[],
                subject="Test",
                body="Test"
            )
        
        # Test empty subject
        with pytest.raises(ValueError, match="Subject is required"):
            await create_email_draft_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                to=["test@example.com"],
                subject="",
                body="Test"
            )
        
        # Test empty body
        with pytest.raises(ValueError, match="Body is required"):
            await create_email_draft_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                to=["test@example.com"],
                subject="Test",
                body=""
            )

    @pytest.mark.asyncio
    async def test_create_email_draft_tool_with_cc_bcc(self):
        """Test Gmail draft creation with CC and BCC"""
        mock_draft_response = {
            "id": "draft_123",
            "message": {"id": "msg_456", "threadId": "thread_789"}
        }
        
        with patch('tools.gmail_tools._get_gmail_service') as mock_service:
            mock_service.return_value.users.return_value.drafts.return_value.create.return_value.execute.return_value = mock_draft_response
            
            result = await create_email_draft_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                to=["test@example.com"],
                subject="Test Subject",
                body="Test body",
                cc=["cc@example.com"],
                bcc=["bcc@example.com"]
            )
            
            assert result["success"] is True
            assert result["draft_id"] == "draft_123"

    @pytest.mark.asyncio
    async def test_create_email_draft_tool_gmail_error(self):
        """Test Gmail draft creation error handling"""
        from googleapiclient.errors import HttpError
        
        with patch('tools.gmail_tools._get_gmail_service') as mock_service:
            mock_service.side_effect = HttpError(
                resp=MagicMock(status=403),
                content=b'Access denied'
            )
            
            with pytest.raises(Exception, match="Failed to create draft"):
                await create_email_draft_tool(
                    credentials_path="test/creds.json",
                    token_path="test/token.json",
                    to=["test@example.com"],
                    subject="Test",
                    body="Test"
                )

    @pytest.mark.asyncio
    async def test_list_email_drafts_tool_success(self):
        """Test successful Gmail drafts listing"""
        mock_list_response = {
            "drafts": [
                {"id": "draft_1", "message": {"id": "msg_1"}},
                {"id": "draft_2", "message": {"id": "msg_2"}}
            ]
        }
        
        with patch('tools.gmail_tools._get_gmail_service') as mock_service:
            mock_service.return_value.users.return_value.drafts.return_value.list.return_value.execute.return_value = mock_list_response
            
            result = await list_email_drafts_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json",
                max_results=10
            )
            
            # Verify result
            assert result["success"] is True
            assert len(result["drafts"]) == 2
            assert result["count"] == 2
            assert result["drafts"][0]["id"] == "draft_1"

    @pytest.mark.asyncio
    async def test_list_email_drafts_tool_empty(self):
        """Test Gmail drafts listing with no drafts"""
        mock_list_response = {"drafts": []}
        
        with patch('tools.gmail_tools._get_gmail_service') as mock_service:
            mock_service.return_value.users.return_value.drafts.return_value.list.return_value.execute.return_value = mock_list_response
            
            result = await list_email_drafts_tool(
                credentials_path="test/creds.json",
                token_path="test/token.json"
            )
            
            assert result["success"] is True
            assert result["drafts"] == []
            assert result["count"] == 0

    def test_gmail_message_creation(self):
        """Test Gmail message creation helper function"""
        from tools.gmail_tools import _create_email_message
        
        message = _create_email_message(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test body content"
        )
        
        assert "raw" in message
        assert isinstance(message["raw"], str)
        
        # Test with CC and BCC
        message_with_cc = _create_email_message(
            to=["test@example.com"],
            subject="Test Subject", 
            body="Test body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )
        
        assert "raw" in message_with_cc
        assert isinstance(message_with_cc["raw"], str)