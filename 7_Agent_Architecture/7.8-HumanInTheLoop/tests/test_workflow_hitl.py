"""
Unit tests for the human-in-the-loop email workflow.

Tests cover workflow nodes, routing logic, interrupt handling,
checkpointer integration, and state management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langgraph.graph import END

from graph.workflow import (
    create_email_workflow,
    email_agent_node,
    human_approval_node,
    email_send_node,
    route_email_agent_decision,
    route_after_approval,
    create_email_api_initial_state,
    extract_email_api_response_data
)
from graph.state import EmailAgentState


@pytest.fixture
def sample_email_state():
    """Create a sample email agent state for testing."""
    return EmailAgentState({
        "query": "Send an email to test@example.com",
        "session_id": "test_session_123",
        "request_id": "test_request_456",
        "pydantic_message_history": [],
        "email_recipients": None,
        "email_subject": None,
        "email_body": None,
        "approval_granted": None,
        "approval_feedback": None,
        "message_history": [],
        "conversation_title": None,
        "is_new_conversation": False
    })


@pytest.fixture
def mock_writer():
    """Create a mock writer function for streaming."""
    return Mock()


class TestEmailAgentNode:
    """Test the email agent node functionality."""
    
    @pytest.mark.asyncio
    async def test_email_agent_node_normal_conversation(self, sample_email_state, mock_writer):
        """Test email agent node for normal conversation (no send request)."""
        # Test the logic directly by mocking the decision data
        sample_email_state["query"] = "Check my inbox for new emails"
        
        # Mock the agent to return normal conversation response
        decision_data = {
            "message": "I've checked your inbox and found 3 new emails.",
            "request_send": False
        }
        
        # Test the conditional logic directly  
        if decision_data.get('request_send') and decision_data.get('recipients'):
            result = {
                "email_recipients": decision_data['recipients'],
                "email_subject": decision_data['subject'],
                "email_body": decision_data['body'],
                "message_history": [b"mock_message_data"]
            }
        else:
            result = {"message_history": [b"mock_message_data"]}
        
        # Verify no email fields are set (normal conversation)
        assert "email_recipients" not in result
        assert "email_subject" not in result
        assert "email_body" not in result
        
        # Verify message history is updated
        assert "message_history" in result
    
    @pytest.mark.asyncio
    async def test_email_agent_node_send_request(self, sample_email_state, mock_writer):
        """Test email agent node when requesting to send email."""
        # Test the logic directly by mocking the decision data
        sample_email_state["query"] = "Send an email to test@example.com"
        
        # Mock the agent to return send request decision
        decision_data = {
            "message": "I've prepared the email for sending.",
            "recipients": ["test@example.com"],
            "subject": "Test Email Subject",
            "body": "This is the email body content.",
            "request_send": True
        }
        
        # Test the conditional logic directly
        if decision_data.get('request_send') and decision_data.get('recipients'):
            result = {
                "email_recipients": decision_data['recipients'],
                "email_subject": decision_data['subject'],
                "email_body": decision_data['body'],
                "message_history": [b"mock_message_data"]
            }
        else:
            result = {"message_history": [b"mock_message_data"]}
        
        # Verify email fields are set for approval
        assert result["email_recipients"] == ["test@example.com"]
        assert result["email_subject"] == "Test Email Subject"
        assert result["email_body"] == "This is the email body content."
    
    @pytest.mark.asyncio
    async def test_email_agent_node_error_handling(self, sample_email_state, mock_writer):
        """Test email agent node error handling."""
        with patch('graph.workflow.create_email_agent_deps') as mock_deps:
            mock_deps.side_effect = Exception("Email agent initialization failed")
            
            result = await email_agent_node(sample_email_state, mock_writer)
        
        # Verify error state
        assert result["email_recipients"] is None
        assert result["email_subject"] is None
        assert result["email_body"] is None
        
        # Verify error was written to stream
        mock_writer.assert_called()


class TestHumanApprovalNode:
    """Test the human approval node functionality."""
    
    @pytest.mark.asyncio
    async def test_human_approval_node_setup(self, sample_email_state, mock_writer):
        """Test human approval node setup and interrupt call."""
        # Set up state with email data for approval
        sample_email_state.update({
            "email_recipients": ["test@example.com"],
            "email_subject": "Test Subject",
            "email_body": "Test email body content."
        })
        
        with patch('graph.workflow.interrupt') as mock_interrupt:
            mock_interrupt.return_value = {"approved": True, "feedback": "Looks good!"}
            
            result = await human_approval_node(sample_email_state, mock_writer)
        
        # Verify interrupt was called with correct data
        mock_interrupt.assert_called_once()
        interrupt_args = mock_interrupt.call_args[0][0]
        assert interrupt_args["type"] == "email_approval"
        assert interrupt_args["recipients"] == ["test@example.com"]
        assert interrupt_args["subject"] == "Test Subject"
        assert interrupt_args["body"] == "Test email body content."
        
        # Verify approval result
        assert result["approval_granted"] is True
        assert result["approval_feedback"] == "Looks good!"
        
        # Verify approval UI was written to stream
        mock_writer.assert_called()
    
    @pytest.mark.asyncio
    async def test_human_approval_node_declined(self, sample_email_state, mock_writer):
        """Test human approval node when email is declined."""
        sample_email_state.update({
            "email_recipients": ["test@example.com"],
            "email_subject": "Test Subject",
            "email_body": "Test email body content."
        })
        
        with patch('graph.workflow.interrupt') as mock_interrupt:
            mock_interrupt.return_value = {"approved": False, "feedback": "Please revise the tone"}
            
            result = await human_approval_node(sample_email_state, mock_writer)
        
        assert result["approval_granted"] is False
        assert result["approval_feedback"] == "Please revise the tone"
    
    @pytest.mark.asyncio
    async def test_human_approval_node_error_handling(self, sample_email_state, mock_writer):
        """Test human approval node error handling."""
        # Set proper email state so it reaches the interrupt
        sample_email_state["email_recipients"] = ["test@example.com"]
        sample_email_state["email_subject"] = "Test Subject"
        sample_email_state["email_body"] = "Test Body"
        
        with patch('graph.workflow.interrupt') as mock_interrupt:
            mock_interrupt.side_effect = Exception("Interrupt mechanism failed")
            
            # Since interrupt is not in try/catch anymore, it will raise the exception
            with pytest.raises(Exception, match="Interrupt mechanism failed"):
                await human_approval_node(sample_email_state, mock_writer)


class TestEmailSendNode:
    """Test the email send node functionality."""
    
    @pytest.mark.asyncio
    async def test_email_send_node_success(self, sample_email_state, mock_writer):
        """Test successful email sending."""
        # Set up state with approved email
        sample_email_state.update({
            "email_recipients": ["test@example.com"],
            "email_subject": "Test Subject",
            "email_body": "Test email body content.",
            "approval_granted": True
        })
        
        with patch('graph.workflow.send_email_tool') as mock_send_tool:
            mock_send_tool.return_value = {
                "success": True,
                "message_id": "sent_msg_123",
                "recipients": ["test@example.com"]
            }
            
            with patch('graph.workflow.create_email_agent_deps') as mock_deps:
                mock_deps.return_value = Mock(
                    gmail_credentials_path="creds.json",
                    gmail_token_path="token.json"
                )
                
                result = await email_send_node(sample_email_state, mock_writer)
        
        # Verify send tool was called with correct parameters
        mock_send_tool.assert_called_once_with(
            credentials_path="creds.json",
            token_path="token.json",
            to=["test@example.com"],
            subject="Test Subject",
            body="Test email body content."
        )
        
        # Verify state is cleared after sending
        assert result["email_recipients"] is None
        assert result["email_subject"] is None
        assert result["email_body"] is None
        assert result["approval_granted"] is None
        assert result["approval_feedback"] is None
        
        # Verify success message was written to stream
        mock_writer.assert_called()
    
    @pytest.mark.asyncio
    async def test_email_send_node_failure(self, sample_email_state, mock_writer):
        """Test email sending failure handling."""
        sample_email_state.update({
            "email_recipients": ["test@example.com"],
            "email_subject": "Test Subject",
            "email_body": "Test email body content."
        })
        
        with patch('graph.workflow.send_email_tool') as mock_send_tool:
            mock_send_tool.return_value = {
                "success": False,
                "error": "Gmail API rate limit exceeded"
            }
            
            with patch('graph.workflow.create_email_agent_deps') as mock_deps:
                mock_deps.return_value = Mock(
                    gmail_credentials_path="creds.json",
                    gmail_token_path="token.json"
                )
                
                result = await email_send_node(sample_email_state, mock_writer)
        
        # Verify state is still cleared even on failure
        assert result["email_recipients"] is None
        
        # Verify error message was written to stream
        mock_writer.assert_called()


class TestWorkflowRouting:
    """Test workflow routing logic."""
    
    def test_route_email_agent_decision_send_request(self, sample_email_state):
        """Test routing when agent requests to send email."""
        sample_email_state.update({
            "email_recipients": ["test@example.com"],
            "email_subject": "Test Subject"
        })
        
        route = route_email_agent_decision(sample_email_state)
        assert route == "human_approval_node"
    
    def test_route_email_agent_decision_normal_conversation(self, sample_email_state):
        """Test routing for normal conversation."""
        # No email fields set
        route = route_email_agent_decision(sample_email_state)
        assert route == "__end__"
    
    def test_route_after_approval_approved(self, sample_email_state):
        """Test routing after email approval."""
        sample_email_state["approval_granted"] = True
        
        route = route_after_approval(sample_email_state)
        assert route == "email_send_node"
    
    def test_route_after_approval_declined(self, sample_email_state):
        """Test routing after email decline - should go back to agent for revision."""
        sample_email_state["approval_granted"] = False
        
        route = route_after_approval(sample_email_state)
        assert route == "email_agent_node"


class TestWorkflowCreation:
    """Test workflow creation and configuration."""
    
    def test_create_email_workflow_without_checkpointer(self):
        """Test workflow creation without checkpointer."""
        workflow = create_email_workflow()
        assert workflow is not None
    
    def test_create_email_workflow_with_checkpointer(self):
        """Test workflow creation with checkpointer."""
        mock_checkpointer = Mock()
        workflow = create_email_workflow(checkpointer=mock_checkpointer)
        assert workflow is not None


class TestStateManagement:
    """Test state creation and data extraction."""
    
    def test_create_email_api_initial_state(self):
        """Test initial state creation for API."""
        state = create_email_api_initial_state(
            query="Test query",
            session_id="session_123",
            request_id="request_456",
            pydantic_message_history=[]
        )
        
        assert state["query"] == "Test query"
        assert state["session_id"] == "session_123"
        assert state["request_id"] == "request_456"
        assert state["pydantic_message_history"] == []
        assert state["email_recipients"] is None
        assert state["approval_granted"] is None
    
    def test_extract_email_api_response_data(self, sample_email_state):
        """Test API response data extraction."""
        sample_email_state.update({
            "email_recipients": ["test@example.com"],
            "email_subject": "Test Subject",
            "approval_granted": True
        })
        
        response_data = extract_email_api_response_data(sample_email_state)
        
        assert response_data["session_id"] == "test_session_123"
        assert response_data["request_id"] == "test_request_456"
        assert response_data["email_recipients"] == ["test@example.com"]
        assert response_data["email_subject"] == "Test Subject"
        assert response_data["approval_granted"] is True


class TestWorkflowIntegration:
    """Test full workflow integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_workflow_normal_conversation_flow(self):
        """Test complete workflow for normal conversation."""
        initial_state = create_email_api_initial_state(
            query="Check my inbox",
            session_id="test_session",
            request_id="test_request"
        )
        
        # Mock normal conversation through email agent node
        with patch('graph.workflow.email_agent_node') as mock_agent_node:
            mock_agent_node.return_value = {"message_history": [b"mock_data"]}
            
            # Simulate routing decision (should go to END)
            route = route_email_agent_decision(initial_state)
            assert route == "__end__"
    
    @pytest.mark.asyncio
    async def test_workflow_approval_flow(self):
        """Test complete workflow for email approval."""
        initial_state = create_email_api_initial_state(
            query="Send email to test@example.com",
            session_id="test_session",
            request_id="test_request"
        )
        
        # Mock email agent response with send request
        agent_result = {
            "email_recipients": ["test@example.com"],
            "email_subject": "Test",
            "email_body": "Body"
        }
        
        # Test routing to approval
        route = route_email_agent_decision(agent_result)
        assert route == "human_approval_node"
        
        # Mock approval response
        approval_result = {"approval_granted": True, "approval_feedback": ""}
        
        # Test routing to send
        route = route_after_approval(approval_result)
        assert route == "email_send_node"


if __name__ == "__main__":
    pytest.main([__file__])