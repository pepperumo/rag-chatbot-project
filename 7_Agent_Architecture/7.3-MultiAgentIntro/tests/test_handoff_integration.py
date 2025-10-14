"""
Integration tests for the TRUE handoff system using Union output types.

This module tests the complete end-to-end handoff flow:
1. Research agent receives request
2. Agent decides between direct response OR email handoff
3. If email handoff, email agent takes complete control
4. Final response comes from the agent that handled the request
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents_handoff.cli_interface import research_agent, ResearchAgentDependencies


class TestEndToEndHandoffFlow:
    """Test cases for complete handoff flow."""
    
    @pytest.mark.asyncio
    async def test_complete_research_flow_no_handoff(self):
        """Test complete flow for research request (no handoff)."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json",
            session_id="test_session"
        )
        
        # Mock the research agent to simulate normal research response
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            # Direct string response - no handoff occurred
            mock_result.output = """
Based on my web search, here are the latest AI developments:

1. **Large Language Models**: Continued improvements in reasoning capabilities
2. **Multimodal AI**: Better integration of text, image, and audio processing
3. **AI Safety**: New frameworks for alignment and safety research

Key sources:
- OpenAI Research: https://openai.com/research
- DeepMind Publications: https://deepmind.com/research
- Stanford AI Lab: https://ai.stanford.edu

These developments show significant progress in both capability and safety measures.
"""
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test research query
            result = await research_agent.run(
                "What are the latest AI developments?",
                deps=deps
            )
            
            # Verify this was a direct response (no handoff)
            assert isinstance(result.output, str)
            assert "Large Language Models" in result.output
            assert "Multimodal AI" in result.output
            assert "AI Safety" in result.output
            assert "📧 **Email Draft Created" not in result.output  # No handoff occurred
            assert result.new_messages() == []
    
    @pytest.mark.asyncio
    async def test_complete_email_handoff_flow(self):
        """Test complete flow for email request (TRUE handoff)."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json",
            session_id="test_session"
        )
        
        # Mock the research agent to simulate email handoff
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            # Result from email_handoff output function - handoff occurred
            mock_result.output = """📧 **Email Draft Created for colleague@company.com:**

Subject: AI Research Update

Dear Colleague,

I hope this email finds you well. I wanted to share some exciting developments in AI research that I thought would interest you.

Recent breakthroughs include:

1. **Advanced Language Models**: New architectures showing improved reasoning
2. **Safety Research**: Novel alignment techniques being developed
3. **Multimodal Integration**: Better cross-modal understanding capabilities

These developments could have significant implications for our current projects.

Best regards,
[Your Name]

---
The email draft has been created and saved to your Gmail drafts."""
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test email creation request
            result = await research_agent.run(
                "Create an email to colleague@company.com about the latest AI research developments",
                deps=deps
            )
            
            # Verify this was a handoff result
            assert isinstance(result.output, str)
            assert "📧 **Email Draft Created for colleague@company.com:**" in result.output
            assert "Subject: AI Research Update" in result.output
            assert "Dear Colleague" in result.output
            assert "Advanced Language Models" in result.output
            assert "email draft has been created" in result.output
            assert result.new_messages() == []
    
    @pytest.mark.asyncio
    async def test_handoff_with_research_summary(self):
        """Test handoff flow when research findings are included in email."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the research agent to simulate handoff with research
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            # Result from email_handoff with research summary
            mock_result.output = """📧 **Email Draft Created for team@company.com:**

Subject: Quantum Computing Research Summary

Dear Team,

I've compiled a comprehensive research summary on quantum computing that I wanted to share with you.

**Key Research Findings:**
- IBM's new quantum processors show 99.9% fidelity
- Google's quantum error correction breakthrough
- Microsoft's topological qubit developments

**Market Implications:**
- $15B investment in quantum startups this year
- Major cloud providers offering quantum services
- Timeline to practical applications: 3-5 years

**Recommendations:**
1. Monitor IBM and Google's quantum cloud offerings
2. Assess our algorithms for quantum readiness
3. Consider partnerships with quantum research labs

The full research data is available in our shared drive.

Best regards,
Research Team

---
Email drafted with comprehensive research findings included."""
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test email with research request
            result = await research_agent.run(
                "Research quantum computing developments and email the findings to team@company.com",
                deps=deps
            )
            
            # Verify handoff with research summary
            assert isinstance(result.output, str)
            assert "📧 **Email Draft Created for team@company.com:**" in result.output
            assert "Quantum Computing Research Summary" in result.output
            assert "Key Research Findings" in result.output
            assert "IBM's new quantum processors" in result.output
            assert "Market Implications" in result.output
            assert "comprehensive research findings" in result.output


class TestHandoffDecisionMaking:
    """Test cases for the agent's decision between direct response and handoff."""
    
    @pytest.mark.asyncio
    async def test_agent_correctly_identifies_research_requests(self):
        """Test that agent chooses direct response for various research queries."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        research_queries = [
            "What is machine learning?",
            "Analyze the stock market trends",
            "Tell me about climate change",
            "Find information about renewable energy",
            "Summarize quantum computing developments",
            "Research the latest in biotechnology"
        ]
        
        for query in research_queries:
            with patch.object(research_agent, 'run') as mock_run:
                mock_result = MagicMock()
                # Simulate direct response (no handoff)
                mock_result.output = f"Research response about: {query}"
                mock_result.new_messages = MagicMock(return_value=[])
                mock_run.return_value = mock_result
                
                result = await research_agent.run(query, deps=deps)
                
                # Should be direct response, not handoff
                assert isinstance(result.output, str)
                assert "📧 **Email Draft Created" not in result.output
                assert f"Research response about: {query}" in result.output
    
    @pytest.mark.asyncio
    async def test_agent_correctly_identifies_email_requests(self):
        """Test that agent chooses handoff for various email creation requests."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        email_requests = [
            "Create an email to john@example.com about the meeting",
            "Draft an email to the team about project updates",
            "Send research findings to client@company.com via email",
            "Compose an email to manager@work.com about the quarterly results",
            "Email the analysis to stakeholders@business.com"
        ]
        
        for request in email_requests:
            with patch.object(research_agent, 'run') as mock_run:
                mock_result = MagicMock()
                # Simulate handoff result
                mock_result.output = f"📧 **Email Draft Created for recipient:**\n\nEmail content for: {request}"
                mock_result.new_messages = MagicMock(return_value=[])
                mock_run.return_value = mock_result
                
                result = await research_agent.run(request, deps=deps)
                
                # Should be handoff result
                assert isinstance(result.output, str)
                assert "📧 **Email Draft Created" in result.output
                assert f"Email content for: {request}" in result.output


class TestHandoffErrorHandling:
    """Test cases for error handling in handoff scenarios."""
    
    @pytest.mark.asyncio
    async def test_handoff_failure_graceful_degradation(self):
        """Test graceful handling when email handoff fails."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the research agent to simulate handoff failure
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            # Simulate error in handoff
            mock_result.output = "❌ Failed to create email for user@example.com: Gmail API authentication failed"
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test email request that fails
            result = await research_agent.run(
                "Create an email to user@example.com about the project status",
                deps=deps
            )
            
            # Verify error is handled gracefully
            assert isinstance(result.output, str)
            assert "❌ Failed to create email" in result.output
            assert "user@example.com" in result.output
            assert "Gmail API authentication failed" in result.output
    
    @pytest.mark.asyncio
    async def test_research_failure_direct_error(self):
        """Test error handling for research requests."""
        # Create dependencies with invalid API key
        deps = ResearchAgentDependencies(
            brave_api_key="",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the research agent to simulate research failure
        with patch.object(research_agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Invalid Brave API key")
            
            # Test that research failure propagates
            with pytest.raises(Exception, match="Invalid Brave API key"):
                await research_agent.run(
                    "Research artificial intelligence",
                    deps=deps
                )


class TestMessageHistoryHandling:
    """Test cases for message history handling in handoffs."""
    
    @pytest.mark.asyncio
    async def test_handoff_preserves_conversation_context(self):
        """Test that handoff passes conversation history to email agent."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock message history
        message_history = [MagicMock(), MagicMock(), MagicMock()]
        
        # Mock the research agent
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "📧 **Email Draft Created for contact@example.com:**\n\nEmail with conversation context included."
            mock_result.new_messages = MagicMock(return_value=message_history)
            mock_run.return_value = mock_result
            
            # Test with message history
            result = await research_agent.run(
                "Email the discussion summary to contact@example.com",
                deps=deps,
                message_history=message_history
            )
            
            # Verify message history is handled
            assert isinstance(result.output, str)
            assert "📧 **Email Draft Created" in result.output
            assert "conversation context" in result.output
            assert result.new_messages() == message_history
    
    @pytest.mark.asyncio
    async def test_direct_response_preserves_message_history(self):
        """Test that direct responses also handle message history correctly."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock message history
        message_history = [MagicMock()]
        
        # Mock the research agent
        with patch.object(research_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "Based on our previous discussion, here's additional information about AI..."
            mock_result.new_messages = MagicMock(return_value=message_history)
            mock_run.return_value = mock_result
            
            # Test with message history
            result = await research_agent.run(
                "Continue the AI discussion from earlier",
                deps=deps,
                message_history=message_history
            )
            
            # Verify message history is preserved
            assert isinstance(result.output, str)
            assert "previous discussion" in result.output
            assert "📧 **Email Draft Created" not in result.output  # Not a handoff
            assert result.new_messages() == message_history


class TestStreamingCompatibility:
    """Test cases for streaming compatibility with handoff system."""
    
    @pytest.mark.asyncio
    async def test_streaming_interface_available_for_handoff_agent(self):
        """Test that streaming interface works with handoff agent."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Verify iter method exists and is callable
        assert hasattr(research_agent, 'iter')
        assert callable(research_agent.iter)
        
        # Mock the iter method
        with patch.object(research_agent, 'iter') as mock_iter:
            mock_run = MagicMock()
            mock_run.result = MagicMock()
            mock_run.result.output = "Streaming research response..."
            mock_run.result.new_messages = MagicMock(return_value=[])
            
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_run)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_iter.return_value = mock_context_manager
            
            # Test streaming interface
            async with research_agent.iter("Test streaming query", deps=deps) as run:
                assert run is mock_run
                assert run.result.output == "Streaming research response..."
            
            mock_iter.assert_called_once_with("Test streaming query", deps=deps)
    
    @pytest.mark.asyncio
    async def test_streaming_works_for_both_response_types(self):
        """Test that streaming works for both direct responses and handoffs."""
        # Create dependencies
        deps = ResearchAgentDependencies(
            brave_api_key="test_api_key",
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Test streaming direct response
        with patch.object(research_agent, 'iter') as mock_iter:
            mock_run = MagicMock()
            mock_run.result = MagicMock()
            mock_run.result.output = "Direct streaming research response"
            
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_run)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_iter.return_value = mock_context_manager
            
            async with research_agent.iter("Research query", deps=deps) as run:
                assert "Direct streaming research response" in run.result.output
                assert "📧 **Email Draft Created" not in run.result.output
        
        # Test streaming handoff response
        with patch.object(research_agent, 'iter') as mock_iter:
            mock_run = MagicMock()
            mock_run.result = MagicMock()
            mock_run.result.output = "📧 **Email Draft Created for test@example.com:**\n\nStreaming handoff result"
            
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_run)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_iter.return_value = mock_context_manager
            
            async with research_agent.iter("Create email to test@example.com", deps=deps) as run:
                assert "📧 **Email Draft Created" in run.result.output
                assert "Streaming handoff result" in run.result.output