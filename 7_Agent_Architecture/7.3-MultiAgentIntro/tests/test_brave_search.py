"""
Tests for Brave Search Tool.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from agents.tools import search_web_tool
from agents.models import BraveSearchResult


class TestBraveSearchTool:
    """Tests for Brave Search pure function."""
    
    @pytest.mark.asyncio
    async def test_search_empty_query_raises_error(self):
        """Test search with empty query raises error."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_web_tool(api_key="test_key", query="")
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_web_tool(api_key="test_key", query="   ")
    
    @pytest.mark.asyncio
    async def test_search_empty_api_key_raises_error(self):
        """Test search with empty API key raises error."""
        with pytest.raises(ValueError, match="Brave API key is required"):
            await search_web_tool(api_key="", query="test query")
        
        with pytest.raises(ValueError, match="Brave API key is required"):
            await search_web_tool(api_key=None, query="test query")
    
    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search."""
        # Mock response data
        mock_response_data = {
            "web": {
                "results": [
                    {
                        "title": "Test Result 1",
                        "url": "https://example.com/1",
                        "description": "Test description 1"
                    },
                    {
                        "title": "Test Result 2",
                        "url": "https://example.com/2",
                        "description": "Test description 2"
                    }
                ]
            }
        }
        
        # Mock httpx client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context_manager
            
            results = await search_web_tool(api_key="test_key", query="test query", count=2)
        
        assert len(results) == 2
        assert results[0]["title"] == "Test Result 1"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["description"] == "Test description 1"
        assert results[0]["score"] == 1.0  # First result gets max score
        
        assert results[1]["title"] == "Test Result 2"
        assert results[1]["score"] == 0.95  # Second result gets slightly lower score
    
    @pytest.mark.asyncio
    async def test_search_rate_limit_error(self):
        """Test search with rate limit error."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context_manager
            
            with pytest.raises(Exception, match="Rate limit exceeded"):
                await search_web_tool(api_key="test_key", query="test query")
    
    @pytest.mark.asyncio
    async def test_search_invalid_api_key_error(self):
        """Test search with invalid API key."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context_manager
            
            with pytest.raises(Exception, match="Invalid Brave API key"):
                await search_web_tool(api_key="invalid_key", query="test query")
    
    @pytest.mark.asyncio
    async def test_search_http_error(self):
        """Test search with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context_manager
            
            with pytest.raises(Exception, match="Brave API returned 500"):
                await search_web_tool(api_key="test_key", query="test query")
    
    @pytest.mark.asyncio
    async def test_search_request_error(self):
        """Test search with request error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            mock_client.return_value = mock_context_manager
            
            with pytest.raises(Exception, match="Request failed"):
                await search_web_tool(api_key="test_key", query="test query")
    
    @pytest.mark.asyncio
    async def test_search_count_limits(self):
        """Test search count parameter limits."""
        mock_response_data = {"web": {"results": []}}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context_manager = AsyncMock()
            mock_get = AsyncMock(return_value=mock_response)
            mock_context_manager.__aenter__.return_value.get = mock_get
            mock_client.return_value = mock_context_manager
            
            # Test count below minimum (should be adjusted to 1)
            await search_web_tool(api_key="test_key", query="test", count=0)
            args, kwargs = mock_get.call_args
            assert kwargs['params']['count'] == 1
            
            # Test count above maximum (should be adjusted to 20)
            await search_web_tool(api_key="test_key", query="test", count=50)
            args, kwargs = mock_get.call_args
            assert kwargs['params']['count'] == 20


@pytest.mark.asyncio
async def test_search_web_tool_function():
    """Test the search_web_tool function."""
    mock_response_data = {
        "web": {
            "results": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "description": "Test description"
                }
            ]
        }
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context_manager
        
        results = await search_web_tool(api_key="test_key", query="test query", count=1)
    
    assert len(results) == 1
    assert results[0]["title"] == "Test Result"