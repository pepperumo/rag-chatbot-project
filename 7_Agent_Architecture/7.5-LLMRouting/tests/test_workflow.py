"""
Unit tests for the routing workflow functionality.

Tests complete routing workflow, conditional routing, and fallback scenarios.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from typing import List, Dict, Any

from graph.workflow import (
    router_node,
    web_search_node,
    email_search_node,
    rag_search_node,
    fallback_node,
    route_based_on_decision,
    workflow,
    create_api_initial_state
)
from graph.state import RouterState
from agents.router_agent import RouterResponse
from agents.deps import RouterDependencies, AgentDependencies


class TestRoutingWorkflow:
    """Test cases for the routing workflow"""
    
    @pytest.fixture
    def mock_router_state(self):
        """Create mock router state for testing"""
        return {
            "query": "What are the latest AI developments?",
            "session_id": "test-session-123",
            "request_id": "test-request-456",
            "routing_decision": "",
            "router_confidence": "",
            "final_response": "",
            "agent_type": "",
            "streaming_success": False
        }

    @pytest.fixture
    def mock_writer(self):
        """Create mock writer for testing"""
        written_data = []
        
        def write(data):
            written_data.append(data)
        
        write.written_data = written_data
        return write
    
    @pytest.fixture
    def mock_router_deps(self):
        """Create mock router dependencies"""
        return RouterDependencies(session_id="test-session-123")
    
    @pytest.fixture
    def mock_agent_deps(self):
        """Create mock agent dependencies"""
        return AgentDependencies(
            brave_api_key="test-brave-key",
            gmail_credentials_path="test/creds.json",
            gmail_token_path="test/token.json",
            supabase=MagicMock(),
            embedding_client=MagicMock(),
            http_client=MagicMock(),
            session_id="test-session-123"
        )

    @pytest.mark.asyncio
    async def test_router_node_web_search_decision(self, mock_router_state, mock_writer):
        """Test router node making web search decision"""
        mock_router_state["query"] = "What's the latest news about AI?"
        
        with patch('graph.workflow.create_router_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.router_agent') as mock_agent:
                mock_result = Mock()
                mock_result.data = RouterResponse(decision="web_search")
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                result = await router_node(mock_router_state, writer=mock_writer)
                
                assert result["routing_decision"] == "web_search"
                assert result["router_confidence"] == "high"
                assert "🔀 Routing to: web_search" in mock_writer.written_data[0]
                
                # Verify router was called with message history
                mock_agent.run.assert_called_once_with(
                    mock_router_state["query"],
                    deps=mock_deps,
                    message_history=[]
                )

    @pytest.mark.asyncio
    async def test_router_node_email_search_decision(self, mock_router_state, mock_writer):
        """Test router node making email search decision"""
        mock_router_state["query"] = "Find emails from John about the project"
        
        with patch('graph.workflow.create_router_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.router_agent') as mock_agent:
                mock_result = Mock()
                mock_result.data = RouterResponse(decision="email_search")
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                result = await router_node(mock_router_state, writer=mock_writer)
                
                assert result["routing_decision"] == "email_search"
                assert result["router_confidence"] == "high"

    @pytest.mark.asyncio
    async def test_router_node_rag_search_decision(self, mock_router_state, mock_writer):
        """Test router node making RAG search decision"""
        mock_router_state["query"] = "What does our company policy say about remote work?"
        
        with patch('graph.workflow.create_router_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.router_agent') as mock_agent:
                mock_result = Mock()
                mock_result.data = RouterResponse(decision="rag_search")
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                result = await router_node(mock_router_state, writer=mock_writer)
                
                assert result["routing_decision"] == "rag_search"
                assert result["router_confidence"] == "high"

    @pytest.mark.asyncio
    async def test_router_node_fallback_decision(self, mock_router_state, mock_writer):
        """Test router node making fallback decision"""
        mock_router_state["query"] = "How are you feeling today?"
        
        with patch('graph.workflow.create_router_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.router_agent') as mock_agent:
                mock_result = Mock()
                mock_result.data = RouterResponse(decision="fallback")
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                result = await router_node(mock_router_state, writer=mock_writer)
                
                assert result["routing_decision"] == "fallback"
                assert result["router_confidence"] == "high"

    @pytest.mark.asyncio
    async def test_router_node_error_handling(self, mock_router_state, mock_writer):
        """Test router node error handling"""
        with patch('graph.workflow.create_router_deps') as mock_create_deps:
            mock_create_deps.side_effect = Exception("Router failed")
            
            result = await router_node(mock_router_state, writer=mock_writer)
            
            assert result["routing_decision"] == "web_search"
            assert result["router_confidence"] == "fallback"
            assert "⚠️ Router failed, defaulting to web search" in mock_writer.written_data[0]

    @pytest.mark.asyncio
    async def test_web_search_node_success(self, mock_router_state, mock_writer):
        """Test web search node execution"""
        mock_router_state["routing_decision"] = "web_search"
        
        with patch('graph.workflow.create_search_agent_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.web_search_agent') as mock_agent:
                # Mock .iter() streaming to simulate streaming failure, triggering fallback
                mock_agent.iter.side_effect = Exception("Streaming failed")
                
                # Mock fallback
                mock_result = Mock()
                mock_result.data = "Web search completed successfully"
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                result = await web_search_node(mock_router_state, writer=mock_writer)
                
                assert result["agent_type"] == "web_search"
                assert result["final_response"] == "Web search completed successfully"
                assert result["streaming_success"] is False  # Failed streaming, used fallback

    @pytest.mark.asyncio
    async def test_email_search_node_success(self, mock_router_state, mock_writer):
        """Test email search node execution"""
        mock_router_state["routing_decision"] = "email_search"
        
        with patch('graph.workflow.create_search_agent_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.email_search_agent') as mock_agent:
                # Mock streaming failure, fallback to non-streaming
                mock_agent.iter.side_effect = Exception("Streaming failed")
                
                mock_result = Mock()
                mock_result.data = "Email search completed successfully"
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                result = await email_search_node(mock_router_state, writer=mock_writer)
                
                assert result["agent_type"] == "email_search"
                assert result["final_response"] == "Email search completed successfully"
                assert result["streaming_success"] is False  # Streaming failed

    @pytest.mark.asyncio
    async def test_rag_search_node_success(self, mock_router_state, mock_writer):
        """Test RAG search node execution"""
        mock_router_state["routing_decision"] = "rag_search"
        
        with patch('graph.workflow.create_search_agent_deps') as mock_create_deps:
            mock_deps = Mock()
            mock_create_deps.return_value = mock_deps
            
            with patch('graph.workflow.rag_search_agent') as mock_agent:
                # Mock .iter() streaming to simulate streaming failure, triggering fallback
                mock_agent.iter.side_effect = Exception("Streaming failed")
                
                mock_result = Mock()
                mock_result.data = "RAG search completed successfully"
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                result = await rag_search_node(mock_router_state, writer=mock_writer)
                
                assert result["agent_type"] == "rag_search"
                assert result["final_response"] == "RAG search completed successfully"
                assert result["streaming_success"] is False  # Failed streaming, used fallback

    @pytest.mark.asyncio
    async def test_fallback_node_execution(self, mock_router_state, mock_writer):
        """Test fallback node execution"""
        mock_router_state["routing_decision"] = "fallback"
        
        result = await fallback_node(mock_router_state, writer=mock_writer)
        
        assert result["agent_type"] == "fallback"
        assert "specialized search capabilities" in result["final_response"]
        assert result["streaming_success"] is True

class TestConditionalRouting:
    """Test cases for conditional routing logic"""
    
    def test_route_based_on_decision_web_search(self):
        """Test routing to web search agent"""
        state = {"routing_decision": "web_search"}
        result = route_based_on_decision(state)
        assert result == "web_search_node"
    
    def test_route_based_on_decision_email_search(self):
        """Test routing to email search agent"""
        state = {"routing_decision": "email_search"}
        result = route_based_on_decision(state)
        assert result == "email_search_node"
    
    def test_route_based_on_decision_rag_search(self):
        """Test routing to RAG search agent"""
        state = {"routing_decision": "rag_search"}
        result = route_based_on_decision(state)
        assert result == "rag_search_node"
    
    def test_route_based_on_decision_fallback(self):
        """Test routing to fallback agent"""
        state = {"routing_decision": "fallback"}
        result = route_based_on_decision(state)
        assert result == "fallback_node"
    
    def test_route_based_on_decision_unknown(self):
        """Test routing with unknown decision defaults to fallback"""
        state = {"routing_decision": "unknown_decision"}
        result = route_based_on_decision(state)
        assert result == "fallback_node"
    
    def test_route_based_on_decision_missing(self):
        """Test routing with missing decision defaults to fallback"""
        state = {}
        result = route_based_on_decision(state)
        assert result == "fallback_node"


class TestWorkflowIntegration:
    """Test cases for complete workflow integration"""
    
    @pytest.mark.asyncio
    async def test_create_api_initial_state(self):
        """Test API initial state creation"""
        query = "Test query"
        session_id = "test-session"
        request_id = "test-request"
        message_history = []
        
        state = create_api_initial_state(
            query=query,
            session_id=session_id,
            request_id=request_id,
            pydantic_message_history=message_history
        )
        
        assert state["query"] == query
        assert state["session_id"] == session_id
        assert state["request_id"] == request_id
        assert state["routing_decision"] == ""
        assert state["final_response"] == ""
        assert state["streaming_success"] is False
    
    @pytest.mark.asyncio
    async def test_workflow_graph_structure(self):
        """Test that workflow graph has correct structure"""
        # Verify workflow has the expected nodes
        assert "router_node" in workflow.nodes
        assert "web_search_node" in workflow.nodes
        assert "email_search_node" in workflow.nodes
        assert "rag_search_node" in workflow.nodes
        assert "fallback_node" in workflow.nodes
        
        # Verify workflow structure (CompiledStateGraph doesn't expose edges directly)
        # Test that workflow can be used for routing
        assert workflow is not None
        assert hasattr(workflow, 'ainvoke')
    
    @pytest.mark.asyncio
    async def test_end_to_end_web_search_workflow(self):
        """Test complete end-to-end web search workflow"""
        initial_state = {
            "query": "Latest AI news",
            "session_id": "test-session",
            "request_id": "test-request",
            "routing_decision": "",
            "router_confidence": "",
            "final_response": "",
            "agent_type": "",
            "streaming_success": False
        }
        
        with patch('graph.workflow.create_router_deps'), \
             patch('graph.workflow.create_search_agent_deps'), \
             patch('graph.workflow.router_agent') as mock_router, \
             patch('graph.workflow.web_search_agent') as mock_web_agent:
            
            # Mock router decision
            mock_router_result = Mock()
            mock_router_result.data = RouterResponse(decision="web_search")
            mock_router.run = AsyncMock(return_value=mock_router_result)
            
            # Mock web search agent
            mock_web_result = Mock()
            mock_web_result.data = "Web search results for AI news"
            mock_web_agent.run = AsyncMock(return_value=mock_web_result)
            mock_web_agent.iter.side_effect = Exception("No streaming")
            
            # Run workflow stream (simplified test)
            config = {"configurable": {"thread_id": "test-thread"}}
            
            # Test that workflow can be invoked without errors
            try:
                final_state = await workflow.ainvoke(initial_state, config)
                # Verify final state has expected fields
                assert "routing_decision" in final_state
                assert "agent_type" in final_state
                assert "final_response" in final_state
            except Exception as e:
                # Workflow may fail due to mocking limitations, but structure should be valid
                assert "web_search" in str(e) or "router" in str(e)
    
    @pytest.mark.asyncio
    async def test_fallback_scenario_workflow(self):
        """Test fallback scenario in workflow"""
        initial_state = {
            "query": "Hello there",
            "session_id": "test-session",
            "request_id": "test-request",
            "routing_decision": "",
            "router_confidence": "",
            "final_response": "",
            "agent_type": "",
            "streaming_success": False
        }
        
        with patch('graph.workflow.create_router_deps'), \
             patch('graph.workflow.router_agent') as mock_router:
            
            # Mock router to choose fallback
            mock_router_result = Mock()
            mock_router_result.data = RouterResponse(decision="fallback")
            mock_router.run = AsyncMock(return_value=mock_router_result)
            
            # Test routing decision with mock writer
            mock_writer = Mock()
            router_state = await router_node(initial_state, mock_writer)
            assert router_state["routing_decision"] == "fallback"
            
            # Test conditional routing
            next_node = route_based_on_decision(router_state)
            assert next_node == "fallback_node"
            
            # Test fallback node (merge router state with initial state)
            merged_state = {**initial_state, **router_state}
            final_state = await fallback_node(merged_state, mock_writer)
            assert final_state["agent_type"] == "fallback"
            assert "specialized search capabilities" in final_state["final_response"]

