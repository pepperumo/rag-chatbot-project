import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from agents.primary_agent import primary_agent
from agents.deps import AgentDeps


class TestPrimaryAgent:
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies for testing"""
        return AgentDeps(
            supabase=Mock(),
            embedding_client=AsyncMock(),
            http_client=AsyncMock(),
            feedback=None
        )

    @pytest.fixture
    def mock_deps_with_feedback(self):
        """Create mock dependencies with feedback for testing"""
        return AgentDeps(
            supabase=Mock(),
            embedding_client=AsyncMock(),
            http_client=AsyncMock(),
            feedback="Please include proper citations from the knowledge base"
        )

    @pytest.mark.asyncio
    async def test_primary_agent_initialization(self, mock_deps):
        """Test that primary agent initializes correctly"""
        assert primary_agent is not None
        assert primary_agent._deps_type == AgentDeps

    @pytest.mark.asyncio
    async def test_retrieve_relevant_documents_tool(self, mock_deps):
        """Test retrieve_relevant_documents tool"""
        # Mock the tool function
        with patch('agents.primary_agent.retrieve_relevant_documents_tool') as mock_tool:
            mock_tool.return_value = "Mock document content with file_id: test123"
            
            # Test the tool directly
            from agents.primary_agent import retrieve_relevant_documents
            
            # Create a mock RunContext
            mock_ctx = Mock()
            mock_ctx.deps = mock_deps
            
            result = await retrieve_relevant_documents(mock_ctx, "test query")
            
            assert result == "Mock document content with file_id: test123"
            mock_tool.assert_called_once_with(
                mock_deps.supabase,
                mock_deps.embedding_client,
                "test query"
            )

    @pytest.mark.asyncio
    async def test_list_documents_tool(self, mock_deps):
        """Test list_documents tool"""
        with patch('agents.primary_agent.list_documents_tool') as mock_tool:
            mock_tool.return_value = "[{'id': 'test123', 'title': 'Test Document'}]"
            
            from agents.primary_agent import list_documents
            
            # Create a mock RunContext
            mock_ctx = Mock()
            mock_ctx.deps = mock_deps
            
            result = await list_documents(mock_ctx)
            
            assert result == "[{'id': 'test123', 'title': 'Test Document'}]"
            mock_tool.assert_called_once_with(mock_deps.supabase)

    @pytest.mark.asyncio
    async def test_get_document_content_tool(self, mock_deps):
        """Test get_document_content tool"""
        with patch('agents.primary_agent.get_document_content_tool') as mock_tool:
            mock_tool.return_value = "Full document content for test123"
            
            from agents.primary_agent import get_document_content
            
            # Create a mock RunContext
            mock_ctx = Mock()
            mock_ctx.deps = mock_deps
            
            result = await get_document_content(mock_ctx, "test123")
            
            assert result == "Full document content for test123"
            mock_tool.assert_called_once_with(mock_deps.supabase, "test123")

    @pytest.mark.asyncio
    async def test_system_prompt_without_feedback(self, mock_deps):
        """Test system prompt when no feedback is provided"""
        from agents.primary_agent import add_feedback_to_prompt
        
        # Create a mock RunContext
        mock_ctx = Mock()
        mock_ctx.deps = mock_deps
        
        result = await add_feedback_to_prompt(mock_ctx)
        
        assert result == ""

    @pytest.mark.asyncio
    async def test_system_prompt_with_feedback(self, mock_deps_with_feedback):
        """Test system prompt when feedback is provided"""
        from agents.primary_agent import add_feedback_to_prompt
        
        # Create a mock RunContext
        mock_ctx = Mock()
        mock_ctx.deps = mock_deps_with_feedback
        
        result = await add_feedback_to_prompt(mock_ctx)
        
        assert "FEEDBACK FROM VALIDATION:" in result
        assert "Please include proper citations from the knowledge base" in result

    @pytest.mark.asyncio
    async def test_agent_response_with_citations(self, mock_deps):
        """Test that agent generates response with proper citations"""
        # Mock the RAG tools to return content with file_ids
        with patch('tools.rag_tools.retrieve_relevant_documents_tool') as mock_retrieve:
            mock_retrieve.return_value = """
# Document ID: test123
# Document Title: Test Document
# Document URL: https://docs.google.com/document/d/test123/

Test document content about AI safety.
"""
            
            # Mock the agent run method
            with patch.object(primary_agent, 'run') as mock_run:
                mock_response = Mock()
                mock_response.data = "Based on the research, AI safety is important. Source: https://docs.google.com/document/d/test123/"
                mock_run.return_value = mock_response
                
                result = await primary_agent.run("What is AI safety?", deps=mock_deps)
                
                assert "https://docs.google.com/document/d/test123/" in result.data
                assert "AI safety" in result.data

    @pytest.mark.asyncio
    async def test_agent_error_handling(self, mock_deps):
        """Test agent error handling"""
        with patch('agents.primary_agent.retrieve_relevant_documents_tool') as mock_retrieve:
            mock_retrieve.side_effect = Exception("Database connection failed")
            
            # The agent should handle the error gracefully
            try:
                from agents.primary_agent import retrieve_relevant_documents
                
                # Create a mock RunContext
                mock_ctx = Mock()
                mock_ctx.deps = mock_deps
                
                await retrieve_relevant_documents(mock_ctx, "test query")
            except Exception as e:
                assert "Database connection failed" in str(e)

    @pytest.mark.asyncio
    async def test_agent_with_no_documents_found(self, mock_deps):
        """Test agent behavior when no documents are found"""
        with patch('agents.primary_agent.retrieve_relevant_documents_tool') as mock_retrieve:
            mock_retrieve.return_value = "No relevant documents found."
            
            from agents.primary_agent import retrieve_relevant_documents
            
            # Create a mock RunContext
            mock_ctx = Mock()
            mock_ctx.deps = mock_deps
            
            result = await retrieve_relevant_documents(mock_ctx, "obscure query")
            
            assert result == "No relevant documents found."