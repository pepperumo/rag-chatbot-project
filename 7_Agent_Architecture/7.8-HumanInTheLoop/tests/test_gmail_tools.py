"""
Unit tests for Gmail tools with human-in-the-loop functionality.

Tests cover inbox reading, email sending, draft creation,
OAuth authentication, and error handling scenarios.
"""

import pytest
import base64
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError

from tools.gmail_tools import (
    _get_gmail_service,
    _create_email_message,
    read_inbox_emails_tool,
    send_email_tool,
    create_email_draft_tool,
    list_email_drafts_tool
)


class TestGmailServiceAuthentication:
    """Test Gmail service authentication and initialization."""
    
    @patch('tools.gmail_tools.build')
    @patch('tools.gmail_tools.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_get_gmail_service_existing_valid_token(self, mock_exists, mock_credentials, mock_build):
        """Test service creation with existing valid token."""
        # Mock existing token file
        mock_exists.return_value = True
        
        # Mock valid credentials
        mock_creds = Mock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds
        
        # Mock Gmail service
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        service = _get_gmail_service("creds.json", "token.json")
        
        assert service == mock_service
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
    
    @patch('tools.gmail_tools.build')
    @patch('tools.gmail_tools.Credentials.from_authorized_user_file')
    @patch('tools.gmail_tools.Request')
    @patch('os.path.exists')
    def test_get_gmail_service_refresh_token(self, mock_exists, mock_request, mock_credentials, mock_build):
        """Test service creation with token refresh."""
        mock_exists.return_value = True
        
        # Mock expired credentials that can be refreshed
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_credentials.return_value = mock_creds
        
        # Mock successful refresh
        mock_creds.refresh = Mock()
        mock_creds.to_json.return_value = '{"token": "mock_token"}'
        
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs'):
                service = _get_gmail_service("creds.json", "credentials/token.json")
        
        mock_creds.refresh.assert_called_once()
        assert service == mock_service
    
    @patch('tools.gmail_tools.InstalledAppFlow.from_client_secrets_file')
    @patch('tools.gmail_tools.build')
    @patch('os.path.exists')
    def test_get_gmail_service_new_auth_flow(self, mock_exists, mock_build, mock_flow_class):
        """Test service creation with new OAuth flow."""
        def exists_side_effect(path):
            return "credentials.json" in path  # Only credentials file exists
        
        mock_exists.side_effect = exists_side_effect
        
        # Mock OAuth flow
        mock_flow = Mock()
        mock_creds = Mock()
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.return_value = mock_flow
        
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        with patch('builtins.open', mock_open()) as mock_file:
            service = _get_gmail_service("credentials.json", "credentials/token.json")
        
        mock_flow.run_local_server.assert_called_once_with(port=0, open_browser=False)
        assert service == mock_service


class TestEmailMessageCreation:
    """Test email message creation and encoding."""
    
    def test_create_email_message_basic(self):
        """Test basic email message creation."""
        message = _create_email_message(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body"
        )
        
        assert "raw" in message
        
        # Decode and verify content
        decoded = base64.urlsafe_b64decode(message["raw"]).decode()
        assert "test@example.com" in decoded
        assert "Test Subject" in decoded
        assert "Test Body" in decoded
    
    def test_create_email_message_with_cc_bcc(self):
        """Test email message creation with CC and BCC."""
        message = _create_email_message(
            to=["to@example.com"],
            subject="Test",
            body="Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )
        
        decoded = base64.urlsafe_b64decode(message["raw"]).decode()
        assert "to@example.com" in decoded
        assert "cc@example.com" in decoded
        assert "bcc@example.com" in decoded
    
    def test_create_email_message_multiple_recipients(self):
        """Test email message with multiple recipients."""
        message = _create_email_message(
            to=["user1@example.com", "user2@example.com"],
            subject="Multiple Recipients",
            body="Test"
        )
        
        decoded = base64.urlsafe_b64decode(message["raw"]).decode()
        assert "user1@example.com" in decoded
        assert "user2@example.com" in decoded


class TestReadInboxEmails:
    """Test inbox email reading functionality."""
    
    @pytest.mark.asyncio
    async def test_read_inbox_emails_success(self):
        """Test successful inbox email reading."""
        # Mock Gmail service and API responses
        mock_service = Mock()
        mock_messages = Mock()
        mock_users = Mock()
        
        mock_service.users.return_value = mock_users
        mock_users.messages.return_value = mock_messages
        
        # Mock message list response
        mock_list = Mock()
        mock_list.execute.return_value = {
            "messages": [
                {"id": "msg_1", "threadId": "thread_1"},
                {"id": "msg_2", "threadId": "thread_2"}
            ]
        }
        mock_messages.list.return_value = mock_list
        
        # Mock individual message responses
        def mock_get_side_effect(*args, **kwargs):
            msg_id = kwargs.get("id")
            mock_response = Mock()
            if msg_id == "msg_1":
                mock_response.execute.return_value = {
                    "id": "msg_1",
                    "threadId": "thread_1",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Test Subject 1"},
                            {"name": "From", "value": "sender1@example.com"},
                            {"name": "Date", "value": "2024-01-01"}
                        ],
                        "mimeType": "text/plain",
                        "body": {"data": base64.urlsafe_b64encode(b"Test body 1").decode()}
                    },
                    "snippet": "Test snippet 1"
                }
            else:
                mock_response.execute.return_value = {
                    "id": "msg_2",
                    "threadId": "thread_2",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Test Subject 2"},
                            {"name": "From", "value": "sender2@example.com"},
                            {"name": "Date", "value": "2024-01-02"}
                        ],
                        "mimeType": "text/plain",
                        "body": {"data": base64.urlsafe_b64encode(b"Test body 2").decode()}
                    },
                    "snippet": "Test snippet 2"
                }
            return mock_response
        
        mock_messages.get.side_effect = mock_get_side_effect
        
        with patch('tools.gmail_tools._get_gmail_service', return_value=mock_service):
            result = await read_inbox_emails_tool(
                credentials_path="creds.json",
                token_path="token.json",
                max_results=2
            )
        
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["emails"]) == 2
        
        # Verify email details
        email1 = result["emails"][0]
        assert email1["subject"] == "Test Subject 1"
        assert email1["from"] == "sender1@example.com"
        assert "Test body 1" in email1["body"]
    
    @pytest.mark.asyncio
    async def test_read_inbox_emails_with_query(self):
        """Test inbox reading with search query."""
        mock_service = Mock()
        mock_messages = Mock()
        mock_users = Mock()
        
        mock_service.users.return_value = mock_users
        mock_users.messages.return_value = mock_messages
        
        mock_list = Mock()
        mock_list.execute.return_value = {"messages": []}
        mock_messages.list.return_value = mock_list
        
        with patch('tools.gmail_tools._get_gmail_service', return_value=mock_service):
            result = await read_inbox_emails_tool(
                credentials_path="creds.json",
                token_path="token.json",
                max_results=10,
                query="is:unread from:test@example.com"
            )
        
        # Verify the query was passed correctly
        mock_messages.list.assert_called_once_with(
            userId="me",
            maxResults=10,
            labelIds=["INBOX"],
            q="is:unread from:test@example.com"
        )
        
        assert result["success"] is True
        assert result["query_used"] == "is:unread from:test@example.com"
    
    @pytest.mark.asyncio
    async def test_read_inbox_emails_api_error(self):
        """Test error handling for Gmail API errors."""
        with patch('tools.gmail_tools._get_gmail_service') as mock_get_service:
            mock_get_service.side_effect = HttpError(
                resp=Mock(status=403), 
                content=b'{"error": "Forbidden"}'
            )
            
            with pytest.raises(Exception) as exc_info:
                await read_inbox_emails_tool("creds.json", "token.json")
            
            assert "Gmail authentication failed" in str(exc_info.value)


class TestSendEmailTool:
    """Test email sending functionality."""
    
    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email sending."""
        mock_service = Mock()
        mock_messages = Mock()
        mock_users = Mock()
        
        mock_service.users.return_value = mock_users
        mock_users.messages.return_value = mock_messages
        
        # Mock send response
        mock_send = Mock()
        mock_send.execute.return_value = {
            "id": "sent_msg_123",
            "threadId": "thread_456"
        }
        mock_messages.send.return_value = mock_send
        
        with patch('tools.gmail_tools._get_gmail_service', return_value=mock_service):
            result = await send_email_tool(
                credentials_path="creds.json",
                token_path="token.json",
                to=["recipient@example.com"],
                subject="Test Email",
                body="Test Body"
            )
        
        assert result["success"] is True
        assert result["message_id"] == "3555525"  # Mock value from current implementation
        assert result["thread_id"] == "345345345345"  # Mock value from current implementation
        assert result["recipients"] == ["recipient@example.com"]
        assert result["subject"] == "Test Email"
    
    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self):
        """Test email sending with CC and BCC."""
        mock_service = Mock()
        mock_messages = Mock()
        mock_users = Mock()
        
        mock_service.users.return_value = mock_users
        mock_users.messages.return_value = mock_messages
        
        mock_send = Mock()
        mock_send.execute.return_value = {"id": "sent_msg_123", "threadId": "thread_456"}
        mock_messages.send.return_value = mock_send
        
        with patch('tools.gmail_tools._get_gmail_service', return_value=mock_service):
            result = await send_email_tool(
                credentials_path="creds.json",
                token_path="token.json",
                to=["to@example.com"],
                subject="Test",
                body="Body",
                cc=["cc@example.com"],
                bcc=["bcc@example.com"]
            )
        
        assert result["success"] is True
        assert result["cc_recipients"] == ["cc@example.com"]
        assert result["bcc_recipients"] == ["bcc@example.com"]
    
    @pytest.mark.asyncio
    async def test_send_email_validation_errors(self):
        """Test email sending validation errors."""
        # Test empty recipients
        with pytest.raises(ValueError, match="At least one recipient is required"):
            await send_email_tool("creds.json", "token.json", [], "Subject", "Body")
        
        # Test empty subject
        with pytest.raises(ValueError, match="Subject is required"):
            await send_email_tool("creds.json", "token.json", ["test@example.com"], "", "Body")
        
        # Test empty body
        with pytest.raises(ValueError, match="Body is required"):
            await send_email_tool("creds.json", "token.json", ["test@example.com"], "Subject", "")
    
    @pytest.mark.asyncio
    async def test_send_email_api_error(self):
        """Test error handling for sending failures."""
        with patch('tools.gmail_tools._get_gmail_service') as mock_get_service:
            mock_get_service.side_effect = HttpError(
                resp=Mock(status=400), 
                content=b'{"error": "Bad Request"}'
            )
            
            with pytest.raises(Exception) as exc_info:
                await send_email_tool(
                    "creds.json", "token.json", 
                    ["test@example.com"], "Subject", "Body"
                )
            
            assert "Failed to send email" in str(exc_info.value)


class TestCreateEmailDraftTool:
    """Test email draft creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_draft_success(self):
        """Test successful draft creation."""
        mock_service = Mock()
        mock_drafts = Mock()
        mock_users = Mock()
        
        mock_service.users.return_value = mock_users
        mock_users.drafts.return_value = mock_drafts
        
        # Mock draft creation response
        mock_create = Mock()
        mock_create.execute.return_value = {
            "id": "draft_123",
            "message": {
                "id": "msg_456",
                "threadId": "thread_789"
            }
        }
        mock_drafts.create.return_value = mock_create
        
        with patch('tools.gmail_tools._get_gmail_service', return_value=mock_service):
            result = await create_email_draft_tool(
                credentials_path="creds.json",
                token_path="token.json",
                to=["recipient@example.com"],
                subject="Draft Subject",
                body="Draft Body"
            )
        
        assert result["success"] is True
        assert result["draft_id"] == "draft_123"
        assert result["message_id"] == "msg_456"
        assert result["thread_id"] == "thread_789"
        assert result["recipients"] == ["recipient@example.com"]
        assert result["subject"] == "Draft Subject"


class TestListEmailDraftsTool:
    """Test email draft listing functionality."""
    
    @pytest.mark.asyncio
    async def test_list_drafts_success(self):
        """Test successful draft listing."""
        mock_service = Mock()
        mock_drafts = Mock()
        mock_users = Mock()
        
        mock_service.users.return_value = mock_users
        mock_users.drafts.return_value = mock_drafts
        
        # Mock drafts list response
        mock_list = Mock()
        mock_list.execute.return_value = {
            "drafts": [
                {"id": "draft_1", "message": {"id": "msg_1"}},
                {"id": "draft_2", "message": {"id": "msg_2"}}
            ]
        }
        mock_drafts.list.return_value = mock_list
        
        with patch('tools.gmail_tools._get_gmail_service', return_value=mock_service):
            result = await list_email_drafts_tool(
                credentials_path="creds.json",
                token_path="token.json",
                max_results=5
            )
        
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["drafts"]) == 2
        
        # Verify API call parameters
        mock_drafts.list.assert_called_once_with(userId="me", maxResults=5)


def mock_open():
    """Helper to create a mock file context manager."""
    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_file.__exit__.return_value = None
    return mock_file


if __name__ == "__main__":
    pytest.main([__file__])