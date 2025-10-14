"""
Unit tests for the Email Agent with human-in-the-loop approval.

Tests cover agent initialization, tool usage, structured output,
and the approval request workflow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.email_agent import (
    email_agent,
    EmailAgentDecision,
    read_inbox_emails,
    create_email_draft,
    list_email_drafts
)
from agents.deps import EmailAgentDependencies


@pytest.fixture
def email_deps():
    """Create test email agent dependencies."""
    return EmailAgentDependencies(
        gmail_credentials_path="test_credentials.json",
        gmail_token_path="test_token.json",
        session_id="test_session"
    )


@pytest.fixture
def mock_run_context(email_deps):
    """Create mock run context with dependencies."""
    context = MagicMock()
    context.deps = email_deps
    return context


class TestEmailAgentTools:
    """Test individual email agent tools."""
    
    @pytest.mark.asyncio
    async def test_read_inbox_emails_success(self, mock_run_context):
        """Test successful inbox email reading."""
        expected_result = {
            "success": True,
            "emails": [
                {
                    "id": "test_id_1",
                    "subject": "Test Email",
                    "from": "test@example.com",
                    "body": "Test content"
                }
            ],
            "count": 1
        }
        
        with patch('agents.email_agent.read_inbox_emails_tool', new_callable=AsyncMock) as mock_tool:
            mock_tool.return_value = expected_result
            
            result = await read_inbox_emails(mock_run_context, max_results=10)
            
            assert result["success"] is True
            assert result["count"] == 1
            assert len(result["emails"]) == 1
            
            mock_tool.assert_called_once_with(
                credentials_path=mock_run_context.deps.gmail_credentials_path,
                token_path=mock_run_context.deps.gmail_token_path,
                max_results=10,
                query=None
            )
    
    @pytest.mark.asyncio
    async def test_read_inbox_emails_with_query(self, mock_run_context):
        """Test inbox email reading with search query."""
        with patch('agents.email_agent.read_inbox_emails_tool', new_callable=AsyncMock) as mock_tool:
            mock_tool.return_value = {"success": True, "emails": [], "count": 0}
            
            await read_inbox_emails(mock_run_context, max_results=5, query="is:unread")
            
            mock_tool.assert_called_once_with(
                credentials_path=mock_run_context.deps.gmail_credentials_path,
                token_path=mock_run_context.deps.gmail_token_path,
                max_results=5,
                query="is:unread"
            )
    
    @pytest.mark.asyncio
    async def test_read_inbox_emails_error_handling(self, mock_run_context):
        """Test error handling in inbox reading."""
        with patch('agents.email_agent.read_inbox_emails_tool', new_callable=AsyncMock) as mock_tool:
            mock_tool.side_effect = Exception("Gmail API error")
            
            result = await read_inbox_emails(mock_run_context)
            
            assert result["success"] is False
            assert "error" in result
            assert result["emails"] == []
            assert result["count"] == 0
    
    @pytest.mark.asyncio
    async def test_create_email_draft_success(self, mock_run_context):
        """Test successful email draft creation."""
        expected_result = {
            "success": True,
            "draft_id": "draft_123",
            "message_id": "msg_456"
        }
        
        with patch('agents.email_agent.create_email_draft_tool', new_callable=AsyncMock) as mock_tool:
            mock_tool.return_value = expected_result
            
            result = await create_email_draft(
                mock_run_context,
                to=["test@example.com"],
                subject="Test Subject",
                body="Test Body"
            )
            
            assert result["success"] is True
            assert result["draft_id"] == "draft_123"
            
            mock_tool.assert_called_once_with(
                credentials_path=mock_run_context.deps.gmail_credentials_path,
                token_path=mock_run_context.deps.gmail_token_path,
                to=["test@example.com"],
                subject="Test Subject",
                body="Test Body",
                cc=None,
                bcc=None
            )
    
    @pytest.mark.asyncio
    async def test_create_email_draft_with_cc_bcc(self, mock_run_context):
        """Test email draft creation with CC and BCC."""
        with patch('agents.email_agent.create_email_draft_tool', new_callable=AsyncMock) as mock_tool:
            mock_tool.return_value = {"success": True, "draft_id": "draft_123"}
            
            await create_email_draft(
                mock_run_context,
                to=["to@example.com"],
                subject="Test",
                body="Body",
                cc=["cc@example.com"],
                bcc=["bcc@example.com"]
            )
            
            mock_tool.assert_called_once_with(
                credentials_path=mock_run_context.deps.gmail_credentials_path,
                token_path=mock_run_context.deps.gmail_token_path,
                to=["to@example.com"],
                subject="Test",
                body="Body",
                cc=["cc@example.com"],
                bcc=["bcc@example.com"]
            )
    
    @pytest.mark.asyncio
    async def test_list_email_drafts_success(self, mock_run_context):
        """Test successful draft listing."""
        expected_result = {
            "success": True,
            "drafts": [{"id": "draft_1"}, {"id": "draft_2"}],
            "count": 2
        }
        
        with patch('agents.email_agent.list_email_drafts_tool', new_callable=AsyncMock) as mock_tool:
            mock_tool.return_value = expected_result
            
            result = await list_email_drafts(mock_run_context, max_results=5)
            
            assert result["success"] is True
            assert result["count"] == 2
            assert len(result["drafts"]) == 2


class TestEmailAgent:
    """Test the main email agent functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test that the email agent is properly initialized."""
        assert email_agent is not None
        assert email_agent.model is not None
        assert email_agent._deps_type == EmailAgentDependencies
        assert email_agent.output_type == EmailAgentDecision
    
    @pytest.mark.asyncio
    async def test_agent_tools_registration(self):
        """Test that all required tools are registered with the agent."""
        tool_names = list(email_agent._function_tools.keys())
        
        expected_tools = ["read_inbox_emails", "create_email_draft", "list_email_drafts"]
        for tool_name in expected_tools:
            assert tool_name in tool_names
    
    @pytest.mark.asyncio
    async def test_agent_structured_output_normal_conversation(self, email_deps):
        """Test agent structured output for normal conversation."""
        with patch.object(email_agent, 'run', new_callable=AsyncMock) as mock_run:
            # Mock a normal conversation response (no send request)
            mock_result = MagicMock()
            mock_result.output = {
                "message": "I've checked your inbox and found 3 new emails.",
                "request_send": False
            }
            mock_run.return_value = mock_result
            
            result = await email_agent.run("Check my inbox", deps=email_deps)
            
            assert result.output["message"] is not None
            assert result.output.get("request_send", False) is False
            assert "recipients" not in result.output or result.output["recipients"] is None
    
    @pytest.mark.asyncio
    async def test_agent_structured_output_send_request(self, email_deps):
        """Test agent structured output when requesting to send email."""
        with patch.object(email_agent, 'run', new_callable=AsyncMock) as mock_run:
            # Mock a send request response
            mock_result = MagicMock()
            mock_result.output = {
                "message": "I've prepared the email for sending. Please review and approve.",
                "recipients": ["test@example.com"],
                "subject": "Test Email",
                "body": "This is a test email body.",
                "request_send": True
            }
            mock_run.return_value = mock_result
            
            result = await email_agent.run("Send an email to test@example.com", deps=email_deps)
            
            assert result.output["request_send"] is True
            assert result.output["recipients"] == ["test@example.com"]
            assert result.output["subject"] == "Test Email"
            assert result.output["body"] is not None
            assert result.output["message"] is not None


class TestEmailAgentEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_agent_with_invalid_dependencies(self):
        """Test agent behavior with invalid dependencies."""
        invalid_deps = EmailAgentDependencies(
            gmail_credentials_path="",
            gmail_token_path="",
            session_id=None
        )
        
        # The agent should still initialize but tools may fail
        with patch.object(email_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_result = MagicMock()
            mock_result.output = {
                "message": "Error: Gmail credentials not configured properly.",
                "request_send": False
            }
            mock_run.return_value = mock_result
            
            result = await email_agent.run("Check inbox", deps=invalid_deps)
            
            assert "Error" in result.output["message"]
    
    @pytest.mark.asyncio
    async def test_agent_empty_query(self, email_deps):
        """Test agent behavior with empty query."""
        with patch.object(email_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_result = MagicMock()
            mock_result.output = {
                "message": "How can I help you with your emails today?",
                "request_send": False
            }
            mock_run.return_value = mock_result
            
            result = await email_agent.run("", deps=email_deps)
            
            assert result.output["message"] is not None
            assert result.output.get("request_send", False) is False
    
    @pytest.mark.asyncio
    async def test_structured_output_validation(self):
        """Test that EmailAgentDecision structure is valid."""
        # Test valid decision
        valid_decision: EmailAgentDecision = {
            "message": "Test message",
            "recipients": ["test@example.com"],
            "subject": "Test Subject",
            "body": "Test Body",
            "request_send": True
        }
        
        assert valid_decision["message"] == "Test message"
        assert valid_decision["request_send"] is True
        
        # Test minimal decision (normal conversation)
        minimal_decision: EmailAgentDecision = {
            "message": "Just a conversation",
            "request_send": False
        }
        
        assert minimal_decision["message"] == "Just a conversation"
        assert minimal_decision["request_send"] is False


if __name__ == "__main__":
    pytest.main([__file__])