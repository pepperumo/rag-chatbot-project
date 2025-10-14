"""
Tests for Research Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.research_agent import ResearchAgentDependencies, create_research_agent
from agents.models import BraveSearchResult


class TestResearchAgent:
    """Tests for Research Agent functionality."""
    
    def test_create_research_agent_with_api_keys(self):
        """Test creating research agent with API key dependencies."""
        agent = create_research_agent(
            brave_api_key="test_brave_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json",
            session_id="test_session"
        )
        
        assert agent is not None
    
    def test_research_agent_dependencies_init(self):
        """Test ResearchAgentDependencies initialization."""
        deps = ResearchAgentDependencies(
            brave_api_key="test_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        assert deps.brave_api_key == "test_key"
        assert deps.gmail_credentials_path == "/fake/creds.json"
        assert deps.gmail_token_path == "/fake/token.json"
        assert deps.session_id is None
    
    def test_research_agent_dependencies_with_custom_values(self):
        """Test ResearchAgentDependencies with custom values."""
        deps = ResearchAgentDependencies(
            brave_api_key="custom_key",
            gmail_credentials_path="/custom/creds.json",
            gmail_token_path="/custom/token.json",
            session_id="custom_session"
        )
        
        assert deps.brave_api_key == "custom_key"
        assert deps.gmail_credentials_path == "/custom/creds.json"
        assert deps.gmail_token_path == "/custom/token.json"
        assert deps.session_id == "custom_session"


class TestResearchAgentTools:
    """Tests for Research Agent tool functions."""
    
    @pytest.mark.asyncio
    async def test_search_web_success(self):
        """Test successful web search."""
        from agents.research_agent import search_web
        
        # Mock the search_web_tool function
        mock_search_results = [
            {
                "title": "Test Result 1",
                "url": "https://example.com/1",
                "description": "Test description 1",
                "score": 0.95
            },
            {
                "title": "Test Result 2", 
                "url": "https://example.com/2",
                "description": "Test description 2",
                "score": 0.90
            }
        ]
        
        with patch('agents.research_agent.search_web_tool', new_callable=AsyncMock) as mock_search_tool:
            mock_search_tool.return_value = mock_search_results
            
            # Mock context with new dependency structure
            mock_ctx = MagicMock()
            mock_ctx.deps.brave_api_key = "test_api_key"
            
            # Call the function
            result = await search_web(mock_ctx, "test query", max_results=2)
            
            assert len(result) == 2
            assert result[0]["title"] == "Test Result 1"
            assert result[0]["url"] == "https://example.com/1"
            assert result[0]["description"] == "Test description 1"
            assert result[0]["score"] == 0.95
            
            mock_search_tool.assert_called_once_with(
                api_key="test_api_key",
                query="test query",
                count=2
            )
    
    @pytest.mark.asyncio
    async def test_search_web_empty_query(self):
        """Test web search with empty query."""
        from agents.research_agent import search_web
        
        mock_ctx = MagicMock()
        mock_ctx.deps.brave_api_key = "test_api_key"
        
        # Should handle empty queries gracefully  
        result = await search_web(mock_ctx, "", max_results=5)
        
        # Should return error result
        assert len(result) == 1
        assert "error" in result[0]
    
    @pytest.mark.asyncio
    async def test_search_web_api_error(self):
        """Test web search with API error."""
        from agents.research_agent import search_web
        
        with patch('agents.research_agent.search_web_tool', new_callable=AsyncMock) as mock_search_tool:
            mock_search_tool.side_effect = Exception("API Error")
            
            mock_ctx = MagicMock()
            mock_ctx.deps.brave_api_key = "test_api_key"
            
            result = await search_web(mock_ctx, "test query")
            
            assert len(result) == 1
            assert "error" in result[0]
            assert "Search failed: API Error" == result[0]["error"]
    
    @pytest.mark.asyncio
    async def test_search_web_count_limits(self):
        """Test web search count parameter limits."""
        from agents.research_agent import search_web
        
        with patch('agents.research_agent.search_web_tool', new_callable=AsyncMock) as mock_search_tool:
            mock_search_tool.return_value = []
            
            mock_ctx = MagicMock()
            mock_ctx.deps.brave_api_key = "test_api_key"
            
            # Test count below minimum
            await search_web(mock_ctx, "test", max_results=0)
            mock_search_tool.assert_called_with(api_key="test_api_key", query="test", count=1)
            
            # Reset mock for next call
            mock_search_tool.reset_mock()
            
            # Test count above maximum
            await search_web(mock_ctx, "test", max_results=50)
            mock_search_tool.assert_called_with(api_key="test_api_key", query="test", count=20)
    
    @pytest.mark.asyncio
    async def test_summarize_research_success(self):
        """Test successful research summarization."""
        from agents.research_agent import summarize_research
        
        search_results = [
            {
                "title": "AI Safety Research",
                "url": "https://example.com/ai-safety",
                "description": "Latest developments in AI safety research and methodologies."
            },
            {
                "title": "Machine Learning Ethics",
                "url": "https://example.com/ml-ethics", 
                "description": "Ethical considerations in machine learning applications."
            }
        ]
        
        mock_ctx = MagicMock()
        
        result = await summarize_research(
            mock_ctx,
            search_results,
            "AI Safety",
            "Research methodologies"
        )
        
        assert result["topic"] == "AI Safety"
        assert result["sources_count"] == 2
        assert len(result["key_points"]) == 2
        assert "AI safety research" in result["summary"]
        assert "Research methodologies" in result["summary"]
    
    @pytest.mark.asyncio
    async def test_summarize_research_empty_results(self):
        """Test research summarization with empty results."""
        from agents.research_agent import summarize_research
        
        mock_ctx = MagicMock()
        
        result = await summarize_research(mock_ctx, [], "Empty Topic")
        
        assert "No search results provided" in result["summary"]
        assert result["key_points"] == []
        assert result["sources"] == []
    
    @pytest.mark.asyncio
    @patch('agents.research_agent.email_agent')
    async def test_create_email_draft_success(self, mock_email_agent):
        """Test successful email draft creation via Email Agent."""
        from agents.research_agent import create_email_draft
        
        # Mock email agent response
        mock_email_result = MagicMock()
        mock_email_result.data = {"draft_id": "draft_123"}
        mock_email_agent.run = AsyncMock(return_value=mock_email_result)
        
        # Mock context with new dependency structure
        mock_ctx = MagicMock()
        mock_ctx.usage = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        mock_ctx.deps.session_id = "test_session"
        
        result = await create_email_draft(
            mock_ctx,
            "test@example.com",
            "Research Summary",
            "Please find research findings",
            "AI safety research shows promising developments"
        )
        
        assert result["success"] is True
        assert result["recipient"] == "test@example.com"
        assert result["subject"] == "Research Summary"
        assert "agent_response" in result
        
        # Verify email agent was called with usage tracking
        mock_email_agent.run.assert_called_once()
        call_args = mock_email_agent.run.call_args
        assert call_args.kwargs["usage"] == mock_ctx.usage
    
    @pytest.mark.asyncio
    @patch('agents.research_agent.email_agent')
    async def test_create_email_draft_without_research_summary(self, mock_email_agent):
        """Test email draft creation without research summary."""
        from agents.research_agent import create_email_draft
        
        mock_email_result = MagicMock()
        mock_email_result.data = {"draft_id": "draft_456"}
        mock_email_agent.run = AsyncMock(return_value=mock_email_result)
        
        mock_ctx = MagicMock()
        mock_ctx.usage = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        mock_ctx.deps.session_id = "test_session"
        
        result = await create_email_draft(
            mock_ctx,
            "test@example.com",
            "Simple Email",
            "Basic context"
        )
        
        assert result["success"] is True
        assert result["recipient"] == "test@example.com"
        assert result["subject"] == "Simple Email"
        assert result["context"] == "Basic context"
    
    @pytest.mark.asyncio
    @patch('agents.research_agent.email_agent')
    async def test_create_email_draft_agent_error(self, mock_email_agent):
        """Test email draft creation with agent error."""
        from agents.research_agent import create_email_draft
        
        mock_email_agent.run = AsyncMock(side_effect=Exception("Agent Error"))
        
        mock_ctx = MagicMock()
        mock_ctx.usage = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        mock_ctx.deps.session_id = "test_session"
        
        result = await create_email_draft(
            mock_ctx,
            "test@example.com",
            "Error Test",
            "This should fail"
        )
        
        assert result["success"] is False
        assert "Agent Error" in result["error"]
        assert result["recipient"] == "test@example.com"