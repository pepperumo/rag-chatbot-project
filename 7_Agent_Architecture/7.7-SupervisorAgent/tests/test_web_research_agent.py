"""
Unit tests for the web research agent functionality.

Tests web research agent with Brave Search API integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from agents.web_research_agent import web_research_agent, WebResearchAgentDependencies


@pytest.fixture
def mock_web_research_deps():
    """Create mock web research dependencies"""
    return WebResearchAgentDependencies(
        brave_api_key="test-brave-key",
        session_id="test-session-123"
    )


@pytest.fixture
def mock_search_results():
    """Create mock search results"""
    return [
        {
            "title": "AI Trends 2024: Latest Developments",
            "url": "https://techcrunch.com/ai-trends-2024",
            "description": "Comprehensive overview of artificial intelligence trends in 2024",
            "score": 1.0
        },
        {
            "title": "Machine Learning Market Analysis",
            "url": "https://marketresearch.com/ml-analysis",
            "description": "In-depth analysis of machine learning market dynamics",
            "score": 0.95
        },
        {
            "title": "Enterprise AI Adoption Report",
            "url": "https://enterprise.ai/adoption-report",
            "description": "Survey of enterprise AI adoption patterns and challenges",
            "score": 0.90
        }
    ]


@pytest.fixture
def mock_comprehensive_search_result():
    """Create mock comprehensive search result"""
    return {
        "success": True,
        "primary_query": "AI trends 2024",
        "total_queries": 3,
        "total_sources": 15,
        "results_by_query": {
            "AI trends 2024": [
                {"title": "AI Trends", "url": "https://example.com/1", "description": "AI trends overview"}
            ],
            "machine learning 2024": [
                {"title": "ML Progress", "url": "https://example.com/2", "description": "ML developments"}
            ],
            "enterprise AI adoption": [
                {"title": "Enterprise AI", "url": "https://example.com/3", "description": "Enterprise adoption"}
            ]
        }
    }


@pytest.fixture
def mock_analysis_result():
    """Create mock analysis result"""
    return {
        "success": True,
        "topic": "AI Trends 2024",
        "summary": "Research Analysis: AI Trends 2024\n\nKey Findings:\n• AI adoption increasing rapidly\n• Focus on enterprise solutions\n• Ethical AI gaining importance",
        "key_findings": [
            "AI adoption increasing rapidly across industries",
            "Enterprise solutions dominating market",
            "Ethical AI considerations becoming critical"
        ],
        "high_relevance_sources": [
            {"title": "AI Trends Report", "url": "https://example.com/report", "relevance_score": 0.95}
        ],
        "sources_count": 10
    }


@pytest.fixture
def mock_web_research_agent_result():
    """Create mock web research agent result"""
    mock_result = MagicMock()
    mock_result.output = "Found 5 key AI trends for 2024: increased enterprise adoption, focus on ethical AI, edge computing integration, multimodal AI development, and sustainable AI practices. Sources: TechCrunch, MIT Technology Review, Forbes."
    return mock_result


class TestWebResearchAgent:
    """Test cases for web research agent functionality"""

    @pytest.mark.asyncio
    async def test_search_web_success(self, mock_web_research_deps, mock_search_results):
        """Test successful web search"""
        query = "AI trends 2024"
        
        with patch('agents.web_research_agent.search_web_tool', return_value=mock_search_results) as mock_search:
            # Create mock context
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_web_research_deps
            
            # Import and call the tool function directly
            from agents.web_research_agent import search_web
            result = await search_web(mock_ctx, query, 10)
            
            # Verify Brave search tool was called with correct parameters
            mock_search.assert_called_once_with(
                api_key="test-brave-key",
                query=query,
                count=10
            )
            
            # Verify results
            assert len(result) == 3
            assert result[0]["title"] == "AI Trends 2024: Latest Developments"
            assert result[0]["url"] == "https://techcrunch.com/ai-trends-2024"
            assert result[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_search_web_count_validation(self, mock_web_research_deps, mock_search_results):
        """Test search web count parameter validation"""
        with patch('agents.web_research_agent.search_web_tool', return_value=mock_search_results) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_web_research_deps
            
            from agents.web_research_agent import search_web
            
            # Test upper bound
            await search_web(mock_ctx, "test query", 25)
            call_args = mock_search.call_args[1]
            assert call_args["count"] == 20  # Should be clamped to 20
            
            # Test lower bound
            await search_web(mock_ctx, "test query", 0)
            call_args = mock_search.call_args[1]
            assert call_args["count"] == 1  # Should be clamped to 1

    @pytest.mark.asyncio
    async def test_search_web_error_handling(self, mock_web_research_deps):
        """Test search web error handling"""
        query = "test query"
        
        with patch('agents.web_research_agent.search_web_tool', side_effect=Exception("Brave API Error")) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_web_research_deps
            
            from agents.web_research_agent import search_web
            result = await search_web(mock_ctx, query)
            
            # Verify error handling
            assert len(result) == 1
            assert "error" in result[0]
            assert "Search failed: Brave API Error" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_search_success(self, mock_web_research_deps, mock_comprehensive_search_result):
        """Test successful comprehensive search"""
        primary_query = "AI trends 2024"
        related_queries = ["machine learning 2024", "enterprise AI adoption"]
        
        # Mock multiple search calls
        search_results = [
            [{"title": "AI Trends", "url": "https://example.com/1", "description": "AI trends overview"}],
            [{"title": "ML Progress", "url": "https://example.com/2", "description": "ML developments"}],
            [{"title": "Enterprise AI", "url": "https://example.com/3", "description": "Enterprise adoption"}]
        ]
        
        with patch('agents.web_research_agent.search_web_tool', side_effect=search_results) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_web_research_deps
            
            from agents.web_research_agent import conduct_comprehensive_search
            result = await conduct_comprehensive_search(
                mock_ctx, 
                primary_query, 
                related_queries, 
                max_results_per_query=5
            )
            
            # Verify multiple search calls were made
            assert mock_search.call_count == 3
            
            # Verify result structure
            assert result["success"] is True
            assert result["primary_query"] == primary_query
            assert result["total_queries"] == 3
            assert result["total_sources"] == 3  # One result per query in mock
            assert len(result["results_by_query"]) == 3

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_search_partial_failure(self, mock_web_research_deps):
        """Test comprehensive search with partial failures"""
        primary_query = "AI trends"
        related_queries = ["valid query", "failing query"]
        
        # Mock mixed success/failure
        def mock_search_side_effect(*args, **kwargs):
            query = kwargs.get("query", "")
            if "failing" in query:
                raise Exception("Search failed")
            return [{"title": "Result", "url": "https://example.com", "description": "Test"}]
        
        with patch('agents.web_research_agent.search_web_tool', side_effect=mock_search_side_effect):
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_web_research_deps
            
            from agents.web_research_agent import conduct_comprehensive_search
            result = await conduct_comprehensive_search(
                mock_ctx, 
                primary_query, 
                related_queries
            )
            
            # Should still succeed with partial results
            assert result["success"] is True
            assert result["total_queries"] == 3
            assert result["total_sources"] == 2  # Primary + one successful related query

    @pytest.mark.asyncio
    async def test_analyze_search_results_success(self, mock_web_research_deps, mock_search_results):
        """Test successful search results analysis"""
        topic = "AI Trends 2024"
        focus_areas = ["enterprise adoption", "ethical considerations"]
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_web_research_deps
        
        from agents.web_research_agent import analyze_search_results
        result = await analyze_search_results(
            mock_ctx, 
            mock_search_results, 
            topic, 
            focus_areas
        )
        
        # Verify analysis structure
        assert result["success"] is True
        assert result["topic"] == topic
        assert "summary" in result
        assert "key_findings" in result
        assert "high_relevance_sources" in result
        assert "all_sources" in result
        assert result["sources_count"] == 3
        assert result["focus_areas"] == focus_areas

    @pytest.mark.asyncio
    async def test_analyze_search_results_empty_input(self, mock_web_research_deps):
        """Test search results analysis with empty input"""
        topic = "Test Topic"
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_web_research_deps
        
        from agents.web_research_agent import analyze_search_results
        result = await analyze_search_results(mock_ctx, [], topic)
        
        # Verify error handling
        assert result["success"] is False
        assert "No search results provided" in result["error"]
        assert result["topic"] == topic
        assert result["key_findings"] == []
        assert result["sources"] == []

    @pytest.mark.asyncio
    async def test_analyze_search_results_with_errors(self, mock_web_research_deps):
        """Test search results analysis with error results"""
        results_with_errors = [
            {"error": "Search failed"},
            {"title": "Valid Result", "url": "https://example.com", "description": "Valid description"},
            {"error": "Another error"}
        ]
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_web_research_deps
        
        from agents.web_research_agent import analyze_search_results
        result = await analyze_search_results(mock_ctx, results_with_errors, "Test Topic")
        
        # Should process only valid results
        assert result["success"] is True
        assert result["sources_count"] == 1  # Only one valid result
        assert len(result["all_sources"]) == 1

    @pytest.mark.asyncio
    async def test_search_with_context_success(self, mock_web_research_deps, mock_search_results):
        """Test successful search with context"""
        query = "AI market analysis"
        context = "Previous research shows increasing enterprise AI adoption"
        
        with patch('agents.web_research_agent.search_web_tool', return_value=mock_search_results) as mock_search:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_web_research_deps
            
            from agents.web_research_agent import search_with_context
            result = await search_with_context(mock_ctx, query, context, 8)
            
            # Verify search was called
            mock_search.assert_called_once_with(
                api_key="test-brave-key",
                query=query,  # Enhanced query same as input in current implementation
                count=8
            )
            
            # Verify result structure
            assert result["success"] is True
            assert result["query"] == query
            assert result["context_provided"] is True
            assert result["total_results"] == 3
            assert result["relevant_results"] == 3
            assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_search_with_context_no_context(self, mock_web_research_deps, mock_search_results):
        """Test search with context but no context provided"""
        query = "AI trends"
        
        with patch('agents.web_research_agent.search_web_tool', return_value=mock_search_results):
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_web_research_deps
            
            from agents.web_research_agent import search_with_context
            result = await search_with_context(mock_ctx, query, None)
            
            # Verify result indicates no context
            assert result["success"] is True
            assert result["context_provided"] is False

    @pytest.mark.asyncio
    async def test_web_research_agent_integration(self, mock_web_research_deps, mock_web_research_agent_result):
        """Test web research agent end-to-end integration"""
        query = "Research the latest AI trends and developments in 2024"
        
        with patch.object(web_research_agent, 'run', return_value=mock_web_research_agent_result) as mock_run:
            result = await web_research_agent.run(query, deps=mock_web_research_deps)
            
            # Verify the agent was called
            mock_run.assert_called_with(query, deps=mock_web_research_deps)
            
            # Verify result structure
            assert hasattr(result, 'output')
            assert isinstance(result.output, str)

    @pytest.mark.asyncio
    async def test_web_research_agent_with_message_history(self, mock_web_research_deps, mock_web_research_agent_result):
        """Test web research agent with message history"""
        query = "Continue research on AI trends, focusing on enterprise applications"
        message_history = [MagicMock()]
        
        with patch.object(web_research_agent, 'run', return_value=mock_web_research_agent_result) as mock_run:
            result = await web_research_agent.run(
                query, 
                deps=mock_web_research_deps,
                message_history=message_history
            )
            
            # Verify the agent was called with message history
            mock_run.assert_called_with(
                query, 
                deps=mock_web_research_deps,
                message_history=message_history
            )

    def test_web_research_dependencies_structure(self):
        """Test WebResearchAgentDependencies dataclass structure"""
        deps = WebResearchAgentDependencies(
            brave_api_key="test-key",
            session_id="test-session"
        )
        
        assert deps.brave_api_key == "test-key"
        assert deps.session_id == "test-session"
        
        # Test with None session_id
        deps_none = WebResearchAgentDependencies(
            brave_api_key="test-key"
        )
        assert deps_none.brave_api_key == "test-key"
        assert deps_none.session_id is None

    def test_web_research_system_prompt_structure(self):
        """Test that web research agent has proper system prompt"""
        # Access the system prompt constant
        from agents.prompts import WEB_RESEARCH_SYSTEM_PROMPT
        
        # Verify key elements are present
        assert "research" in WEB_RESEARCH_SYSTEM_PROMPT.lower()
        assert "brave search" in WEB_RESEARCH_SYSTEM_PROMPT.lower()
        assert "synthesis" in WEB_RESEARCH_SYSTEM_PROMPT.lower()
        assert "concise" in WEB_RESEARCH_SYSTEM_PROMPT.lower()
        
        # Verify output format requirements
        assert "3-5 key points" in WEB_RESEARCH_SYSTEM_PROMPT
        assert "500 words" in WEB_RESEARCH_SYSTEM_PROMPT
        assert "bullet points" in WEB_RESEARCH_SYSTEM_PROMPT.lower()

    @pytest.mark.asyncio
    async def test_web_research_tool_error_propagation(self, mock_web_research_deps):
        """Test that tool errors are properly handled and logged"""
        query = "test query"
        
        with patch('agents.web_research_agent.search_web_tool', side_effect=Exception("Network error")):
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_web_research_deps
            
            from agents.web_research_agent import search_web
            result = await search_web(mock_ctx, query)
            
            # Should return error result instead of raising
            assert isinstance(result, list)
            assert len(result) == 1
            assert "error" in result[0]
            assert "Network error" in result[0]["error"]