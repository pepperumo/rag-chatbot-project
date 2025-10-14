"""
Tests for the tools module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
import sys
import os

# Import the tools directly
from ..tools import (
    brave_web_search,
    searxng_web_search,
    web_search_tool
)


class TestBraveWebSearch:
    """Tests for the brave_web_search function."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        client = AsyncMock(spec=AsyncClient)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Test Result 1",
                        "url": "https://example.com/1",
                        "description": "This is test result 1",
                    },
                    {
                        "title": "Test Result 2",
                        "url": "https://example.com/2",
                        "description": "This is test result 2",
                    },
                ]
            }
        }
        client.get.return_value = mock_response
        return client

    @pytest.mark.asyncio
    async def test_brave_web_search_success(self, mock_client):
        """Test successful web search with Brave."""
        result = await brave_web_search("test query", mock_client, "test_api_key")

        # Verify the client was called with the correct parameters
        mock_client.get.assert_called_once()
        args, kwargs = mock_client.get.call_args
        assert args[0] == "https://api.search.brave.com/res/v1/web/search"
        assert kwargs["headers"]["X-Subscription-Token"] == "test_api_key"
        assert kwargs["params"]["q"] == "test query"

        # Verify the result is a string and contains expected content
        assert isinstance(result, str)
        assert "Test Result 1" in result
        assert "https://example.com/1" in result
        assert "This is test result 1" in result

    @pytest.mark.asyncio
    async def test_brave_web_search_http_error(self, mock_client):
        """Test web search with HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_client.get.return_value = mock_response

        # The function should catch the exception and return it as a string
        result = await brave_web_search("test query", mock_client, "test_api_key")
        assert "HTTP Error" in result


class TestSearXNGWebSearch:
    """Tests for the searxng_web_search function."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        client = AsyncMock(spec=AsyncClient)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Test Result 1",
                    "url": "https://example.com/1",
                    "content": "This is test result 1",
                },
                {
                    "title": "Test Result 2",
                    "url": "https://example.com/2",
                    "content": "This is test result 2",
                },
            ]
        }
        client.get.return_value = mock_response
        return client

    @pytest.mark.asyncio
    async def test_searxng_web_search_success(self, mock_client):
        """Test successful web search with SearXNG."""
        result = await searxng_web_search("test query", mock_client, "https://searx.example.com")

        # Verify the client was called with the correct parameters
        mock_client.get.assert_called_once()
        args, kwargs = mock_client.get.call_args
        assert args[0] == "https://searx.example.com/search"
        assert kwargs["params"]["q"] == "test query"
        assert kwargs["params"]["format"] == "json"

        # Verify the result is a string and contains expected content
        assert isinstance(result, str)
        assert "Test Result 1" in result
        assert "https://example.com/1" in result
        assert "This is test result 1" in result

    @pytest.mark.asyncio
    async def test_searxng_web_search_http_error(self, mock_client):
        """Test web search with HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_client.get.return_value = mock_response

        # The function should catch the exception and return it as a string
        result = await searxng_web_search("test query", mock_client, "https://searx.example.com")
        assert "HTTP Error" in result


class TestWebSearchTool:
    """Tests for the web_search_tool function."""

    @pytest.fixture
    def mock_brave_search(self):
        """Create a mock for brave_web_search."""
        with patch("src.tools.brave_web_search") as mock:
            mock.return_value = "Brave search result for test query"
            yield mock

    @pytest.fixture
    def mock_searxng_search(self):
        """Create a mock for searxng_web_search."""
        with patch("src.tools.searxng_web_search") as mock:
            mock.return_value = "SearXNG search result for test query"
            yield mock

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return AsyncMock(spec=AsyncClient)

    @pytest.mark.asyncio
    async def test_web_search_tool_brave(self, mock_client, mock_brave_search, mock_searxng_search):
        """Test web search tool with Brave."""
        result = await web_search_tool("test query", mock_client, "test_api_key", None)

        # Verify that brave_web_search was called
        mock_brave_search.assert_called_once_with("test query", mock_client, "test_api_key")
        mock_searxng_search.assert_not_called()

        # Verify the result
        assert result == "Brave search result for test query"

    @pytest.mark.asyncio
    async def test_web_search_tool_searxng(self, mock_client, mock_brave_search, mock_searxng_search):
        """Test web search tool with SearXNG."""
        result = await web_search_tool("test query", mock_client, None, "https://searx.example.com")

        # Verify that searxng_web_search was called
        mock_searxng_search.assert_called_once_with("test query", mock_client, "https://searx.example.com")
        mock_brave_search.assert_not_called()

        # Verify the result
        assert result == "SearXNG search result for test query"

    @pytest.mark.asyncio
    async def test_web_search_tool_no_provider(self, mock_client, mock_brave_search, mock_searxng_search):
        """Test web search tool with no provider configured."""
        result = await web_search_tool("test query", mock_client, None, None)

        # Verify neither search function was called
        mock_brave_search.assert_not_called()
        mock_searxng_search.assert_not_called()

        # Verify the result contains the expected error message
        assert "No search provider configured" in result
