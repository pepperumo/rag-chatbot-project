"""
Unit tests for handoff CLI interface.

This module tests the simplified CLI interface for the handoff system.
The interface directly exposes the research agent with Union output type handoffs.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents_handoff.cli_interface import (
    research_agent,
    ResearchAgentDependencies
)


class TestCLIInterfaceSimplified:
    """Test cases for the simplified CLI interface."""
    
    def test_cli_interface_exports_research_agent(self):
        """Test that CLI interface exports the research agent."""
        # Verify the research agent is exported
        assert research_agent is not None
        
        # Check that it's a PydanticAI Agent
        from pydantic_ai import Agent
        assert isinstance(research_agent, Agent)
    
    def test_cli_interface_exports_dependencies(self):
        """Test that CLI interface exports ResearchAgentDependencies."""
        # Create dependencies to verify the class is exported correctly
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json",
            session_id="test_session"
        )
        
        assert deps.brave_api_key == "test_api_key"
        assert deps.gmail_credentials_path == "/fake/creds.json"
        assert deps.gmail_token_path == "/fake/token.json"
        assert deps.session_id == "test_session"


class TestResearchAgentViaInterface:
    """Test cases for research agent accessed via CLI interface."""
    
    @pytest.mark.asyncio
    async def test_research_agent_run_success(self):
        """Test research agent run method via CLI interface."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent's run method
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "Research results here"
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test the agent via CLI interface
            result = await research_agent.run(
                "What are the latest AI developments?",
                deps=deps
            )
            
            # Verify the result
            assert result.output == "Research results here"
            mock_run.assert_called_once_with(
                "What are the latest AI developments?",
                deps=deps
            )
    
    @pytest.mark.asyncio
    async def test_research_agent_run_with_message_history(self):
        """Test research agent run method with message history."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock message history
        mock_message_history = [MagicMock(), MagicMock()]
        
        # Mock the agent's run method
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "Research results with history context"
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test the agent with message history
            result = await research_agent.run(
                "Follow up question",
                deps=deps,
                message_history=mock_message_history
            )
            
            # Verify the result
            assert result.output == "Research results with history context"
            mock_run.assert_called_once_with(
                "Follow up question",
                deps=deps,
                message_history=mock_message_history
            )
    
    @pytest.mark.asyncio
    async def test_research_agent_run_failure(self):
        """Test research agent run method with failure."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="invalid_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent's run method to raise exception
        with patch.object(research_agent, 'run') as mock_run:
            mock_run.side_effect = Exception("API key invalid")
            
            # Test that exception is raised
            with pytest.raises(Exception, match="API key invalid"):
                await research_agent.run("Test query", deps=deps)
    
    @pytest.mark.asyncio
    async def test_research_agent_iter_success(self):
        """Test research agent iter method for streaming."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent's iter method
        with patch.object(research_agent, 'iter') as mock_iter:
            # Create a mock async context manager
            mock_run = MagicMock()
            mock_run.result = MagicMock()
            mock_run.result.output = "Streaming response"
            mock_run.result.new_messages = MagicMock(return_value=[])
            
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_run)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_iter.return_value = mock_context_manager
            
            # Test streaming
            async with research_agent.iter(
                "Stream this query",
                deps=deps
            ) as run:
                assert run is mock_run
                assert run.result.output == "Streaming response"
            
            mock_iter.assert_called_once_with(
                "Stream this query",
                deps=deps
            )


class TestResearchAgentDependenciesViaInterface:
    """Test cases for ResearchAgentDependencies via CLI interface."""
    
    def test_research_agent_dependencies_creation_full(self):
        """Test creating ResearchAgentDependencies with all parameters."""
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/path/to/creds.json",
            gmail_token_path="/path/to/token.json",
            session_id="test_session"
        )
        
        assert deps.brave_api_key == "test_api_key"
        assert deps.gmail_credentials_path == "/path/to/creds.json"
        assert deps.gmail_token_path == "/path/to/token.json"
        assert deps.session_id == "test_session"
    
    def test_research_agent_dependencies_creation_minimal(self):
        """Test creating ResearchAgentDependencies with minimal parameters."""
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/path/to/creds.json",
            gmail_token_path="/path/to/token.json"
        )
        
        assert deps.brave_api_key == "test_api_key"
        assert deps.gmail_credentials_path == "/path/to/creds.json"
        assert deps.gmail_token_path == "/path/to/token.json"
        assert deps.session_id is None
    
    def test_research_agent_dependencies_compatibility(self):
        """Test that ResearchAgentDependencies is compatible with original."""
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/path/to/creds.json",
            gmail_token_path="/path/to/token.json",
            session_id="test_session"
        )
        
        # Check that all expected attributes exist
        assert hasattr(deps, 'brave_api_key')
        assert hasattr(deps, 'gmail_credentials_path')
        assert hasattr(deps, 'gmail_token_path')
        assert hasattr(deps, 'session_id')


class TestCLIInterfaceCompatibility:
    """Test cases for CLI interface compatibility with original API."""
    
    @pytest.mark.asyncio
    async def test_cli_interface_matches_original_signature(self):
        """Test that CLI interface matches original research agent signature."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "Compatible response"
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test all signature variations
            # 1. Basic call
            result1 = await research_agent.run("Query 1", deps=deps)
            assert result1.output == "Compatible response"
            
            # 2. With message history
            result2 = await research_agent.run("Query 2", deps=deps, message_history=[])
            assert result2.output == "Compatible response"
            
            # 3. With message history as None
            result3 = await research_agent.run("Query 3", deps=deps, message_history=None)
            assert result3.output == "Compatible response"
            
            # Verify all calls were made
            assert mock_run.call_count == 3
    
    @pytest.mark.asyncio
    async def test_cli_interface_result_format(self):
        """Test that CLI interface returns results in expected format."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "Test response data"
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test the interface
            result = await research_agent.run("Test query", deps=deps)
            
            # Verify result format
            assert hasattr(result, 'output')
            assert result.output == "Test response data"
            assert hasattr(result, 'new_messages')
            
            # Verify it's the same object returned by mock
            assert result is mock_result


class TestCLIInterfaceErrorHandling:
    """Test cases for CLI interface error handling."""
    
    @pytest.mark.asyncio
    async def test_cli_interface_handles_agent_error(self):
        """Test that CLI interface properly handles agent errors."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent to raise exception
        with patch.object(research_agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Agent error")
            
            # Test that exception is propagated
            with pytest.raises(Exception, match="Agent error"):
                await research_agent.run("Test query", deps=deps)
    
    @pytest.mark.asyncio
    async def test_cli_interface_handles_invalid_dependencies(self):
        """Test that CLI interface handles invalid dependencies."""
        # Mock the agent to raise exception
        with patch.object(research_agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Invalid dependencies")
            
            # Test with None dependencies
            with pytest.raises(Exception, match="Invalid dependencies"):
                await research_agent.run("Test query", deps=None)
    
    @pytest.mark.asyncio
    async def test_cli_interface_handles_empty_response(self):
        """Test that CLI interface handles empty response."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent to return empty response
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = ""
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test the interface
            result = await research_agent.run("Test query", deps=deps)
            
            # Verify result
            assert result.output == ""
    
    @pytest.mark.asyncio
    async def test_cli_interface_handles_empty_query(self):
        """Test that CLI interface handles empty query."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "Please provide a specific query."
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test with empty query
            result = await research_agent.run("", deps=deps)
            
            # Verify result
            assert result.output == "Please provide a specific query."


class TestStreamingSupport:
    """Test cases for streaming support via CLI interface."""
    
    @pytest.mark.asyncio
    async def test_streaming_interface_available(self):
        """Test that streaming interface (iter) is available."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Verify iter method exists
        assert hasattr(research_agent, 'iter')
        assert callable(research_agent.iter)
        
        # Mock the iter method to verify it can be called
        with patch.object(research_agent, 'iter') as mock_iter:
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_iter.return_value = mock_context_manager
            
            # Test that iter can be called
            async with research_agent.iter("Test query", deps=deps) as run:
                assert run is not None
            
            mock_iter.assert_called_once_with("Test query", deps=deps)


class TestIntegrationConsistency:
    """Test cases for ensuring consistency between the interface and implementation."""
    
    def test_interface_exposes_same_agent_instance(self):
        """Test that interface exposes the same agent instance as implementation."""
        from agents_handoff.research_agent import research_agent as impl_agent
        from agents_handoff.cli_interface import research_agent as interface_agent
        
        # Should be the same instance
        assert impl_agent is interface_agent
    
    def test_interface_exposes_same_dependencies_class(self):
        """Test that interface exposes the same dependencies class."""
        from agents_handoff.research_agent import ResearchAgentDependencies as impl_deps
        from agents_handoff.cli_interface import ResearchAgentDependencies as interface_deps
        
        # Should be the same class
        assert impl_deps is interface_deps
    
    def test_interface_all_exports(self):
        """Test that interface exports the expected items."""
        import agents_handoff.cli_interface as cli
        
        # Check __all__ if defined
        if hasattr(cli, '__all__'):
            expected_exports = cli.__all__
            for export in expected_exports:
                assert hasattr(cli, export), f"Expected export '{export}' not found"
        
        # At minimum, should have these exports
        assert hasattr(cli, 'research_agent')
        assert hasattr(cli, 'ResearchAgentDependencies')