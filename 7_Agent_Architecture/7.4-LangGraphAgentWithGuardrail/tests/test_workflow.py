import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from typing import List

from graph.workflow import (
    primary_agent_node,
    guardrail_agent_node,
    route_after_validation,
    workflow,
    create_api_initial_state
)
from graph.state import AgentState, should_continue_iteration


class TestWorkflow:
    
    @pytest.fixture
    def mock_state(self):
        """Create mock state for testing"""
        return {
            "query": "What is AI safety?",
            "primary_response": "AI safety is important. Source: https://docs.google.com/document/d/test123/",
            "google_drive_urls": [],
            "file_ids": [],
            "validation_result": None,
            "feedback": None,
            "iteration_count": 0,
            "final_output": "",
            "message_history": []
        }

    @pytest.fixture
    def mock_writer(self):
        """Create mock writer for testing"""
        written_data = []
        
        def write(data):
            written_data.append(data)
        
        # Return the actual writer function, not a Mock
        write.written_data = written_data
        return write

    @pytest.mark.asyncio
    async def test_primary_agent_node_success(self, mock_state, mock_writer):
        """Test primary agent node fallback to non-streaming mode"""
        with patch('graph.workflow.create_agent_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.primary_agent') as mock_agent:
                # Mock run_stream to raise an exception, triggering fallback
                mock_agent.run_stream.side_effect = Exception("Streaming failed")
                
                # Mock the fallback run method
                mock_result = Mock()
                mock_result.data = "AI safety is important."
                mock_result.new_messages_json.return_value = b'{"messages": []}'
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                result = await primary_agent_node(mock_state, writer=mock_writer)
                
                assert result["primary_response"] == "AI safety is important."
                assert len(mock_writer.written_data) >= 1  # At least one text chunk
                
                # Verify the writer was called with the response
                assert any("AI safety is important." in str(data) for data in mock_writer.written_data)

    @pytest.mark.asyncio
    async def test_primary_agent_node_with_feedback(self, mock_state, mock_writer):
        """Test primary agent node with feedback"""
        mock_state["feedback"] = "Please include proper citations"
        
        with patch('graph.workflow.create_agent_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.primary_agent') as mock_agent:
                mock_result = Mock()
                mock_result.new_messages_json.return_value = b'{"messages": []}'
                
                # Mock the streaming context manager
                mock_stream = AsyncMock()
                mock_stream.stream_text.return_value = AsyncMock()
                mock_stream.stream_text.return_value.__aiter__.return_value = iter(["Corrected ", "response ", "with citations."])
                mock_stream.new_messages_json.return_value = b'{"messages": []}'
                
                mock_agent.run_stream.return_value.__aenter__.return_value = mock_stream
                
                result = await primary_agent_node(mock_state, writer=mock_writer)
                
                # Verify feedback was passed to create_agent_deps
                mock_create_deps.assert_called_once_with(feedback="Please include proper citations")

    @pytest.mark.asyncio
    async def test_primary_agent_node_error(self, mock_state, mock_writer):
        """Test primary agent node error handling"""
        with patch('graph.workflow.create_agent_deps') as mock_create_deps:
            mock_create_deps.side_effect = Exception("Connection failed")
            
            result = await primary_agent_node(mock_state, writer=mock_writer)
            
            assert "Error in primary agent: Connection failed" in result["primary_response"]
            assert result["message_history"] == []

    @pytest.mark.asyncio
    async def test_guardrail_agent_node_valid(self, mock_state, mock_writer):
        """Test guardrail agent node with valid citations"""
        with patch('graph.workflow.create_agent_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.guardrail_agent') as mock_agent:
                mock_result = Mock()
                mock_result.data = "VALID - All citations are accurate and relevant"
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                with patch('graph.workflow.extract_google_drive_urls') as mock_extract:
                    mock_extract.return_value = ["https://docs.google.com/document/d/test123/"]
                    
                    with patch('graph.workflow.extract_file_ids_from_urls') as mock_extract_ids:
                        mock_extract_ids.return_value = ["test123"]
                        
                        result = await guardrail_agent_node(mock_state, writer=mock_writer)
                        
                        assert result["validation_result"] == "valid"
                        assert result["google_drive_urls"] == ["https://docs.google.com/document/d/test123/"]
                        assert result["file_ids"] == ["test123"]
                        assert result["final_output"] == mock_state["primary_response"]

    @pytest.mark.asyncio
    async def test_guardrail_agent_node_invalid(self, mock_state, mock_writer):
        """Test guardrail agent node with invalid citations"""
        with patch('graph.workflow.create_agent_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.guardrail_agent') as mock_agent:
                mock_result = Mock()
                mock_result.data = "INVALID - Document not found in knowledge base"
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                with patch('graph.workflow.extract_google_drive_urls') as mock_extract:
                    mock_extract.return_value = ["https://docs.google.com/document/d/fake123/"]
                    
                    with patch('graph.workflow.extract_file_ids_from_urls') as mock_extract_ids:
                        mock_extract_ids.return_value = ["fake123"]
                        
                        result = await guardrail_agent_node(mock_state, writer=mock_writer)
                        
                        assert result["validation_result"] == "invalid"
                        assert result["feedback"] == "INVALID - Document not found in knowledge base"
                        assert result["iteration_count"] == 1

    @pytest.mark.asyncio
    async def test_guardrail_agent_node_error(self, mock_state, mock_writer):
        """Test guardrail agent node error handling"""
        with patch('graph.workflow.create_agent_deps') as mock_create_deps:
            mock_create_deps.side_effect = Exception("Validation failed")
            
            result = await guardrail_agent_node(mock_state, writer=mock_writer)
            
            assert result["validation_result"] == "valid"  # Falls back to valid on error
            assert "guardrail_error" in result  # Error is stored in guardrail_error field

    def test_route_after_validation_continue(self):
        """Test routing when validation fails and should continue"""
        state = {
            "validation_result": "invalid",
            "iteration_count": 1,
            "feedback": "Please fix citations"
        }
        
        result = route_after_validation(state)
        
        assert result == "primary_agent_node"

    def test_route_after_validation_end_valid(self):
        """Test routing when validation passes"""
        state = {
            "validation_result": "valid",
            "iteration_count": 1
        }
        
        result = route_after_validation(state)
        
        assert result == "end"

    def test_route_after_validation_end_max_iterations(self):
        """Test routing when max iterations reached"""
        state = {
            "validation_result": "invalid",
            "iteration_count": 3,
            "feedback": "Still invalid"
        }
        
        result = route_after_validation(state)
        
        assert result == "fallback_node"  # Goes to fallback when max iterations reached

class TestStateManagement:
    

    def test_should_continue_iteration_under_limit(self):
        """Test should continue when under iteration limit"""
        from graph.state import should_continue_iteration
        
        state = {
            "iteration_count": 1,
            "validation_result": "invalid"
        }
        
        assert should_continue_iteration(state) is True

    def test_should_continue_iteration_at_limit(self):
        """Test should not continue when at iteration limit"""
        from graph.state import should_continue_iteration
        
        state = {
            "iteration_count": 3,
            "validation_result": "invalid"
        }
        
        assert should_continue_iteration(state) is False

    def test_should_continue_iteration_valid(self):
        """Test should not continue when validation passes"""
        from graph.state import should_continue_iteration
        
        state = {
            "iteration_count": 1,
            "validation_result": "valid"
        }
        
        assert should_continue_iteration(state) is False

