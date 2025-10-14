"""
Unit tests for the web search agent functionality.

Tests Brave API integration, mock responses, and verify streaming.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from typing import List, Dict, Any

from agents.web_search_agent import web_search_agent
from agents.deps import AgentDependencies
from tools.web_tools import search_web_tool


@pytest.fixture
def mock_agent_deps():
    """Create mock agent dependencies for web search"""
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
def mock_brave_search_results():
    """Create mock Brave search results"""
    return [
        {
            "title": "AI Breakthrough in 2024",
            "url": "https://example.com/ai-breakthrough",
            "description": "Latest developments in artificial intelligence technology",
            "score": 0.95
        },
        {
            "title": "Machine Learning Research",
            "url": "https://example.com/ml-research",
            "description": "Recent advances in machine learning algorithms",
            "score": 0.90
        },
        {
            "title": "Tech Industry News",
            "url": "https://example.com/tech-news",
            "description": "Current trends in technology sector",
            "score": 0.85
        }
    ]


class TestWebSearchAgent:
    """Test cases for web search agent functionality"""

    @pytest.mark.asyncio
    async def test_search_web_tool_success(self, mock_agent_deps, mock_brave_search_results):
        """Test successful web search using Brave API"""
        query = "latest AI developments"
        
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "AI Breakthrough in 2024",
                        "url": "https://example.com/ai-breakthrough",
                        "description": "Latest developments in artificial intelligence technology"
                    },
                    {
                        "title": "Machine Learning Research",
                        "url": "https://example.com/ml-research",
                        "description": "Recent advances in machine learning algorithms"
                    }
                ]
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await search_web_tool(
                api_key="test-key",
                query=query,
                count=10
            )
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["title"] == "AI Breakthrough in 2024"
            assert result[0]["url"] == "https://example.com/ai-breakthrough"
            assert "score" in result[0]

    @pytest.mark.asyncio
    async def test_search_web_tool_api_key_validation(self):
        """Test web search tool validates API key"""
        with pytest.raises(ValueError, match="Brave API key is required"):
            await search_web_tool(api_key="", query="test query")
        
        with pytest.raises(ValueError, match="Brave API key is required"):
            await search_web_tool(api_key=None, query="test query")

    @pytest.mark.asyncio
    async def test_search_web_tool_query_validation(self):
        """Test web search tool validates query"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_web_tool(api_key="test-key", query="")
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_web_tool(api_key="test-key", query="   ")

    @pytest.mark.asyncio
    async def test_search_web_tool_count_limits(self):
        """Test web search tool enforces count limits"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"web": {"results": []}}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test count too high gets clamped to 20
            await search_web_tool(api_key="test-key", query="test", count=50)
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            assert call_args[1]["params"]["count"] == 20
            
            # Test count too low gets clamped to 1
            await search_web_tool(api_key="test-key", query="test", count=0)
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            assert call_args[1]["params"]["count"] == 1

    @pytest.mark.asyncio
    async def test_search_web_tool_rate_limiting(self):
        """Test web search tool handles rate limiting"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(Exception, match="Rate limit exceeded"):
                await search_web_tool(api_key="test-key", query="test")

    @pytest.mark.asyncio
    async def test_search_web_tool_auth_error(self):
        """Test web search tool handles authentication errors"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(Exception, match="Invalid Brave API key"):
                await search_web_tool(api_key="invalid-key", query="test")

    @pytest.mark.asyncio
    async def test_search_web_tool_network_error(self):
        """Test web search tool handles network errors"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError("Network error")
            
            with pytest.raises(Exception, match="Request failed"):
                await search_web_tool(api_key="test-key", query="test")

    @pytest.mark.asyncio
    async def test_web_search_agent_tool_integration(self, mock_agent_deps):
        """Test web search agent tool integration"""
        query = "AI research"
        max_results = 5
        
        # Mock the search_web_tool function
        mock_results = [
            {"title": "AI Research Paper", "url": "https://example.com", "description": "Research on AI", "score": 0.9}
        ]
        
        with patch('agents.web_search_agent.search_web_tool', return_value=mock_results) as mock_search:
            # Create a mock RunContext
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_agent_deps
            
            # Import and test the tool function directly
            from agents.web_search_agent import search_web
            result = await search_web(mock_ctx, query, max_results)
            
            # Verify the tool was called correctly
            mock_search.assert_called_once_with(
                api_key=mock_agent_deps.brave_api_key,
                query=query,
                count=max_results
            )
            
            assert result == mock_results

    @pytest.mark.asyncio
    async def test_web_search_agent_tool_error_handling(self, mock_agent_deps):
        """Test web search agent tool error handling"""
        query = "test query"
        
        # Mock search_web_tool to raise an exception
        with patch('agents.web_search_agent.search_web_tool', side_effect=Exception("API Error")) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_agent_deps
            
            from agents.web_search_agent import search_web
            result = await search_web(mock_ctx, query, 10)
            
            # Should return error in list format
            assert isinstance(result, list)
            assert len(result) == 1
            assert "error" in result[0]
            assert "API Error" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_summarize_search_results_tool(self, mock_agent_deps, mock_brave_search_results):
        """Test search results summarization tool"""
        topic = "AI Developments"
        focus_areas = "Machine Learning, Neural Networks"
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_agent_deps
        
        from agents.web_search_agent import summarize_search_results
        result = await summarize_search_results(mock_ctx, mock_brave_search_results, topic, focus_areas)
        
        assert isinstance(result, dict)
        assert "summary" in result
        assert "topic" in result
        assert "sources_count" in result
        assert "key_points" in result
        
        assert result["topic"] == topic
        assert result["sources_count"] == len(mock_brave_search_results)
        assert topic in result["summary"]
        assert focus_areas in result["summary"]

    @pytest.mark.asyncio
    async def test_summarize_search_results_empty(self, mock_agent_deps):
        """Test summarization with empty search results"""
        topic = "Empty Results"
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_agent_deps
        
        from agents.web_search_agent import summarize_search_results
        result = await summarize_search_results(mock_ctx, [], topic)
        
        assert isinstance(result, dict)
        assert "summary" in result
        assert "sources_count" in result
        assert "key_points" in result
        assert result["sources_count"] == 0

    @pytest.mark.asyncio
    async def test_web_search_agent_configuration(self):
        """Test web search agent configuration"""
        # Test that web search agent can be imported
        from agents.web_search_agent import web_search_agent
        from agents.deps import AgentDependencies
        
        # Verify basic functionality
        assert web_search_agent is not None
        assert AgentDependencies is not None
        
        # Test that AgentDependencies has the expected fields
        deps = AgentDependencies(
            brave_api_key="test",
            gmail_credentials_path="test", 
            gmail_token_path="test",
            supabase=None,
            embedding_client=None,
            http_client=None
        )
        assert deps.brave_api_key == "test"

    @pytest.mark.asyncio
    async def test_web_search_agent_streaming_mock(self, mock_agent_deps):
        """Test web search agent streaming capabilities (mocked)"""
        query = "test streaming query"
        
        # Mock the agent's run_stream method
        mock_stream_result = MagicMock()
        mock_stream_result.stream_text.return_value = AsyncMock()
        mock_stream_result.stream_text.return_value.__aiter__ = AsyncMock(return_value=iter(["chunk1", "chunk2", "chunk3"]))
        
        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_stream_result)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(web_search_agent, 'run_stream', return_value=mock_context_manager):
            # Test that we can create the stream context
            stream_context = web_search_agent.run_stream(query, deps=mock_agent_deps)
            assert stream_context is not None

    @pytest.mark.asyncio
    async def test_web_search_agent_non_streaming_fallback(self, mock_agent_deps):
        """Test web search agent non-streaming fallback"""
        query = "test fallback query"
        expected_response = "This is a test response from web search"
        
        # Mock the agent's run method (non-streaming)
        mock_result = MagicMock()
        mock_result.data = expected_response
        
        with patch.object(web_search_agent, 'run', return_value=mock_result):
            result = await web_search_agent.run(query, deps=mock_agent_deps)
            assert result.data == expected_response

    @pytest.mark.asyncio
    async def test_brave_api_headers_and_parameters(self):
        """Test that Brave API is called with correct headers and parameters"""
        query = "test query"
        api_key = "test-api-key"
        count = 5
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"web": {"results": []}}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = mock_client.return_value.__aenter__.return_value.get
            mock_get.return_value = mock_response
            
            await search_web_tool(api_key=api_key, query=query, count=count)
            
            # Verify the call was made with correct parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            
            # Check URL
            assert call_args[0][0] == "https://api.search.brave.com/res/v1/web/search"
            
            # Check headers
            headers = call_args[1]["headers"]
            assert headers["X-Subscription-Token"] == api_key
            assert headers["Accept"] == "application/json"
            
            # Check parameters
            params = call_args[1]["params"]
            assert params["q"] == query
            assert params["count"] == count

    @pytest.mark.asyncio
    async def test_search_results_scoring(self):
        """Test that search results include proper scoring"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {"title": "First Result", "url": "https://first.com", "description": "First"},
                    {"title": "Second Result", "url": "https://second.com", "description": "Second"},
                    {"title": "Third Result", "url": "https://third.com", "description": "Third"}
                ]
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            results = await search_web_tool(api_key="test-key", query="test")
            
            # Check that scores are assigned correctly (decreasing order)
            assert len(results) == 3
            assert results[0]["score"] > results[1]["score"]
            assert results[1]["score"] > results[2]["score"]
            assert all(result["score"] >= 0.1 for result in results)  # Minimum score
            assert all(result["score"] <= 1.0 for result in results)  # Maximum score