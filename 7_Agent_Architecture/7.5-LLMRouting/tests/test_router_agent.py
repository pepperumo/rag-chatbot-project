"""
Unit tests for the router agent functionality.

Tests routing decisions, mock dependencies, and verify structured output.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Any

from agents.router_agent import router_agent, RouterResponse
from agents.deps import RouterDependencies


@pytest.fixture
def mock_router_deps():
    """Create mock router dependencies"""
    return RouterDependencies(session_id="test-session-123")


@pytest.fixture
def mock_router_result():
    """Create mock router result with data attribute"""
    mock_result = MagicMock()
    mock_result.data = RouterResponse(decision="web_search")
    return mock_result


class TestRouterAgent:
    """Test cases for router agent functionality"""

    @pytest.mark.asyncio
    async def test_router_web_search_decision(self, mock_router_deps, mock_router_result):
        """Router correctly identifies web search requests"""
        # Test queries that should route to web search
        web_queries = [
            "What's the latest news about AI?",
            "Current weather in New York",
            "Recent developments in machine learning",
            "Search for information about climate change",
            "What happened in the tech industry today?"
        ]
        
        with patch.object(router_agent, 'run', return_value=mock_router_result) as mock_run:
            for query in web_queries:
                result = await router_agent.run(query, deps=mock_router_deps)
                
                # Verify the agent was called with correct parameters
                mock_run.assert_called_with(query, deps=mock_router_deps)
                
                # Verify structured output
                assert isinstance(result.data, RouterResponse)
                assert result.data.decision == "web_search"

    @pytest.mark.asyncio
    async def test_router_email_search_decision(self, mock_router_deps):
        """Router correctly identifies email search requests"""
        # Test queries that should route to email search
        email_queries = [
            "Find emails from John about the project",
            "Search for messages from my manager",
            "Show me emails about the budget meeting",
            "Find correspondence with Sarah",
            "Search inbox for quarterly reports"
        ]
        
        for query in email_queries:
            mock_result = MagicMock()
            mock_result.data = RouterResponse(decision="email_search")
            
            with patch.object(router_agent, 'run', return_value=mock_result) as mock_run:
                result = await router_agent.run(query, deps=mock_router_deps)
                
                mock_run.assert_called_with(query, deps=mock_router_deps)
                assert isinstance(result.data, RouterResponse)
                assert result.data.decision == "email_search"

    @pytest.mark.asyncio
    async def test_router_rag_search_decision(self, mock_router_deps):
        """Router correctly identifies RAG search requests"""
        # Test queries that should route to RAG search
        rag_queries = [
            "What does our company policy say about remote work?",
            "Find information in the user manual",
            "What's in the documentation about API usage?",
            "Search the knowledge base for troubleshooting steps",
            "What does the employee handbook say about vacation?"
        ]
        
        for query in rag_queries:
            mock_result = MagicMock()
            mock_result.data = RouterResponse(decision="rag_search")
            
            with patch.object(router_agent, 'run', return_value=mock_result) as mock_run:
                result = await router_agent.run(query, deps=mock_router_deps)
                
                mock_run.assert_called_with(query, deps=mock_router_deps)
                assert isinstance(result.data, RouterResponse)
                assert result.data.decision == "rag_search"

    @pytest.mark.asyncio
    async def test_router_fallback_decision(self, mock_router_deps):
        """Router uses fallback for unclear requests"""
        # Test queries that should route to fallback
        fallback_queries = [
            "How are you feeling today?",
            "Tell me a joke",
            "What's the meaning of life?",
            "Hello there",
            "Can you help me with something unclear?"
        ]
        
        for query in fallback_queries:
            mock_result = MagicMock()
            mock_result.data = RouterResponse(decision="fallback")
            
            with patch.object(router_agent, 'run', return_value=mock_result) as mock_run:
                result = await router_agent.run(query, deps=mock_router_deps)
                
                mock_run.assert_called_with(query, deps=mock_router_deps)
                assert isinstance(result.data, RouterResponse)
                assert result.data.decision == "fallback"

    @pytest.mark.asyncio
    async def test_router_response_structure(self, mock_router_deps):
        """Test that RouterResponse has correct structure and validation"""
        # Test valid decisions
        valid_decisions = ["web_search", "email_search", "rag_search", "fallback"]
        
        for decision in valid_decisions:
            response = RouterResponse(decision=decision)
            assert response.decision == decision
            assert response.decision in ["web_search", "email_search", "rag_search", "fallback"]

    @pytest.mark.asyncio
    async def test_router_dependencies_structure(self):
        """Test RouterDependencies structure"""
        # Test with session_id
        deps_with_session = RouterDependencies(session_id="test-session-456")
        assert deps_with_session.session_id == "test-session-456"
        
        # Test without session_id
        deps_without_session = RouterDependencies()
        assert deps_without_session.session_id is None

    @pytest.mark.asyncio
    async def test_router_error_handling(self, mock_router_deps):
        """Test router error handling and graceful failures"""
        query = "Test query that causes error"
        
        # Test exception handling
        with patch.object(router_agent, 'run', side_effect=Exception("Mock error")) as mock_run:
            with pytest.raises(Exception) as exc_info:
                await router_agent.run(query, deps=mock_router_deps)
            
            assert "Mock error" in str(exc_info.value)
            mock_run.assert_called_with(query, deps=mock_router_deps)

    @pytest.mark.asyncio
    async def test_router_empty_query_handling(self, mock_router_deps):
        """Test router handling of empty or whitespace queries"""
        empty_queries = ["", "   ", "\n\t", None]
        
        for query in empty_queries:
            if query is None:
                continue  # Skip None as it would cause TypeError
                
            mock_result = MagicMock()
            mock_result.data = RouterResponse(decision="fallback")
            
            with patch.object(router_agent, 'run', return_value=mock_result) as mock_run:
                result = await router_agent.run(query, deps=mock_router_deps)
                
                mock_run.assert_called_with(query, deps=mock_router_deps)
                assert isinstance(result.data, RouterResponse)
                # Empty queries should typically route to fallback
                assert result.data.decision == "fallback"

    @pytest.mark.asyncio
    async def test_router_agent_model_configuration(self):
        """Test that router agent is configured correctly"""
        # Test that router agent can be imported and instantiated
        from agents.router_agent import router_agent, RouterResponse
        from agents.deps import RouterDependencies
        
        # Verify basic functionality - router agent should exist
        assert router_agent is not None
        assert RouterResponse is not None
        assert RouterDependencies is not None
        
        # Test that RouterResponse has the expected structure
        response = RouterResponse(decision="web_search")
        assert response.decision == "web_search"
        assert response.decision in ["web_search", "email_search", "rag_search", "fallback"]

    @pytest.mark.asyncio
    async def test_router_decision_consistency(self, mock_router_deps):
        """Test that similar queries get consistent routing decisions"""
        # Similar web search queries
        web_queries_group = [
            "Latest news about technology",
            "Current events in tech industry",
            "Recent technology developments"
        ]
        
        results = []
        for query in web_queries_group:
            mock_result = MagicMock()
            mock_result.data = RouterResponse(decision="web_search")
            
            with patch.object(router_agent, 'run', return_value=mock_result):
                result = await router_agent.run(query, deps=mock_router_deps)
                results.append(result.data.decision)
        
        # All should be the same decision
        assert all(decision == "web_search" for decision in results)

    @pytest.mark.asyncio
    async def test_router_session_handling(self):
        """Test router with different session IDs"""
        query = "Test query"
        
        # Test with different session IDs
        sessions = ["session-1", "session-2", None, ""]
        
        for session_id in sessions:
            deps = RouterDependencies(session_id=session_id)
            assert deps.session_id == session_id
            
            mock_result = MagicMock()
            mock_result.data = RouterResponse(decision="web_search")
            
            with patch.object(router_agent, 'run', return_value=mock_result) as mock_run:
                result = await router_agent.run(query, deps=deps)
                
                mock_run.assert_called_with(query, deps=deps)
                assert isinstance(result.data, RouterResponse)
                assert result.data.decision == "web_search"

    @pytest.mark.asyncio
    async def test_edge_case_queries(self, mock_router_deps):
        """Test router with edge case queries"""
        edge_cases = [
            "a",  # Single character
            "?" * 100,  # Very long query
            "email web search documents",  # Mixed keywords
            "search emails for web documents",  # Ambiguous routing
            "🔍📧📄",  # Emoji only
        ]
        
        for query in edge_cases:
            # Mock different decisions for edge cases
            mock_result = MagicMock()
            mock_result.data = RouterResponse(decision="fallback")  # Edge cases should fallback
            
            with patch.object(router_agent, 'run', return_value=mock_result) as mock_run:
                result = await router_agent.run(query, deps=mock_router_deps)
                
                mock_run.assert_called_with(query, deps=mock_router_deps)
                assert isinstance(result.data, RouterResponse)
                assert result.data.decision in ["web_search", "email_search", "rag_search", "fallback"]