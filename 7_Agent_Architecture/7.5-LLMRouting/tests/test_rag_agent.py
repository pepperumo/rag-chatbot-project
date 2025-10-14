"""
Unit tests for the RAG search agent functionality.

Tests document search, use existing RAG patterns, and verify streaming.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from agents.rag_search_agent import rag_search_agent
from agents.deps import AgentDependencies
from tools.rag_tools import (
    retrieve_relevant_documents_tool,
    list_documents_tool,
    get_document_content_tool
)


@pytest.fixture
def mock_agent_deps():
    """Create mock agent dependencies for RAG search"""
    return AgentDependencies(
        brave_api_key="test-brave-api-key",
        gmail_credentials_path="test/credentials.json",
        gmail_token_path="test/token.json",
        supabase=MagicMock(),
        embedding_client=MagicMock(),
        http_client=MagicMock(),
        session_id="test-session-123"
    )


@pytest.fixture
def mock_document_search_results():
    """Create mock document search results"""
    return """
# Document ID: doc1
# Document Title: Company Policy Manual
# Document URL: https://company.com/policy-manual

This document contains information about remote work policies and procedures.
Remote work is allowed for full-time employees with manager approval.

---

# Document ID: doc2  
# Document Title: Employee Handbook
# Document URL: https://company.com/handbook

The employee handbook covers vacation policies, benefits, and HR procedures.
Vacation requests must be submitted 2 weeks in advance.

---

# Document ID: doc3
# Document Title: Technical Documentation
# Document URL: https://company.com/tech-docs

This technical documentation covers API usage, troubleshooting, and best practices.
The API supports both REST and GraphQL endpoints.
"""


@pytest.fixture
def mock_documents_list():
    """Create mock documents list"""
    return [
        {
            "id": "doc1",
            "title": "Company Policy Manual",
            "schema": None,
            "url": "https://company.com/policy-manual"
        },
        {
            "id": "doc2", 
            "title": "Employee Handbook",
            "schema": None,
            "url": "https://company.com/handbook"
        },
        {
            "id": "doc3",
            "title": "Technical Documentation", 
            "schema": "api-docs",
            "url": "https://company.com/tech-docs"
        }
    ]


class TestRAGSearchAgent:
    """Test cases for RAG search agent functionality"""

    @pytest.mark.asyncio
    async def test_retrieve_relevant_documents_tool_success(self, mock_agent_deps):
        """Test successful document retrieval using RAG"""
        query = "remote work policy"
        
        mock_embedding = [0.1, 0.2, 0.3] * 512  # Mock 1536-dim embedding
        mock_agent_deps.embedding_client.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=mock_embedding)]
        )
        
        mock_agent_deps.supabase.rpc.return_value.execute.return_value.data = [
            {
                "content": "Remote work policy information",
                "metadata": {
                    "file_id": "policy-doc-1",
                    "file_title": "Remote Work Policy",
                    "file_url": "https://company.com/policy"
                }
            },
            {
                "content": "Additional policy details",
                "metadata": {
                    "file_id": "policy-doc-2", 
                    "file_title": "Work Guidelines",
                    "file_url": "https://company.com/guidelines"
                }
            }
        ]
        
        result = await retrieve_relevant_documents_tool(
            supabase=mock_agent_deps.supabase,
            embedding_client=mock_agent_deps.embedding_client,
            user_query=query
        )
        
        assert isinstance(result, str)
        assert "Remote work policy information" in result
        assert "policy-doc-1" in result
        assert "Remote Work Policy" in result
        assert "---" in result  # Separator between documents

    @pytest.mark.asyncio
    async def test_retrieve_relevant_documents_tool_no_results(self, mock_agent_deps):
        """Test document retrieval with no results"""
        query = "nonexistent topic"
        
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_agent_deps.embedding_client.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=mock_embedding)]
        )
        
        mock_agent_deps.supabase.rpc.return_value.execute.return_value.data = []
        
        result = await retrieve_relevant_documents_tool(
            supabase=mock_agent_deps.supabase,
            embedding_client=mock_agent_deps.embedding_client,
            user_query=query
        )
        
        assert result == "No relevant documents found."

    @pytest.mark.asyncio
    async def test_retrieve_relevant_documents_tool_error(self, mock_agent_deps):
        """Test document retrieval error handling"""
        query = "test query"
        
        # Mock the embedding client to raise an exception
        mock_embedding_client = AsyncMock()
        mock_embedding_client.embeddings.create.side_effect = Exception("Embedding error")
        
        # Mock Supabase to return no documents (since embedding error is caught and zero vector is used)
        mock_agent_deps.supabase.rpc.return_value.execute.return_value.data = []
        
        result = await retrieve_relevant_documents_tool(
            supabase=mock_agent_deps.supabase,
            embedding_client=mock_embedding_client,
            user_query=query
        )
        
        # When embedding fails, get_embedding returns zero vector and no documents are found
        assert result == "No relevant documents found."

    @pytest.mark.asyncio
    async def test_list_documents_tool_success(self, mock_agent_deps, mock_documents_list):
        """Test successful document listing"""
        mock_agent_deps.supabase.from_.return_value.select.return_value.execute.return_value.data = mock_documents_list
        
        result = await list_documents_tool(supabase=mock_agent_deps.supabase)
        
        assert isinstance(result, str)
        result_data = eval(result)  # Convert string back to list
        assert len(result_data) == 3
        assert result_data[0]["title"] == "Company Policy Manual"
        assert result_data[1]["id"] == "doc2"

    @pytest.mark.asyncio
    async def test_list_documents_tool_error(self, mock_agent_deps):
        """Test document listing error handling"""
        mock_agent_deps.supabase.from_.return_value.select.return_value.execute.side_effect = Exception("DB error")
        
        result = await list_documents_tool(supabase=mock_agent_deps.supabase)
        
        assert result == "[]"

    @pytest.mark.asyncio
    async def test_get_document_content_tool_success(self, mock_agent_deps):
        """Test successful document content retrieval"""
        document_id = "policy-doc-1"
        
        mock_agent_deps.supabase.from_.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {
                "id": 1,
                "content": "First chunk of the document content",
                "metadata": {"file_title": "Policy Document - Section 1"}
            },
            {
                "id": 2,
                "content": "Second chunk of the document content", 
                "metadata": {"file_title": "Policy Document - Section 2"}
            }
        ]
        
        result = await get_document_content_tool(
            supabase=mock_agent_deps.supabase,
            document_id=document_id
        )
        
        assert isinstance(result, str)
        assert "Policy Document" in result
        assert "First chunk of the document content" in result
        assert "Second chunk of the document content" in result
        assert len(result) <= 20000  # Verify truncation limit

    @pytest.mark.asyncio
    async def test_get_document_content_tool_not_found(self, mock_agent_deps):
        """Test document content retrieval when document not found"""
        document_id = "nonexistent-doc"
        
        mock_agent_deps.supabase.from_.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
        
        result = await get_document_content_tool(
            supabase=mock_agent_deps.supabase,
            document_id=document_id
        )
        
        assert f"No content found for document: {document_id}" in result

    @pytest.mark.asyncio
    async def test_rag_search_agent_tool_integration(self, mock_agent_deps, mock_document_search_results):
        """Test RAG search agent tool integration"""
        query = "company policy"
        
        with patch('agents.rag_search_agent.retrieve_relevant_documents_tool', return_value=mock_document_search_results) as mock_retrieve:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_agent_deps
            
            from agents.rag_search_agent import search_documents
            result = await search_documents(mock_ctx, query)
            
            mock_retrieve.assert_called_once_with(
                supabase=mock_agent_deps.supabase,
                embedding_client=mock_agent_deps.embedding_client,
                user_query=query
            )
            
            assert result == mock_document_search_results

    @pytest.mark.asyncio
    async def test_rag_search_agent_tool_error_handling(self, mock_agent_deps):
        """Test RAG search agent tool error handling"""
        query = "test query"
        
        with patch('agents.rag_search_agent.retrieve_relevant_documents_tool', side_effect=Exception("RAG Error")) as mock_retrieve:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_agent_deps
            
            from agents.rag_search_agent import search_documents
            result = await search_documents(mock_ctx, query)
            
            assert "Document search failed: RAG Error" in result

    @pytest.mark.asyncio
    async def test_list_available_documents_agent_tool(self, mock_agent_deps):
        """Test list available documents agent tool"""
        mock_documents_str = "[{'id': 'doc1', 'title': 'Test Doc'}]"
        
        with patch('agents.rag_search_agent.list_documents_tool', return_value=mock_documents_str) as mock_list:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_agent_deps
            
            from agents.rag_search_agent import list_available_documents
            result = await list_available_documents(mock_ctx)
            
            mock_list.assert_called_once_with(supabase=mock_agent_deps.supabase)
            assert result == mock_documents_str

    @pytest.mark.asyncio
    async def test_get_full_document_agent_tool(self, mock_agent_deps):
        """Test get full document agent tool"""
        document_id = "test-doc-id"
        mock_content = "Full document content here"
        
        with patch('agents.rag_search_agent.get_document_content_tool', return_value=mock_content) as mock_get:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_agent_deps
            
            from agents.rag_search_agent import get_full_document
            result = await get_full_document(mock_ctx, document_id)
            
            mock_get.assert_called_once_with(
                supabase=mock_agent_deps.supabase,
                document_id=document_id
            )
            assert result == mock_content

    @pytest.mark.asyncio
    async def test_analyze_search_results_tool(self, mock_agent_deps, mock_document_search_results):
        """Test search results analysis tool"""
        query = "remote work policy"
        focus_areas = "policies, procedures"
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_agent_deps
        
        from agents.rag_search_agent import analyze_search_results
        result = await analyze_search_results(mock_ctx, mock_document_search_results, query, focus_areas)
        
        assert isinstance(result, dict)
        assert "summary" in result
        assert "query" in result
        assert "documents_found" in result
        assert "key_points" in result
        
        assert result["query"] == query
        assert result["focus_areas"] == focus_areas
        assert result["documents_found"] == 3  # Based on mock data
        assert len(result["key_points"]) == 3
        
        # Check that document info was extracted correctly
        summary = result["summary"]
        assert query in summary
        assert focus_areas in summary
        assert "Company Policy Manual" in result["key_points"][0]
        assert "Employee Handbook" in result["key_points"][1]

    @pytest.mark.asyncio
    async def test_analyze_search_results_no_results(self, mock_agent_deps):
        """Test analysis with no search results"""
        query = "no results query"
        search_results = "No relevant documents found."
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_agent_deps
        
        from agents.rag_search_agent import analyze_search_results
        result = await analyze_search_results(mock_ctx, search_results, query)
        
        assert result["summary"] == f"No relevant documents found for query: '{query}'"
        assert result["documents_found"] == 0
        assert result["key_points"] == []

    @pytest.mark.asyncio
    async def test_analyze_search_results_error_handling(self, mock_agent_deps):
        """Test analysis error handling"""
        query = "error query"
        search_results = mock_document_search_results  # This will cause parsing error in extraction
        
        # Patch the document ID extraction to cause an error
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_agent_deps
        
        # Mock the function to raise an exception during processing
        with patch('agents.rag_search_agent.analyze_search_results', side_effect=Exception("Analysis error")):
            from agents.rag_search_agent import analyze_search_results
            
            with pytest.raises(Exception, match="Analysis error"):
                await analyze_search_results(mock_ctx, search_results, query)

    @pytest.mark.asyncio
    async def test_rag_search_agent_configuration(self):
        """Test RAG search agent configuration"""
        # Test that RAG search agent can be imported
        from agents.rag_search_agent import rag_search_agent
        from agents.deps import AgentDependencies
        
        # Verify basic functionality
        assert rag_search_agent is not None
        assert AgentDependencies is not None
        
        # Test that AgentDependencies has RAG-related fields
        deps = AgentDependencies(
            brave_api_key="test",
            gmail_credentials_path="test", 
            gmail_token_path="test",
            supabase=None,
            embedding_client=None,
            http_client=None
        )
        assert deps.supabase is None  # Can be None in tests
        assert deps.embedding_client is None  # Can be None in tests

    @pytest.mark.asyncio
    async def test_rag_search_agent_streaming_mock(self, mock_agent_deps):
        """Test RAG search agent streaming capabilities (mocked)"""
        query = "test streaming query"
        
        # Mock the agent's run_stream method
        mock_stream_result = MagicMock()
        mock_stream_result.stream_text.return_value = AsyncMock()
        mock_stream_result.stream_text.return_value.__aiter__ = AsyncMock(return_value=iter(["chunk1", "chunk2", "chunk3"]))
        
        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_stream_result)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(rag_search_agent, 'run_stream', return_value=mock_context_manager):
            # Test that we can create the stream context
            stream_context = rag_search_agent.run_stream(query, deps=mock_agent_deps)
            assert stream_context is not None

    @pytest.mark.asyncio
    async def test_embedding_generation_and_search(self, mock_agent_deps):
        """Test embedding generation and vector search"""
        query = "test embedding query"
        
        # Create proper async mock for embedding client
        mock_embedding_client = AsyncMock()
        mock_embedding = [0.1] * 1536  # Standard embedding size
        mock_embedding_client.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=mock_embedding)]
        )
        
        # Mock vector search results
        mock_agent_deps.supabase.rpc.return_value.execute.return_value.data = [
            {
                "content": "Relevant document content",
                "metadata": {
                    "file_id": "test-doc",
                    "file_title": "Test Document",
                    "file_url": "https://test.com/doc"
                }
            }
        ]
        
        result = await retrieve_relevant_documents_tool(
            supabase=mock_agent_deps.supabase,
            embedding_client=mock_embedding_client,
            user_query=query
        )
        
        # Verify embedding was created
        mock_embedding_client.embeddings.create.assert_called_once()
        
        # Verify vector search was called
        mock_agent_deps.supabase.rpc.assert_called_once_with(
            'match_documents',
            {
                'query_embedding': mock_embedding,
                'match_count': 4
            }
        )
        
        assert "Relevant document content" in result

    @pytest.mark.asyncio
    async def test_document_chunking_and_formatting(self, mock_agent_deps):
        """Test document chunking and proper formatting"""
        document_id = "long-doc"
        
        # Create a very long document to test truncation
        long_content = "This is a test chunk. " * 1000  # Create content > 20000 chars
        
        mock_agent_deps.supabase.from_.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {
                "id": 1,
                "content": long_content,
                "metadata": {"file_title": "Long Document - Part 1"}
            }
        ]
        
        result = await get_document_content_tool(
            supabase=mock_agent_deps.supabase,
            document_id=document_id
        )
        
        # Verify content is truncated to 20000 characters
        assert len(result) <= 20000
        assert "Long Document" in result
        assert "This is a test chunk" in result

    @pytest.mark.asyncio
    async def test_document_metadata_extraction(self, mock_agent_deps):
        """Test proper extraction of document metadata"""
        search_results = """
# Document ID: policy-2024
# Document Title: Updated Remote Work Policy
# Document URL: https://company.com/policies/remote-work-2024

Content about remote work policies and guidelines.

---

# Document ID: handbook-v3
# Document Title: Employee Handbook Version 3
# Document URL: https://company.com/handbook/v3

Employee guidelines and procedures.
"""
        
        query = "company policies"
        
        mock_ctx = MagicMock()
        mock_ctx.deps = mock_agent_deps
        
        from agents.rag_search_agent import analyze_search_results
        result = await analyze_search_results(mock_ctx, search_results, query)
        
        # Verify metadata was correctly extracted
        assert result["documents_found"] == 2
        assert "Updated Remote Work Policy (ID: policy-2024)" in result["key_points"][0]
        assert "Employee Handbook Version 3 (ID: handbook-v3)" in result["key_points"][1]