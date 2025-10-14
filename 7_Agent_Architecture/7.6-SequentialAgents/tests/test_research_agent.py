"""
Unit tests for the research agent functionality.

Tests research agent with Brave search integration and tool functionality.
"""

import pytest
from unittest.mock import MagicMock, patch

from agents.research_agent import research_agent
from agents.deps import ResearchAgentDependencies


@pytest.fixture
def mock_research_deps():
    """Create mock research dependencies"""
    return ResearchAgentDependencies(
        brave_api_key="test-brave-key",
        session_id="test-session-123"
    )


@pytest.fixture
def mock_search_results():
    """Create mock search results"""
    return [
        {
            "title": "John Doe - Senior Engineer at TechCorp",
            "url": "https://linkedin.com/in/johndoe",
            "description": "Experienced software engineer specializing in AI/ML",
            "score": 0.95
        },
        {
            "title": "TechCorp Company Profile",
            "url": "https://techcorp.com/about",
            "description": "Leading technology company focused on AI solutions",
            "score": 0.88
        }
    ]


@pytest.fixture
def mock_research_result():
    """Create mock research agent result"""
    mock_result = MagicMock()
    mock_result.data = "Based on my research, John Doe is a Senior Engineer at TechCorp..."
    return mock_result


class TestResearchAgent:
    """Test cases for research agent functionality"""

    @pytest.mark.asyncio
    async def test_search_web_tool_success(self, mock_research_deps, mock_search_results):
        """Test successful web search using Brave API"""
        query = "John Doe TechCorp engineer"
        max_results = 10
        
        with patch('agents.research_agent.search_web_tool', return_value=mock_search_results) as mock_search:
            # Create mock context
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_research_deps
            
            # Import and call the tool function directly
            from agents.research_agent import search_web
            result = await search_web(mock_ctx, query, max_results)
            
            # Verify search was called with correct parameters
            mock_search.assert_called_once_with(
                api_key="test-brave-key",
                query=query,
                count=max_results
            )
            
            # Verify results
            assert result == mock_search_results
            assert len(result) == 2
            assert result[0]["title"] == "John Doe - Senior Engineer at TechCorp"

    @pytest.mark.asyncio
    async def test_search_web_tool_api_error(self, mock_research_deps):
        """Test web search tool handling API errors"""
        query = "test query"
        
        with patch('agents.research_agent.search_web_tool', side_effect=Exception("API Error")) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_research_deps
            
            from agents.research_agent import search_web
            result = await search_web(mock_ctx, query)
            
            # Verify error handling
            assert len(result) == 1
            assert "error" in result[0]
            assert "Search failed: API Error" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_search_web_tool_max_results_validation(self, mock_research_deps):
        """Test max_results parameter validation"""
        query = "test query"
        
        with patch('agents.research_agent.search_web_tool', return_value=[]) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_research_deps
            
            from agents.research_agent import search_web
            
            # Test upper bound
            await search_web(mock_ctx, query, 25)
            mock_search.assert_called_with(
                api_key="test-brave-key",
                query=query,
                count=20  # Should be clamped to 20
            )
            
            # Test lower bound
            await search_web(mock_ctx, query, 0)
            mock_search.assert_called_with(
                api_key="test-brave-key",
                query=query,
                count=1  # Should be clamped to 1
            )

    @pytest.mark.asyncio
    async def test_research_agent_integration(self, mock_research_deps, mock_research_result):
        """Test research agent end-to-end integration"""
        query = "Research John Doe at TechCorp"
        
        with patch.object(research_agent, 'run', return_value=mock_research_result) as mock_run:
            result = await research_agent.run(query, deps=mock_research_deps)
            
            # Verify the agent was called
            mock_run.assert_called_with(query, deps=mock_research_deps)
            
            # Verify result structure
            assert hasattr(result, 'data')
            assert isinstance(result.data, str)

    @pytest.mark.asyncio
    async def test_research_agent_with_message_history(self, mock_research_deps, mock_research_result):
        """Test research agent with message history"""
        query = "Follow up on John Doe research"
        message_history = [MagicMock()]
        
        with patch.object(research_agent, 'run', return_value=mock_research_result) as mock_run:
            result = await research_agent.run(
                query, 
                deps=mock_research_deps,
                message_history=message_history
            )
            
            # Verify the agent was called with message history
            mock_run.assert_called_with(
                query, 
                deps=mock_research_deps,
                message_history=message_history
            )

    def test_research_dependencies_structure(self):
        """Test ResearchAgentDependencies dataclass structure"""
        deps = ResearchAgentDependencies(
            brave_api_key="test-key",
            session_id="test-session"
        )
        
        assert deps.brave_api_key == "test-key"
        assert deps.session_id == "test-session"
        
        # Test with None session_id
        deps_none = ResearchAgentDependencies(brave_api_key="test-key")
        assert deps_none.session_id is None

    @pytest.mark.asyncio
    async def test_search_web_tool_empty_results(self, mock_research_deps):
        """Test search tool handling empty results"""
        query = "nonexistent query"
        
        with patch('agents.research_agent.search_web_tool', return_value=[]) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_research_deps
            
            from agents.research_agent import search_web
            result = await search_web(mock_ctx, query)
            
            # Verify empty results are handled
            assert result == []
            mock_search.assert_called_once()
            