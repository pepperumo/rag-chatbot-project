"""
Unit tests for the sequential workflow functionality.

Tests the complete LangGraph workflow with sequential agent execution.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from graph.workflow import (
    workflow, 
    create_api_initial_state,
    extract_api_response_data,
    guardrail_node,
    research_node,
    enrichment_node,
    email_draft_node,
    fallback_node,
    route_after_guardrail
)


@pytest.fixture
def mock_state():
    """Create mock sequential agent state"""
    return {
        "query": "Research John Doe at TechCorp and draft an outreach email",
        "session_id": "test-session-123",
        "request_id": "test-request-456",
        "pydantic_message_history": []
    }


@pytest.fixture
def mock_research_state():
    """Create mock state after research step"""
    return {
        "query": "Research John Doe at TechCorp and draft an outreach email",
        "session_id": "test-session-123",
        "request_id": "test-request-456",
        "is_research_request": True,
        "routing_reason": "This is a research and outreach request",
        "research_summary": "John Doe is a Senior Engineer at TechCorp...",
        "research_sources": [{"url": "https://linkedin.com/in/johndoe", "title": "John Doe LinkedIn"}],
        "pydantic_message_history": []
    }


@pytest.fixture
def mock_writer():
    """Create mock writer function"""
    return MagicMock()


class TestSequentialWorkflow:
    """Test cases for sequential workflow functionality"""

    @pytest.mark.asyncio
    async def test_guardrail_node_research_detection(self, mock_state, mock_writer):
        """Test guardrail node detecting research requests"""
        mock_result = MagicMock()
        mock_result.data.is_research_request = True
        mock_result.data.reasoning = "This is a research request"
        
        with patch('agents.guardrail_agent.guardrail_agent.run', return_value=mock_result):
            result = await guardrail_node(mock_state, mock_writer)
            
            # Verify routing decision
            assert result["is_research_request"] is True
            assert result["routing_reason"] == "This is a research request"
            
            # Verify writer was called with appropriate message
            mock_writer.assert_called()
            call_args = mock_writer.call_args[0][0]
            assert "🔬 Detected research/outreach request" in call_args

    @pytest.mark.asyncio
    async def test_guardrail_node_conversation_detection(self, mock_writer):
        """Test guardrail node detecting conversation requests"""
        conversation_state = {
            "query": "How are you today?",
            "session_id": "test-session",
            "pydantic_message_history": []
        }
        
        mock_result = MagicMock()
        mock_result.data.is_research_request = False
        mock_result.data.reasoning = "This is a conversation request"
        
        with patch('agents.guardrail_agent.guardrail_agent.run', return_value=mock_result):
            result = await guardrail_node(conversation_state, mock_writer)
            
            # Verify routing decision
            assert result["is_research_request"] is False
            assert result["routing_reason"] == "This is a conversation request"
            
            # Verify writer was called with conversation message
            mock_writer.assert_called()
            call_args = mock_writer.call_args[0][0]
            assert "💬 Routing to conversation mode" in call_args

    @pytest.mark.asyncio
    async def test_guardrail_node_error_handling(self, mock_state, mock_writer):
        """Test guardrail node error handling"""
        with patch('agents.guardrail_agent.guardrail_agent.run', side_effect=Exception("Guardrail error")):
            result = await guardrail_node(mock_state, mock_writer)
            
            # Verify error fallback
            assert result["is_research_request"] is False
            assert "Guardrail error" in result["routing_reason"]
            
            # Verify error message was written
            mock_writer.assert_called()
            call_args = mock_writer.call_args[0][0]
            assert "⚠️ Guardrail failed" in call_args

    @pytest.mark.asyncio
    async def test_research_node_success(self, mock_state, mock_writer):
        """Test research node successful execution"""
        mock_run = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = "Research summary about John Doe..."
        mock_run.result = mock_result
        
        with patch('agents.research_agent.research_agent.iter') as mock_iter:
            mock_iter.return_value.__aenter__.return_value = mock_run
            mock_run.__aiter__.return_value = []  # No streaming events
            
            result = await research_node(mock_state, mock_writer)
            
            # Verify result structure
            assert "research_summary" in result
            assert "research_sources" in result
            assert result["agent_type"] == "research"
            assert "message_history" not in result  # Should not update history

    @pytest.mark.asyncio
    async def test_research_node_streaming(self, mock_state, mock_writer):
        """Test research node with streaming"""
        # Simplified streaming test - just verify the structure works
        mock_run = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = "Research summary with streaming..."
        mock_run.result = mock_result
        
        with patch('agents.research_agent.research_agent.iter') as mock_iter:
            mock_iter.return_value.__aenter__.return_value = mock_run
            mock_run.__aiter__.return_value = []  # No complex streaming events for now
            
            result = await research_node(mock_state, mock_writer)
            
            # Verify basic structure
            assert "research_summary" in result
            assert result["agent_type"] == "research"
            assert "streaming_success" in result

    @pytest.mark.asyncio
    async def test_enrichment_node_with_previous_research(self, mock_research_state, mock_writer):
        """Test enrichment node using previous research data"""
        mock_run = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = "Additional enrichment data about John Doe..."
        mock_run.result = mock_result
        
        with patch('agents.enrichment_agent.enrichment_agent.iter') as mock_iter:
            mock_iter.return_value.__aenter__.return_value = mock_run
            mock_run.__aiter__.return_value = []  # No streaming events
            
            result = await enrichment_node(mock_research_state, mock_writer)
            
            # Verify result structure
            assert "enrichment_summary" in result
            assert "enriched_data" in result
            assert result["agent_type"] == "enrichment"
            assert "message_history" not in result  # Should not update history

    @pytest.mark.asyncio
    async def test_email_draft_node_final_agent(self, mock_writer):
        """Test email draft node as final agent updating history"""
        enriched_state = {
            "query": "Research John Doe and draft email",
            "session_id": "test-session",
            "research_summary": "John Doe research...",
            "enrichment_summary": "Additional data...",
            "pydantic_message_history": []
        }
        
        mock_run = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = "Professional email draft created..."
        mock_result.new_messages_json.return_value = b'{"message": "test"}'
        mock_run.result = mock_result
        
        with patch('agents.email_draft_agent.email_draft_agent.iter') as mock_iter:
            mock_iter.return_value.__aenter__.return_value = mock_run
            mock_run.__aiter__.return_value = []  # No streaming events
            
            result = await email_draft_node(enriched_state, mock_writer)
            
            # Verify final agent behavior
            assert "final_response" in result
            assert result["email_draft_created"] is True
            assert result["agent_type"] == "email_draft"
            assert "message_history" in result  # Final agent updates history
            assert len(result["message_history"]) == 1

    @pytest.mark.asyncio
    async def test_fallback_node_conversation(self, mock_writer):
        """Test fallback node for conversation handling"""
        conversation_state = {
            "query": "How are you?",
            "session_id": "test-session",
            "pydantic_message_history": []
        }
        
        mock_run = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = "I'm doing well, thank you for asking..."
        mock_result.new_messages_json.return_value = b'{"message": "conversation"}'
        mock_run.result = mock_result
        
        with patch('agents.fallback_agent.fallback_agent.iter') as mock_iter:
            mock_iter.return_value.__aenter__.return_value = mock_run
            mock_run.__aiter__.return_value = []  # No streaming events
            
            result = await fallback_node(conversation_state, mock_writer)
            
            # Verify fallback behavior
            assert "final_response" in result
            assert result["agent_type"] == "fallback"
            assert "message_history" in result  # Final agent updates history

    def test_route_after_guardrail_research(self):
        """Test routing after guardrail for research requests"""
        research_state = {"is_research_request": True}
        route = route_after_guardrail(research_state)
        assert route == "research_node"

    def test_route_after_guardrail_conversation(self):
        """Test routing after guardrail for conversation requests"""
        conversation_state = {"is_research_request": False}
        route = route_after_guardrail(conversation_state)
        assert route == "fallback_node"

    def test_route_after_guardrail_missing_key(self):
        """Test routing after guardrail with missing key"""
        empty_state = {}
        route = route_after_guardrail(empty_state)
        assert route == "fallback_node"  # Should default to fallback

    def test_create_api_initial_state(self):
        """Test API initial state creation"""
        state = create_api_initial_state(
            query="Test query",
            session_id="test-session",
            request_id="test-request"
        )
        
        # Verify all required fields are present
        assert state["query"] == "Test query"
        assert state["session_id"] == "test-session"
        assert state["request_id"] == "test-request"
        assert state["is_research_request"] is False
        assert state["routing_reason"] == ""
        assert state["research_summary"] == ""
        assert state["research_sources"] == []
        assert state["enrichment_summary"] == ""
        assert state["enriched_data"] == {}
        assert state["email_draft_created"] is False
        assert state["draft_id"] is None
        assert state["final_response"] == ""
        assert state["agent_type"] == ""
        assert state["pydantic_message_history"] == []
        assert state["message_history"] == []

    def test_extract_api_response_data(self):
        """Test API response data extraction"""
        state = {
            "session_id": "test-session",
            "request_id": "test-request",
            "query": "Test query",
            "final_response": "Test response",
            "agent_type": "research",
            "is_research_request": True,
            "routing_reason": "Research request",
            "research_summary": "Research results",
            "enrichment_summary": "Enrichment results",
            "email_draft_created": False
        }
        
        response_data = extract_api_response_data(state)
        
        # Verify extracted data
        assert response_data["session_id"] == "test-session"
        assert response_data["request_id"] == "test-request"
        assert response_data["query"] == "Test query"
        assert response_data["response"] == "Test response"
        assert response_data["agent_type"] == "research"
        assert response_data["is_research_request"] is True
        assert response_data["routing_reason"] == "Research request"
        assert response_data["research_summary"] == "Research results"
        assert response_data["enrichment_summary"] == "Enrichment results"
        assert response_data["email_draft_created"] is False

    def test_workflow_compilation(self):
        """Test that the workflow compiles successfully"""
        # This should not raise any exceptions
        assert workflow is not None
        
        # Verify workflow has the expected structure
        # Note: Specific LangGraph internals testing would require more complex mocking