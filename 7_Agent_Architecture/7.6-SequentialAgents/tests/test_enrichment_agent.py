"""
Unit tests for the enrichment agent functionality.

Tests enrichment agent with data gap filling and Brave search integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from agents.enrichment_agent import enrichment_agent
from agents.deps import ResearchAgentDependencies


@pytest.fixture
def mock_enrichment_deps():
    """Create mock enrichment dependencies"""
    return ResearchAgentDependencies(
        brave_api_key="test-brave-key",
        session_id="test-session-123"
    )


@pytest.fixture
def mock_enrichment_results():
    """Create mock enrichment search results"""
    return [
        {
            "title": "John Doe Education - Stanford University",
            "url": "https://stanford.edu/alumni/johndoe",
            "description": "Computer Science graduate, class of 2018",
            "score": 0.92
        },
        {
            "title": "TechCorp Recent News - Series B Funding",
            "url": "https://techcrunch.com/techcorp-funding",
            "description": "TechCorp raises $50M in Series B funding",
            "score": 0.87
        }
    ]


@pytest.fixture
def mock_enrichment_result():
    """Create mock enrichment agent result"""
    mock_result = MagicMock()
    mock_result.data = "Additional research reveals John Doe graduated from Stanford..."
    return mock_result


class TestEnrichmentAgent:
    """Test cases for enrichment agent functionality"""

    @pytest.mark.asyncio
    async def test_enrichment_search_web_tool_success(self, mock_enrichment_deps, mock_enrichment_results):
        """Test successful enrichment web search using Brave API"""
        query = "John Doe Stanford University education background"
        max_results = 10
        
        with patch('agents.enrichment_agent.search_web_tool', return_value=mock_enrichment_results) as mock_search:
            # Create mock context
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_enrichment_deps
            
            # Import and call the tool function directly
            from agents.enrichment_agent import search_web
            result = await search_web(mock_ctx, query, max_results)
            
            # Verify search was called with correct parameters
            mock_search.assert_called_once_with(
                api_key="test-brave-key",
                query=query,
                count=max_results
            )
            
            # Verify results
            assert result == mock_enrichment_results
            assert len(result) == 2
            assert "Stanford University" in result[0]["title"]

    @pytest.mark.asyncio
    async def test_enrichment_search_tool_api_error(self, mock_enrichment_deps):
        """Test enrichment search tool handling API errors"""
        query = "test enrichment query"
        
        with patch('agents.enrichment_agent.search_web_tool', side_effect=Exception("Enrichment API Error")) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_enrichment_deps
            
            from agents.enrichment_agent import search_web
            result = await search_web(mock_ctx, query)
            
            # Verify error handling
            assert len(result) == 1
            assert "error" in result[0]
            assert "Enrichment search failed: Enrichment API Error" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_enrichment_agent_integration(self, mock_enrichment_deps, mock_enrichment_result):
        """Test enrichment agent end-to-end integration"""
        query = "Enrich data for John Doe at TechCorp"
        
        with patch.object(enrichment_agent, 'run', return_value=mock_enrichment_result) as mock_run:
            result = await enrichment_agent.run(query, deps=mock_enrichment_deps)
            
            # Verify the agent was called
            mock_run.assert_called_with(query, deps=mock_enrichment_deps)
            
            # Verify result structure
            assert hasattr(result, 'data')
            assert isinstance(result.data, str)

    @pytest.mark.asyncio
    async def test_enrichment_agent_with_message_history(self, mock_enrichment_deps, mock_enrichment_result):
        """Test enrichment agent with message history"""
        query = "Continue enriching John Doe data"
        message_history = [MagicMock()]
        
        with patch.object(enrichment_agent, 'run', return_value=mock_enrichment_result) as mock_run:
            result = await enrichment_agent.run(
                query, 
                deps=mock_enrichment_deps,
                message_history=message_history
            )
            
            # Verify the agent was called with message history
            mock_run.assert_called_with(
                query, 
                deps=mock_enrichment_deps,
                message_history=message_history
            )

    @pytest.mark.asyncio
    async def test_enrichment_search_max_results_validation(self, mock_enrichment_deps):
        """Test enrichment search max_results parameter validation"""
        query = "test enrichment query"
        
        with patch('agents.enrichment_agent.search_web_tool', return_value=[]) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_enrichment_deps
            
            from agents.enrichment_agent import search_web
            
            # Test upper bound
            await search_web(mock_ctx, query, 30)
            mock_search.assert_called_with(
                api_key="test-brave-key",
                query=query,
                count=20  # Should be clamped to 20
            )
            
            # Test lower bound
            await search_web(mock_ctx, query, -5)
            mock_search.assert_called_with(
                api_key="test-brave-key",
                query=query,
                count=1  # Should be clamped to 1
            )

    @pytest.mark.asyncio
    async def test_enrichment_search_empty_results(self, mock_enrichment_deps):
        """Test enrichment search handling empty results"""
        query = "nonexistent enrichment query"
        
        with patch('agents.enrichment_agent.search_web_tool', return_value=[]) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_enrichment_deps
            
            from agents.enrichment_agent import search_web
            result = await search_web(mock_ctx, query)
            
            # Verify empty results are handled
            assert result == []
            mock_search.assert_called_once()

    def test_enrichment_dependencies_reuse(self):
        """Test that enrichment agent uses ResearchAgentDependencies"""
        deps = ResearchAgentDependencies(
            brave_api_key="test-key",
            session_id="test-session"
        )
        
        assert deps.brave_api_key == "test-key"
        assert deps.session_id == "test-session"

    @pytest.mark.asyncio
    async def test_enrichment_search_specific_queries(self, mock_enrichment_deps):
        """Test enrichment search with specific data gap queries"""
        enrichment_queries = [
            "John Doe location address",
            "TechCorp company size employees",
            "John Doe education university degree",
            "TechCorp recent news funding",
            "John Doe LinkedIn professional connections"
        ]
        
        with patch('agents.enrichment_agent.search_web_tool', return_value=[]) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_enrichment_deps
            
            from agents.enrichment_agent import search_web
            
            for query in enrichment_queries:
                await search_web(mock_ctx, query)
                mock_search.assert_called_with(
                    api_key="test-brave-key",
                    query=query,
                    count=10
                )
                mock_search.reset_mock()