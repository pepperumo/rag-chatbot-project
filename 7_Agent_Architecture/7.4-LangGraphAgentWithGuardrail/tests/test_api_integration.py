"""
Integration tests for the LangGraph API endpoint.

These tests validate the complete flow from API request through
LangGraph workflow to streaming response.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from typing import Dict, Any

from api.models import AgentRequest, FileAttachment
from api.streaming import StreamBridge, create_error_stream
from graph.workflow import create_api_initial_state, extract_api_response_data


class TestAPIIntegration:
    
    def test_agent_request_model(self):
        """Test AgentRequest model validation"""
        request_data = {
            "query": "What is AI safety?",
            "user_id": "test-user-123",
            "request_id": "req-456",
            "session_id": "session-789",
            "files": [
                {
                    "fileName": "test.pdf",
                    "content": "base64content",
                    "mimeType": "application/pdf"
                }
            ]
        }
        
        request = AgentRequest(**request_data)
        assert request.query == "What is AI safety?"
        assert request.user_id == "test-user-123"
        assert len(request.files) == 1
        assert request.files[0].fileName == "test.pdf"
    
    def test_file_attachment_model(self):
        """Test FileAttachment model validation"""
        file_data = {
            "fileName": "document.pdf",
            "content": "SGVsbG8gV29ybGQ=",  # "Hello World" in base64
            "mimeType": "application/pdf"
        }
        
        file_attachment = FileAttachment(**file_data)
        assert file_attachment.fileName == "document.pdf"
        assert file_attachment.content == "SGVsbG8gV29ybGQ="
        assert file_attachment.mimeType == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_stream_bridge_basic_flow(self):
        """Test StreamBridge basic functionality"""
        bridge = StreamBridge()
        
        # Write some data
        test_data = json.dumps({"text": "Hello"}).encode('utf-8') + b'\n'
        bridge.write(test_data)
        
        # Complete the stream
        bridge.complete({"final": "data"})
        
        # Collect streaming output
        chunks = []
        async for chunk in bridge.stream_http():
            chunks.append(chunk)
        
        assert len(chunks) >= 1
        # Check that we get our test data
        assert test_data in chunks
        
        # Check final summary is included
        final_chunk = chunks[-1]
        final_data = json.loads(final_chunk.decode('utf-8'))
        assert "final_summary" in final_data
        assert final_data["final_summary"]["final"] == "data"
    
    @pytest.mark.asyncio
    async def test_error_stream_bridge(self):
        """Test ErrorStreamBridge functionality"""
        error_bridge = create_error_stream("Test error", "session-123")
        
        chunks = []
        async for chunk in error_bridge.stream_error():
            chunks.append(chunk)
        
        assert len(chunks) == 2
        
        # Check first chunk has error text
        first_chunk = json.loads(chunks[0].decode('utf-8'))
        assert first_chunk["text"] == "Test error"
        
        # Check final chunk has complete error data
        final_chunk = json.loads(chunks[1].decode('utf-8'))
        assert final_chunk["error"] == "Test error"
        assert final_chunk["session_id"] == "session-123"
        assert final_chunk["complete"] is True
    
    def test_create_api_initial_state(self):
        """Test API initial state creation"""
        state = create_api_initial_state(
            query="Test query",
            session_id="session-123",
            request_id="req-789",
            pydantic_message_history=[]
        )
        
        # Check all required fields are present
        assert state["query"] == "Test query"
        assert state["session_id"] == "session-123"
        assert state["request_id"] == "req-789"
        assert "pydantic_message_history" in state
        
        # Check base state fields are inherited
        assert "google_drive_urls" in state
        assert "validation_result" in state
        assert "iteration_count" in state
    
    def test_extract_api_response_data(self):
        """Test API response data extraction"""
        state = create_api_initial_state(
            query="Test query",
            session_id="session-123",
            request_id="req-789",
            pydantic_message_history=[]
        )
        
        # Add some response data
        state.update({
            "final_output": "Test response",
            "google_drive_urls": ["https://docs.google.com/document/d/test123/"],
            "validation_result": "valid",
            "iteration_count": 1
        })
        
        api_data = extract_api_response_data(state)
        
        assert api_data["session_id"] == "session-123"
        assert api_data["request_id"] == "req-789"
        assert api_data["query"] == "Test query"
        assert api_data["response"] == "Test response"
        assert api_data["validation_passed"] is True
        assert api_data["iterations"] == 1
        assert len(api_data["citations"]) == 1
    


class TestAPIWorkflowMocks:
    """Test API workflow components with mocked dependencies"""
    
    @pytest.mark.asyncio
    async def test_unified_workflow_mock(self):
        """Test unified workflow with mocked components"""
        with patch('graph.workflow.create_agent_deps') as mock_create_deps:
            with patch('graph.workflow.primary_agent') as mock_primary_agent:
                
                # Setup mocks
                mock_deps = Mock()
                mock_create_deps.return_value = mock_deps
                
                # Mock the fallback (non-streaming) path for simplicity
                mock_result = Mock()
                mock_result.data = "Test AI response"
                mock_result.new_messages_json.return_value = b'{"messages": []}'
                mock_primary_agent.run_stream.side_effect = Exception("Triggering fallback")
                mock_primary_agent.run = AsyncMock(return_value=mock_result)
                
                # Import and test the node function
                from graph.workflow import primary_agent_node
                
                # Create test state
                state = create_api_initial_state(
                    query="What is AI safety?",
                    session_id="session-123",
                    request_id="req-789",
                    pydantic_message_history=[]
                )
                
                # Mock writer
                mock_writer = Mock()
                mock_writer.write = Mock()
                
                # Execute the node
                result = await primary_agent_node(state, writer=mock_writer)
                
                # Verify results
                assert result["primary_response"] == "Test AI response"
                assert len(result["message_history"]) == 1
                
                # Verify agent was called with correct parameters
                mock_primary_agent.run.assert_called_once()
                call_args = mock_primary_agent.run.call_args
                
                # Check that the first argument is the agent input (query)
                agent_input = call_args[0][0]
                assert agent_input == "What is AI safety?"


class TestAPIModels:
    """Test API model validation and serialization"""
    
    def test_agent_request_defaults(self):
        """Test AgentRequest with default values"""
        minimal_request = AgentRequest(
            query="Test query",
            user_id="user-123",
            request_id="req-456",
            session_id="session-789"
        )
        
        assert minimal_request.files is None  # Default value
    
    def test_agent_request_validation_errors(self):
        """Test AgentRequest validation with missing fields"""
        with pytest.raises(ValueError):
            AgentRequest(
                query="Test query",
                # Missing required fields
            )
    
    def test_file_attachment_validation(self):
        """Test FileAttachment validation"""
        # Valid file attachment
        valid_file = FileAttachment(
            fileName="test.pdf",
            content="base64content",
            mimeType="application/pdf"
        )
        assert valid_file.fileName == "test.pdf"
        
        # Test with missing fields
        with pytest.raises(ValueError):
            FileAttachment(
                fileName="test.pdf"
                # Missing content and mimeType
            )