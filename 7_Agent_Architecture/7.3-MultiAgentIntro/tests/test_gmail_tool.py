"""
Tests for Gmail Tool pure functions.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from googleapiclient.errors import HttpError

from agents.tools import create_email_draft_tool, list_email_drafts_tool
from agents.models import EmailDraft, EmailDraftResponse


class TestGmailTool:
    """Tests for Gmail pure functions."""
    
    @pytest.mark.asyncio
    async def test_create_draft_success(self):
        """Test successful draft creation."""
        with patch('agents.tools._get_gmail_service') as mock_service_func:
            # Mock Gmail service
            mock_service = MagicMock()
            mock_service_func.return_value = mock_service
            
            # Mock draft creation response
            mock_draft_response = {
                'id': 'draft_123',
                'message': {
                    'id': 'message_456',
                    'threadId': 'thread_789'
                }
            }
            
            mock_service.users().drafts().create().execute.return_value = mock_draft_response
            
            result = await create_email_draft_tool(
                credentials_path="fake_creds.json",
                token_path="fake_token.json",
                to=["test@example.com"],
                subject="Test Subject",
                body="Test Body"
            )
            
            assert result["success"] is True
            assert result["draft_id"] == 'draft_123'
            assert result["message_id"] == 'message_456'
            assert result["thread_id"] == 'thread_789'
    
    @pytest.mark.asyncio
    async def test_create_draft_http_error(self):
        """Test draft creation with HTTP error."""
        with patch('agents.tools._get_gmail_service') as mock_service_func:
            # Mock Gmail service that raises HttpError
            mock_service = MagicMock()
            mock_service_func.return_value = mock_service
            
            http_error = HttpError(resp=MagicMock(status=500), content=b"Server Error")
            mock_service.users().drafts().create().execute.side_effect = http_error
            
            with pytest.raises(Exception, match="Failed to create draft"):
                await create_email_draft_tool(
                    credentials_path="fake_creds.json",
                    token_path="fake_token.json",
                    to=["test@example.com"],
                    subject="Test Subject",
                    body="Test Body"
                )
    
    @pytest.mark.asyncio
    async def test_create_draft_empty_to_raises_error(self):
        """Test draft creation with empty to field raises error."""
        with pytest.raises(ValueError, match="At least one recipient is required"):
            await create_email_draft_tool(
                credentials_path="fake_creds.json",
                token_path="fake_token.json",
                to=[],
                subject="Test Subject",
                body="Test Body"
            )
    
    @pytest.mark.asyncio
    async def test_create_draft_empty_subject_raises_error(self):
        """Test draft creation with empty subject raises error."""
        with pytest.raises(ValueError, match="Subject is required"):
            await create_email_draft_tool(
                credentials_path="fake_creds.json",
                token_path="fake_token.json",
                to=["test@example.com"],
                subject="",
                body="Test Body"
            )
    
    @pytest.mark.asyncio
    async def test_create_draft_empty_body_raises_error(self):
        """Test draft creation with empty body raises error."""
        with pytest.raises(ValueError, match="Body is required"):
            await create_email_draft_tool(
                credentials_path="fake_creds.json",
                token_path="fake_token.json",
                to=["test@example.com"],
                subject="Test Subject",
                body=""
            )
    
    @pytest.mark.asyncio
    async def test_list_drafts_success(self):
        """Test successful draft listing."""
        with patch('agents.tools._get_gmail_service') as mock_service_func:
            # Mock Gmail service
            mock_service = MagicMock()
            mock_service_func.return_value = mock_service
            
            # Mock drafts list response
            mock_drafts_response = {
                'drafts': [
                    {'id': 'draft_1', 'message': {'id': 'msg_1'}},
                    {'id': 'draft_2', 'message': {'id': 'msg_2'}}
                ]
            }
            
            mock_service.users().drafts().list().execute.return_value = mock_drafts_response
            
            result = await list_email_drafts_tool(
                credentials_path="fake_creds.json",
                token_path="fake_token.json",
                max_results=10
            )
            
            assert result["success"] is True
            assert result["count"] == 2
            assert len(result["drafts"]) == 2
            assert result["drafts"][0]['id'] == 'draft_1'
            assert result["drafts"][1]['id'] == 'draft_2'


@pytest.mark.asyncio
async def test_create_email_draft_tool_convenience_function():
    """Test the create_email_draft_tool function directly."""
    with patch('agents.tools._get_gmail_service') as mock_service_func:
        mock_service = MagicMock()
        mock_service_func.return_value = mock_service
        
        # Mock successful draft creation
        mock_draft_response = {
            'id': 'draft_123',
            'message': {
                'id': 'message_456',
                'threadId': 'thread_789'
            }
        }
        mock_service.users().drafts().create().execute.return_value = mock_draft_response
        
        result = await create_email_draft_tool(
            credentials_path="fake_creds.json",
            token_path="fake_token.json",
            to=["test@example.com"],
            subject="Test",
            body="Test body"
        )
        
        assert result["success"] is True
        assert result["draft_id"] == 'draft_123'


class TestEmailDraft:
    """Tests for EmailDraft model validation."""
    
    def test_valid_email_draft(self):
        """Test valid email draft creation."""
        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body"
        )
        
        assert draft.to == ["test@example.com"]
        assert draft.subject == "Test Subject"
        assert draft.body == "Test Body"
        assert draft.cc is None
        assert draft.bcc is None
    
    def test_email_draft_with_cc_bcc(self):
        """Test email draft with CC and BCC."""
        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )
        
        assert draft.cc == ["cc@example.com"]
        assert draft.bcc == ["bcc@example.com"]
    
    def test_invalid_email_draft_empty_to(self):
        """Test invalid email draft with empty to field."""
        with pytest.raises(ValueError):
            EmailDraft(
                to=[],
                subject="Test Subject",
                body="Test Body"
            )
    
    def test_invalid_email_draft_empty_subject(self):
        """Test invalid email draft with empty subject."""
        with pytest.raises(ValueError):
            EmailDraft(
                to=["test@example.com"],
                subject="",
                body="Test Body"
            )
    
    def test_invalid_email_draft_empty_body(self):
        """Test invalid email draft with empty body."""
        with pytest.raises(ValueError):
            EmailDraft(
                to=["test@example.com"],
                subject="Test Subject",
                body=""
            )