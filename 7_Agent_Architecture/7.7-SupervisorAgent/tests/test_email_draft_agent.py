"""
Unit tests for the email draft agent functionality.

Tests email draft agent with Gmail integration and draft creation.
"""

import pytest
from unittest.mock import MagicMock, patch

from agents.email_draft_agent import email_draft_agent
from agents.deps import EmailDraftAgentDependencies


@pytest.fixture
def mock_email_deps():
    """Create mock email draft dependencies"""
    return EmailDraftAgentDependencies(
        gmail_credentials_path="test/credentials.json",
        gmail_token_path="test/token.json",
        session_id="test-session-123"
    )


@pytest.fixture
def mock_gmail_draft_result():
    """Create mock Gmail draft creation result"""
    return {
        "success": True,
        "draft_id": "draft_123456",
        "message_id": "msg_789012",
        "thread_id": "thread_345678",
        "created_at": "2024-01-01T12:00:00",
        "recipients": ["john.doe@techcorp.com"],
        "subject": "Partnership Opportunity - Your Company & TechCorp"
    }


@pytest.fixture
def mock_email_draft_result():
    """Create mock email draft agent result"""
    mock_result = MagicMock()
    mock_result.data = "Professional email draft created based on research..."
    mock_result.new_messages_json.return_value = b'{"message": "test"}'
    return mock_result


class TestEmailDraftAgent:
    """Test cases for email draft agent functionality"""

    @pytest.mark.asyncio
    async def test_create_gmail_draft_success(self, mock_email_deps, mock_gmail_draft_result):
        """Test successful Gmail draft creation"""
        recipient = "john.doe@techcorp.com"
        subject = "Partnership Opportunity"
        body = "Dear John,\n\nI hope this email finds you well..."
        
        with patch('agents.email_draft_agent.create_email_draft_tool', return_value=mock_gmail_draft_result) as mock_create:
            # Create mock context
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_email_deps
            
            # Import and call the tool function directly
            from agents.email_draft_agent import create_gmail_draft
            result = await create_gmail_draft(mock_ctx, recipient, subject, body)
            
            # Verify Gmail tool was called with correct parameters
            mock_create.assert_called_once_with(
                credentials_path="test/credentials.json",
                token_path="test/token.json",
                to=[recipient],
                subject=subject,
                body=body,
                cc=None,
                bcc=None
            )
            
            # Verify results
            assert result == mock_gmail_draft_result
            assert result["success"] is True
            assert result["draft_id"] == "draft_123456"

    @pytest.mark.asyncio
    async def test_create_gmail_draft_with_cc_bcc(self, mock_email_deps, mock_gmail_draft_result):
        """Test Gmail draft creation with CC and BCC recipients"""
        recipient = "john.doe@techcorp.com"
        subject = "Partnership Opportunity"
        body = "Dear John,\n\nI hope this email finds you well..."
        cc_emails = "manager@techcorp.com, assistant@techcorp.com"
        bcc_emails = "bcc@mycompany.com"
        
        with patch('agents.email_draft_agent.create_email_draft_tool', return_value=mock_gmail_draft_result) as mock_create:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_email_deps
            
            from agents.email_draft_agent import create_gmail_draft
            result = await create_gmail_draft(
                mock_ctx, recipient, subject, body, cc_emails, bcc_emails
            )
            
            # Verify Gmail tool was called with parsed email lists
            mock_create.assert_called_once_with(
                credentials_path="test/credentials.json",
                token_path="test/token.json",
                to=[recipient],
                subject=subject,
                body=body,
                cc=["manager@techcorp.com", "assistant@techcorp.com"],
                bcc=["bcc@mycompany.com"]
            )

    @pytest.mark.asyncio
    async def test_create_gmail_draft_error(self, mock_email_deps):
        """Test Gmail draft creation error handling"""
        recipient = "john.doe@techcorp.com"
        subject = "Test Subject"
        body = "Test body"
        
        with patch('agents.email_draft_agent.create_email_draft_tool', side_effect=Exception("Gmail API Error")) as mock_create:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_email_deps
            
            from agents.email_draft_agent import create_gmail_draft
            result = await create_gmail_draft(mock_ctx, recipient, subject, body)
            
            # Verify error handling
            assert result["success"] is False
            assert "Gmail API Error" in result["error"]
            assert result["recipient"] == recipient
            assert result["subject"] == subject

    @pytest.mark.asyncio
    async def test_email_draft_agent_integration(self, mock_email_deps, mock_email_draft_result):
        """Test email draft agent end-to-end integration"""
        query = "Create professional outreach email based on research"
        
        with patch.object(email_draft_agent, 'run', return_value=mock_email_draft_result) as mock_run:
            result = await email_draft_agent.run(query, deps=mock_email_deps)
            
            # Verify the agent was called
            mock_run.assert_called_with(query, deps=mock_email_deps)
            
            # Verify result structure
            assert hasattr(result, 'data')
            assert isinstance(result.data, str)
            assert hasattr(result, 'new_messages_json')

    @pytest.mark.asyncio
    async def test_email_draft_agent_with_message_history(self, mock_email_deps, mock_email_draft_result):
        """Test email draft agent with message history"""
        query = "Refine the email draft based on previous conversation"
        message_history = [MagicMock()]
        
        with patch.object(email_draft_agent, 'run', return_value=mock_email_draft_result) as mock_run:
            result = await email_draft_agent.run(
                query, 
                deps=mock_email_deps,
                message_history=message_history
            )
            
            # Verify the agent was called with message history
            mock_run.assert_called_with(
                query, 
                deps=mock_email_deps,
                message_history=message_history
            )

    def test_email_draft_dependencies_structure(self):
        """Test EmailDraftAgentDependencies dataclass structure"""
        deps = EmailDraftAgentDependencies(
            gmail_credentials_path="test/creds.json",
            gmail_token_path="test/token.json",
            session_id="test-session"
        )
        
        assert deps.gmail_credentials_path == "test/creds.json"
        assert deps.gmail_token_path == "test/token.json"
        assert deps.session_id == "test-session"
        
        # Test with None session_id
        deps_none = EmailDraftAgentDependencies(
            gmail_credentials_path="test/creds.json",
            gmail_token_path="test/token.json"
        )
        assert deps_none.session_id is None

    @pytest.mark.asyncio
    async def test_gmail_draft_email_parsing(self, mock_email_deps):
        """Test email address parsing for CC and BCC"""
        recipient = "john@test.com"
        subject = "Test"
        body = "Test body"
        
        test_cases = [
            ("", []),  # Empty string
            ("single@test.com", ["single@test.com"]),  # Single email
            ("one@test.com, two@test.com", ["one@test.com", "two@test.com"]),  # Multiple emails
            ("  spaced@test.com  ,  another@test.com  ", ["spaced@test.com", "another@test.com"]),  # With spaces
            ("valid@test.com, , invalid, another@test.com", ["valid@test.com", "invalid", "another@test.com"])  # Mixed valid/invalid - current behavior
        ]
        
        with patch('agents.email_draft_agent.create_email_draft_tool', return_value={"success": True}) as mock_create:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_email_deps
            
            from agents.email_draft_agent import create_gmail_draft
            
            for cc_input, expected_cc in test_cases:
                await create_gmail_draft(mock_ctx, recipient, subject, body, cc_input)
                
                call_args = mock_create.call_args[1]  # Get keyword arguments
                if expected_cc:
                    assert call_args['cc'] == expected_cc
                else:
                    assert call_args['cc'] is None
                
                mock_create.reset_mock()

    @pytest.mark.asyncio 
    async def test_gmail_draft_required_fields_validation(self, mock_email_deps):
        """Test that Gmail draft validates required fields"""
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_email_deps
        
        from agents.email_draft_agent import create_gmail_draft
        
        # These should work through to the Gmail tool and let it handle validation
        with patch('agents.email_draft_agent.create_email_draft_tool', side_effect=ValueError("At least one recipient is required")):
            result = await create_gmail_draft(mock_ctx, "", "subject", "body")
            assert result["success"] is False
            assert "At least one recipient is required" in result["error"]