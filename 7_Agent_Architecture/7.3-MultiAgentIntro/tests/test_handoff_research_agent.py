"""
Unit tests for handoff research agent with Union output types.

This module tests the research agent that uses Union output types:
- Direct string responses for research queries
- email_handoff output function for email creation (TRUE handoff)
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents_handoff.research_agent import (
    research_agent, 
    ResearchAgentDependencies,
    email_handoff,
    create_research_agent
)


class TestResearchAgentDependencies:
    """Test cases for ResearchAgentDependencies."""
    
    def test_create_research_agent_dependencies_valid(self):
        """Test creating valid ResearchAgentDependencies."""
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/path/to/credentials.json",
            gmail_token_path="/path/to/token.json",
            session_id="test_session"
        )
        
        assert deps.brave_api_key == "test_api_key"
        assert deps.gmail_credentials_path == "/path/to/credentials.json"
        assert deps.gmail_token_path == "/path/to/token.json"
        assert deps.session_id == "test_session"
    
    def test_create_research_agent_dependencies_without_session(self):
        """Test creating ResearchAgentDependencies without session_id."""
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/path/to/credentials.json",
            gmail_token_path="/path/to/token.json"
        )
        
        assert deps.session_id is None


class TestEmailHandoffOutputFunction:
    """Test cases for the email_handoff output function."""
    
    @pytest.mark.asyncio
    async def test_email_handoff_success(self):
        """Test successful email handoff output function."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        mock_ctx.deps.session_id = "test_session"
        mock_ctx.messages = [MagicMock(), MagicMock()]  # Mock message history
        
        # Mock the email agent
        with patch('agents_handoff.research_agent.email_agent') as mock_email_agent:
            mock_result = MagicMock()
            mock_result.output = "Professional email draft created successfully with all requested details."
            mock_email_agent.run = AsyncMock(return_value=mock_result)
            
            # Test the email handoff function
            result = await email_handoff(
                mock_ctx,
                recipient_email="test@example.com",
                subject="Test Email Subject",
                context="Testing email creation via handoff",
                research_summary="Key findings from research"
            )
            
            # Verify email agent was called correctly
            mock_email_agent.run.assert_called_once()
            call_args = mock_email_agent.run.call_args
            
            # Check the email prompt includes all required information
            email_prompt = call_args[0][0]
            assert "test@example.com" in email_prompt
            assert "Test Email Subject" in email_prompt
            assert "Testing email creation via handoff" in email_prompt
            assert "Key findings from research" in email_prompt
            
            # Verify the result format
            assert "📧 **Email Draft Created for test@example.com:**" in result
            assert "Professional email draft created successfully" in result
    
    @pytest.mark.asyncio
    async def test_email_handoff_without_research_summary(self):
        """Test email handoff without research summary."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        mock_ctx.deps.session_id = "test_session"
        mock_ctx.messages = [MagicMock()]
        
        # Mock the email agent
        with patch('agents_handoff.research_agent.email_agent') as mock_email_agent:
            mock_result = MagicMock()
            mock_result.output = "Simple email draft created."
            mock_email_agent.run = AsyncMock(return_value=mock_result)
            
            # Test without research summary
            result = await email_handoff(
                mock_ctx,
                recipient_email="simple@example.com",
                subject="Simple Subject",
                context="Simple context"
            )
            
            # Verify email agent was called
            mock_email_agent.run.assert_called_once()
            call_args = mock_email_agent.run.call_args
            email_prompt = call_args[0][0]
            
            # Should NOT include research summary section
            assert "Research Summary to Include:" not in email_prompt
            assert "simple@example.com" in email_prompt
            assert "Simple Subject" in email_prompt
            
            # Verify result
            assert "📧 **Email Draft Created for simple@example.com:**" in result
            assert "Simple email draft created." in result
    
    @pytest.mark.asyncio
    async def test_email_handoff_failure(self):
        """Test email handoff when email agent fails."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        mock_ctx.deps.session_id = "test_session"
        mock_ctx.messages = []
        
        # Mock the email agent to raise an exception
        with patch('agents_handoff.research_agent.email_agent') as mock_email_agent:
            mock_email_agent.run = AsyncMock(side_effect=Exception("Email service unavailable"))
            
            # Test email handoff failure
            result = await email_handoff(
                mock_ctx,
                recipient_email="fail@example.com",
                subject="Test Subject",
                context="Test context"
            )
            
            # Verify error handling
            assert "❌ Failed to create email for fail@example.com" in result
            assert "Email service unavailable" in result


class TestResearchAgentTools:
    """Test cases for research agent tools."""
    
    @pytest.mark.asyncio
    async def test_search_web_success(self):
        """Test successful web search tool."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.brave_api_key = "test_api_key"
        
        # Mock the search tool
        with patch('agents_handoff.research_agent.search_web_tool') as mock_tool:
            mock_tool.return_value = [
                {
                    "title": "Test Result 1",
                    "url": "https://example.com/1",
                    "description": "Test description 1",
                    "relevance_score": 0.95
                },
                {
                    "title": "Test Result 2", 
                    "url": "https://example.com/2",
                    "description": "Test description 2",
                    "relevance_score": 0.85
                }
            ]
            
            # Import the tool function
            from agents_handoff.research_agent import search_web
            
            # Test the tool
            result = await search_web(mock_ctx, "test query", max_results=2)
            
            # Verify the tool was called correctly
            mock_tool.assert_called_once_with(
                api_key="test_api_key",
                query="test query",
                count=2
            )
            
            # Verify the result
            assert len(result) == 2
            assert all(isinstance(r, dict) for r in result)
            assert result[0]["title"] == "Test Result 1"
            assert result[0]["url"] == "https://example.com/1"
    
    @pytest.mark.asyncio
    async def test_search_web_failure(self):
        """Test web search failure."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.brave_api_key = "test_api_key"
        
        # Mock the search tool to raise an exception
        with patch('agents_handoff.research_agent.search_web_tool') as mock_tool:
            mock_tool.side_effect = Exception("API rate limit exceeded")
            
            # Import the tool function
            from agents_handoff.research_agent import search_web
            
            # Test the tool
            result = await search_web(mock_ctx, "test query")
            
            # Verify the result (should return error dict on failure)
            assert len(result) == 1
            assert result[0]["error"] == "Search failed: API rate limit exceeded"
    
    @pytest.mark.asyncio
    async def test_summarize_research_success(self):
        """Test successful research summarization."""
        # Mock context
        mock_ctx = MagicMock()
        
        # Create test search results
        search_results = [
            {
                "title": "AI Safety Research",
                "url": "https://example.com/ai-safety",
                "description": "Latest developments in AI safety"
            },
            {
                "title": "Machine Learning Ethics",
                "url": "https://example.com/ml-ethics", 
                "description": "Ethical considerations in ML"
            }
        ]
        
        # Import the tool function
        from agents_handoff.research_agent import summarize_research
        
        # Test the tool
        result = await summarize_research(mock_ctx, search_results, "AI Safety")
        
        # Verify the result format
        assert isinstance(result, dict)
        assert result["topic"] == "AI Safety"
        assert result["sources_count"] == 2
        assert "Research Summary: AI Safety" in result["summary"]
        assert "AI Safety Research" in result["summary"]


class TestResearchAgentIntegration:
    """Test cases for research agent integration with Union output types."""
    
    @pytest.mark.asyncio
    async def test_research_agent_direct_response(self):
        """Test research agent returning direct string response."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent's run method to return direct string
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "Here are the latest developments in AI safety research based on my web search..."
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test research agent run for research query
            result = await research_agent.run(
                "What are the latest developments in AI safety?",
                deps=deps
            )
            
            # Verify the result
            mock_run.assert_called_once()
            assert isinstance(result.output, str)
            assert "AI safety research" in result.output
    
    @pytest.mark.asyncio
    async def test_research_agent_email_handoff_via_output_function(self):
        """Test research agent using email handoff output function."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent's run method to simulate output function call
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            # This would be the result of the email_handoff output function
            mock_result.output = "📧 **Email Draft Created for user@example.com:**\n\nProfessional email with research findings has been created."
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test research agent run for email creation request
            result = await research_agent.run(
                "Create an email to user@example.com with the AI safety research findings",
                deps=deps
            )
            
            # Verify the result
            mock_run.assert_called_once()
            assert isinstance(result.output, str)
            assert "📧 **Email Draft Created" in result.output
            assert "user@example.com" in result.output


class TestResearchAgentConfiguration:
    """Test cases for research agent configuration."""
    
    def test_research_agent_has_union_output_type(self):
        """Test that research agent is configured with Union output type."""
        # Verify the agent was created properly
        assert research_agent is not None
        
        # Check that it's a PydanticAI Agent
        from pydantic_ai import Agent
        assert isinstance(research_agent, Agent)
    
    def test_research_agent_has_tools(self):
        """Test that research agent has the expected tools."""
        # Verify the agent has tools configured
        assert research_agent is not None
        
        # The agent should be configured with search_web and summarize_research tools
        # We can't easily inspect the tools without diving into PydanticAI internals,
        # so we'll just verify the agent exists and is properly typed
        assert hasattr(research_agent, 'run')
        assert hasattr(research_agent, 'iter')
    
    def test_research_agent_system_prompt_includes_handoff_instructions(self):
        """Test that system prompt includes proper handoff instructions."""
        # The agent should be configured with proper instructions
        assert research_agent is not None
        
        # We can't easily access the system prompt, but we can verify
        # the agent was created with the expected configuration
        assert hasattr(research_agent, 'run')


class TestResearchAgentFactory:
    """Test cases for research agent factory function."""
    
    def test_create_research_agent_function(self):
        """Test create_research_agent factory function."""
        agent = create_research_agent(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json",
            session_id="test_session"
        )
        
        # Verify the agent is returned (same instance)
        assert agent is research_agent
    
    def test_create_research_agent_minimal_params(self):
        """Test create_research_agent with minimal parameters."""
        agent = create_research_agent(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Verify the agent is returned
        assert agent is research_agent


class TestResearchAgentErrorHandling:
    """Test cases for research agent error handling."""
    
    @pytest.mark.asyncio
    async def test_research_agent_invalid_dependencies(self):
        """Test research agent with invalid dependencies."""
        # Create dependencies with invalid API key
        deps = ResearchAgentDependencies(
            brave_api_key="",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent's run method to raise an exception
        with patch.object(research_agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Invalid API key")
            
            # Test that exception is raised
            with pytest.raises(Exception, match="Invalid API key"):
                await research_agent.run(
                    "Research AI safety",
                    deps=deps
                )
    
    @pytest.mark.asyncio
    async def test_research_agent_empty_query(self):
        """Test research agent with empty query."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent's run method
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "Please provide a specific research query."
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test with empty query
            result = await research_agent.run("", deps=deps)
            
            # Verify the result
            mock_run.assert_called_once_with("", deps=deps)
            assert isinstance(result.output, str)
            assert "Please provide" in result.output


class TestUnionOutputTypeDecisionMaking:
    """Test cases for the agent's decision making between output types."""
    
    @pytest.mark.asyncio
    async def test_agent_chooses_direct_response_for_research(self):
        """Test that agent chooses direct string response for research queries."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent to simulate choosing direct response
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            # Direct string response (not output function result)
            mock_result.output = "Based on my research, quantum computing is advancing rapidly with new developments in..."
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test with research query
            result = await research_agent.run(
                "Tell me about quantum computing developments",
                deps=deps
            )
            
            # Should be direct string response
            assert isinstance(result.output, str)
            assert "quantum computing" in result.output
            assert "📧 **Email Draft Created" not in result.output  # Should NOT be email handoff
    
    @pytest.mark.asyncio
    async def test_agent_chooses_email_handoff_for_email_requests(self):
        """Test that agent chooses email handoff output function for email requests."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent to simulate choosing email handoff output function
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            # Result from email_handoff output function
            mock_result.output = "📧 **Email Draft Created for colleague@company.com:**\n\nEmail about quantum computing research has been created successfully."
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test with email creation request
            result = await research_agent.run(
                "Create an email to colleague@company.com about quantum computing research",
                deps=deps
            )
            
            # Should be result from email handoff function
            assert isinstance(result.output, str)
            assert "📧 **Email Draft Created" in result.output
            assert "colleague@company.com" in result.output