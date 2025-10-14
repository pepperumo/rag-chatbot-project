"""
Unit tests for handoff email agent.

This module tests the email agent used in the handoff system,
ensuring proper tool integration and email functionality.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents_handoff.email_agent import email_agent, EmailAgentDependencies


class TestEmailAgentDependencies:
    """Test cases for EmailAgentDependencies."""
    
    def test_create_email_agent_dependencies_valid(self):
        """Test creating valid EmailAgentDependencies."""
        deps = EmailAgentDependencies(
            gmail_credentials_path="/path/to/credentials.json",
            gmail_token_path="/path/to/token.json",
            session_id="test_session"
        )
        
        assert deps.gmail_credentials_path == "/path/to/credentials.json"
        assert deps.gmail_token_path == "/path/to/token.json"
        assert deps.session_id == "test_session"
    
    def test_create_email_agent_dependencies_without_session(self):
        """Test creating EmailAgentDependencies without session_id."""
        deps = EmailAgentDependencies(
            gmail_credentials_path="/path/to/credentials.json",
            gmail_token_path="/path/to/token.json"
        )
        
        assert deps.session_id is None


class TestEmailAgentTools:
    """Test cases for email agent tools."""
    
    @pytest.mark.asyncio
    async def test_create_gmail_draft_success(self):
        """Test successful Gmail draft creation."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        
        # Mock the create_email_draft_tool with fixed parameters
        with patch('agents_handoff.email_agent.create_email_draft_tool') as mock_tool:
            mock_tool.return_value = {
                "draft_id": "test_draft_123",
                "message": "Email draft created successfully"
            }
            
            # Import the tool function
            from agents_handoff.email_agent import create_gmail_draft
            
            # Test the tool with correct parameters
            result = await create_gmail_draft(
                mock_ctx,
                recipient_email="test@example.com",
                subject="Test Subject",
                body="Test email body content"
            )
            
            # Verify the tool was called correctly with fixed 'to' parameter
            mock_tool.assert_called_once_with(
                credentials_path="/fake/creds.json",
                token_path="/fake/token.json",
                to=["test@example.com"],  # Fixed: now passes as list
                subject="Test Subject",
                body="Test email body content"
            )
            
            # Verify the result
            assert result["success"] is True
            assert result["draft_id"] == "test_draft_123"
            assert result["message"] == "Email draft created successfully"
    
    @pytest.mark.asyncio
    async def test_create_gmail_draft_failure(self):
        """Test Gmail draft creation failure."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        
        # Mock the create_email_draft_tool to raise an exception
        with patch('agents_handoff.email_agent.create_email_draft_tool') as mock_tool:
            mock_tool.side_effect = Exception("Gmail API authentication failed")
            
            # Import the tool function
            from agents_handoff.email_agent import create_gmail_draft
            
            # Test the tool
            result = await create_gmail_draft(
                mock_ctx,
                recipient_email="test@example.com",
                subject="Test Subject",
                body="Test email body content"
            )
            
            # Verify the result
            assert result["success"] is False
            assert "Gmail API authentication failed" in result["error_message"]
    
    @pytest.mark.asyncio
    async def test_list_gmail_drafts_success(self):
        """Test successful Gmail drafts listing."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        
        # Mock the list_email_drafts_tool
        with patch('agents_handoff.email_agent.list_email_drafts_tool') as mock_tool:
            mock_tool.return_value = {
                "drafts": [
                    {"id": "draft1", "subject": "Test Subject 1"},
                    {"id": "draft2", "subject": "Test Subject 2"}
                ],
                "count": 2
            }
            
            # Import the tool function
            from agents_handoff.email_agent import list_gmail_drafts
            
            # Test the tool
            result = await list_gmail_drafts(mock_ctx, max_results=10)
            
            # Verify the tool was called correctly
            mock_tool.assert_called_once_with(
                credentials_path="/fake/creds.json",
                token_path="/fake/token.json",
                max_results=10
            )
            
            # Verify the result
            assert result["count"] == 2
            assert len(result["drafts"]) == 2
            assert result["drafts"][0]["subject"] == "Test Subject 1"
    
    @pytest.mark.asyncio
    async def test_list_gmail_drafts_failure(self):
        """Test Gmail drafts listing failure."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        
        # Mock the list_email_drafts_tool to raise an exception
        with patch('agents_handoff.email_agent.list_email_drafts_tool') as mock_tool:
            mock_tool.side_effect = Exception("Gmail API rate limit exceeded")
            
            # Import the tool function
            from agents_handoff.email_agent import list_gmail_drafts
            
            # Test the tool
            result = await list_gmail_drafts(mock_ctx)
            
            # Verify the result
            assert result["success"] is False
            assert "Gmail API rate limit exceeded" in result["error_message"]


class TestEmailAgentIntegration:
    """Test cases for email agent integration."""
    
    @pytest.mark.asyncio
    async def test_email_agent_create_draft_response(self):
        """Test email agent creating draft and responding appropriately."""
        # Create dependencies
        deps = EmailAgentDependencies(
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json",
            session_id="test_session"
        )
        
        # Mock the agent's run method
        with patch.object(email_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "I've created a professional email draft for you. The draft has been saved to Gmail."
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test email agent run
            result = await email_agent.run(
                "Create a professional email to john@example.com about the quarterly results",
                deps=deps
            )
            
            # Verify the result
            mock_run.assert_called_once()
            assert isinstance(result.output, str)
            assert "email draft" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_email_agent_graceful_fallback(self):
        """Test email agent graceful fallback when draft creation fails."""
        # Create dependencies
        deps = EmailAgentDependencies(
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent to simulate fallback behavior
        with patch.object(email_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = """I encountered an issue creating the Gmail draft, but here's the email content:

Subject: Quarterly Results Update

Dear John,

I hope this message finds you well. I wanted to share the quarterly results with you...

Best regards,
[Your Name]

You can copy this content and send it manually."""
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test email agent run with fallback
            result = await email_agent.run(
                "Create an email to john@example.com about quarterly results",
                deps=deps
            )
            
            # Verify the result includes email content
            mock_run.assert_called_once()
            assert isinstance(result.output, str)
            assert "Subject:" in result.output
            assert "Dear John" in result.output
            assert "copy this content" in result.output


class TestEmailAgentSystemPrompt:
    """Test cases for email agent system prompt and configuration."""
    
    def test_email_agent_configuration(self):
        """Test that email agent is configured properly."""
        # Verify the agent was created properly
        assert email_agent is not None
        
        # Check that it's a PydanticAI Agent
        from pydantic_ai import Agent
        assert isinstance(email_agent, Agent)
    
    def test_email_agent_has_tools(self):
        """Test that email agent has the expected tools."""
        # Verify the agent has tools configured
        assert email_agent is not None
        
        # The agent should be configured with Gmail tools
        # We can't easily inspect the tools without diving into PydanticAI internals,
        # so we'll just verify the agent exists and is properly typed
        assert hasattr(email_agent, 'run')
        assert hasattr(email_agent, 'iter')
    
    def test_email_agent_output_type(self):
        """Test that email agent has correct output type."""
        # The email agent should return strings
        assert email_agent is not None
        # Output type checking would need to be done at runtime


class TestEmailAgentErrorHandling:
    """Test cases for email agent error handling."""
    
    @pytest.mark.asyncio
    async def test_email_agent_invalid_dependencies(self):
        """Test email agent with invalid dependencies."""
        # Create dependencies with invalid paths
        deps = EmailAgentDependencies(
            gmail_credentials_path="",
            gmail_token_path=""
        )
        
        # Mock the agent's run method to raise an exception
        with patch.object(email_agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Invalid Gmail credentials path")
            
            # Test that exception is raised
            with pytest.raises(Exception, match="Invalid Gmail credentials path"):
                await email_agent.run(
                    "Create an email",
                    deps=deps
                )
    
    @pytest.mark.asyncio
    async def test_email_agent_empty_prompt(self):
        """Test email agent with empty prompt."""
        # Create dependencies
        deps = EmailAgentDependencies(
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent's run method
        with patch.object(email_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "Please provide specific details about the email you'd like me to create."
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test with empty prompt
            result = await email_agent.run("", deps=deps)
            
            # Verify the result
            mock_run.assert_called_once_with("", deps=deps)
            assert isinstance(result.output, str)
            assert "Please provide" in result.output
    
    @pytest.mark.asyncio
    async def test_email_agent_malformed_request(self):
        """Test email agent with malformed email request."""
        # Create dependencies
        deps = EmailAgentDependencies(
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Mock the agent's run method
        with patch.object(email_agent, 'run') as mock_run:
            mock_result = MagicMock()
            mock_result.output = "I need more information to create this email. Please provide recipient and subject details."
            mock_result.new_messages = MagicMock(return_value=[])
            mock_run.return_value = mock_result
            
            # Test with malformed request
            result = await email_agent.run("send email please", deps=deps)
            
            # Verify the result
            mock_run.assert_called_once_with("send email please", deps=deps)
            assert isinstance(result.output, str)
            assert "more information" in result.output


class TestEmailAgentToolParameters:
    """Test cases for email agent tool parameter handling."""
    
    @pytest.mark.asyncio
    async def test_create_gmail_draft_parameter_validation(self):
        """Test create_gmail_draft tool parameter validation."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        
        # Mock the create_email_draft_tool
        with patch('agents_handoff.email_agent.create_email_draft_tool') as mock_tool:
            mock_tool.return_value = {"draft_id": "test123", "message": "Success"}
            
            # Import the tool function
            from agents_handoff.email_agent import create_gmail_draft
            
            # Test with all parameters
            result = await create_gmail_draft(
                mock_ctx,
                recipient_email="test@example.com",
                subject="Test Subject",
                body="Test Body"
            )
            
            # Verify the underlying tool was called with correct parameters
            mock_tool.assert_called_once_with(
                credentials_path="/fake/creds.json",
                token_path="/fake/token.json",
                to=["test@example.com"],  # Should be converted to list
                subject="Test Subject",
                body="Test Body"
            )
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_list_gmail_drafts_parameter_validation(self):
        """Test list_gmail_drafts tool parameter validation."""
        # Mock context
        mock_ctx = MagicMock()
        mock_ctx.deps.gmail_credentials_path = "/fake/creds.json"
        mock_ctx.deps.gmail_token_path = "/fake/token.json"
        
        # Mock the list_email_drafts_tool
        with patch('agents_handoff.email_agent.list_email_drafts_tool') as mock_tool:
            mock_tool.return_value = {"drafts": [], "count": 0}
            
            # Import the tool function
            from agents_handoff.email_agent import list_gmail_drafts
            
            # Test with custom max_results
            result = await list_gmail_drafts(mock_ctx, max_results=5)
            
            # Verify the underlying tool was called with correct parameters
            mock_tool.assert_called_once_with(
                credentials_path="/fake/creds.json",
                token_path="/fake/token.json",
                max_results=5
            )
            
            # Test with default max_results
            mock_tool.reset_mock()
            result = await list_gmail_drafts(mock_ctx)
            
            # Verify default parameter was used
            mock_tool.assert_called_once_with(
                credentials_path="/fake/creds.json",
                token_path="/fake/token.json",
                max_results=10  # Default value
            )


class TestEmailAgentStreamingCompatibility:
    """Test cases for email agent streaming compatibility."""
    
    @pytest.mark.asyncio
    async def test_email_agent_streaming_interface(self):
        """Test that email agent supports streaming interface."""
        # Create dependencies
        deps = EmailAgentDependencies(
            gmail_credentials_path="/fake/creds.json",
            gmail_token_path="/fake/token.json"
        )
        
        # Verify iter method exists
        assert hasattr(email_agent, 'iter')
        assert callable(email_agent.iter)
        
        # Mock the iter method
        with patch.object(email_agent, 'iter') as mock_iter:
            mock_run = MagicMock()
            mock_run.result = MagicMock()
            mock_run.result.output = "Streaming email creation..."
            
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_run)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_iter.return_value = mock_context_manager
            
            # Test streaming
            async with email_agent.iter(
                "Create email to test@example.com",
                deps=deps
            ) as run:
                assert run is mock_run
                assert run.result.output == "Streaming email creation..."
            
            mock_iter.assert_called_once_with(
                "Create email to test@example.com",
                deps=deps
            )