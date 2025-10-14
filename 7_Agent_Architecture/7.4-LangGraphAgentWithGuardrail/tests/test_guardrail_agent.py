import pytest
from unittest.mock import Mock, AsyncMock, patch
import re

from agents.guardrail_agent import guardrail_agent
from agents.deps import AgentDeps
from tools.validation_tools import (
    extract_google_drive_urls,
    extract_file_ids_from_urls,
    validate_citation_exists,
    validate_citation_relevance,
    validate_all_citations
)


class TestGuardrailAgent:
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies for testing"""
        return AgentDeps(
            supabase=Mock(),
            embedding_client=AsyncMock(),
            http_client=AsyncMock(),
            feedback=None
        )

    @pytest.mark.asyncio
    async def test_guardrail_agent_initialization(self, mock_deps):
        """Test that guardrail agent initializes correctly"""
        assert guardrail_agent is not None
        assert guardrail_agent._deps_type == AgentDeps

    @pytest.mark.asyncio
    async def test_get_document_content_tool(self, mock_deps):
        """Test get_document_content tool"""
        with patch('agents.guardrail_agent.get_document_content_tool') as mock_tool:
            mock_tool.return_value = "Full document content for test123"
            
            from agents.guardrail_agent import get_document_content
            
            # Create a mock RunContext
            mock_ctx = Mock()
            mock_ctx.deps = mock_deps
            
            result = await get_document_content(mock_ctx, "test123")
            
            assert result == "Full document content for test123"
            mock_tool.assert_called_once_with(mock_deps.supabase, "test123")

    @pytest.mark.asyncio
    async def test_extract_citations_tool(self, mock_deps):
        """Test extract_citations tool"""
        response_text = """
        Based on research, AI safety is important. 
        Source: https://docs.google.com/document/d/test123/
        Additional info: https://docs.google.com/document/d/test456/
        """
        
        from agents.guardrail_agent import extract_citations
        
        # Create a mock RunContext
        mock_ctx = Mock()
        mock_ctx.deps = mock_deps
        
        result = await extract_citations(mock_ctx, response_text)
        
        assert "Found 2 citations" in result
        assert "test123" in result
        assert "test456" in result

    @pytest.mark.asyncio
    async def test_validate_citations_tool_valid(self, mock_deps):
        """Test validate_citations tool with valid citations"""
        with patch('agents.guardrail_agent.validate_all_citations') as mock_validate:
            mock_validate.return_value = {
                "status": "valid",
                "feedback": "All citations are valid and relevant"
            }
            
            from agents.guardrail_agent import validate_citations
            
            # Create a mock RunContext
            mock_ctx = Mock()
            mock_ctx.deps = mock_deps
            
            result = await validate_citations(
                mock_ctx, 
                "Response with https://docs.google.com/document/d/test123/",
                "What is AI safety?"
            )
            
            assert result == "VALID - All citations are accurate and relevant"

    @pytest.mark.asyncio
    async def test_validate_citations_tool_invalid(self, mock_deps):
        """Test validate_citations tool with invalid citations"""
        with patch('agents.guardrail_agent.validate_all_citations') as mock_validate:
            mock_validate.return_value = {
                "status": "invalid",
                "feedback": "Document not found in knowledge base"
            }
            
            from agents.guardrail_agent import validate_citations
            
            # Create a mock RunContext
            mock_ctx = Mock()
            mock_ctx.deps = mock_deps
            
            result = await validate_citations(
                mock_ctx, 
                "Response with https://docs.google.com/document/d/fake123/",
                "What is AI safety?"
            )
            
            assert result == "INVALID - Document not found in knowledge base"


class TestValidationTools:
    
    def test_extract_google_drive_urls(self):
        """Test Google Drive URL extraction"""
        text = """
        Based on research, AI safety is important. 
        Source: https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/
        Additional info: https://docs.google.com/document/d/9i8h7g6f5e4d3c2b1a0z/
        Not a drive link: https://example.com/document
        """
        
        urls = extract_google_drive_urls(text)
        
        assert len(urls) == 2
        assert "https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/" in urls
        assert "https://docs.google.com/document/d/9i8h7g6f5e4d3c2b1a0z/" in urls

    def test_extract_file_ids_from_urls(self):
        """Test file ID extraction from URLs"""
        urls = [
            "https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/",
            "https://docs.google.com/document/d/9i8h7g6f5e4d3c2b1a0z/"
        ]
        
        file_ids = extract_file_ids_from_urls(urls)
        
        assert len(file_ids) == 2
        assert "1a2b3c4d5e6f7g8h9i0j" in file_ids
        assert "9i8h7g6f5e4d3c2b1a0z" in file_ids

    def test_extract_google_drive_urls_no_matches(self):
        """Test URL extraction with no valid URLs"""
        text = """
        This is just regular text without any Google Drive links.
        Here's a normal link: https://example.com/document
        """
        
        urls = extract_google_drive_urls(text)
        
        assert len(urls) == 0

    def test_extract_google_drive_urls_malformed(self):
        """Test URL extraction with malformed URLs"""
        text = """
        Almost correct: https://docs.google.com/document/d/
        Missing part: https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j
        Correct: https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/
        """
        
        urls = extract_google_drive_urls(text)
        
        assert len(urls) == 1
        assert "https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/" in urls

    @pytest.mark.asyncio
    async def test_validate_citation_exists_true(self):
        """Test citation existence validation - document exists"""
        mock_supabase = Mock()
        mock_supabase.from_.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{"id": "1"}]
        
        result = await validate_citation_exists(mock_supabase, "test123")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_citation_exists_false(self):
        """Test citation existence validation - document doesn't exist"""
        mock_supabase = Mock()
        mock_supabase.from_.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        
        result = await validate_citation_exists(mock_supabase, "test123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_citation_relevance_true(self):
        """Test citation relevance validation - relevant document"""
        mock_supabase = Mock()
        mock_embedding_client = AsyncMock()
        
        # Mock get_document_content_tool
        with patch('tools.validation_tools.get_document_content_tool') as mock_get_doc:
            mock_get_doc.return_value = "This document discusses AI safety measures and protocols"
            
            # Mock get_embedding to return similar embeddings
            with patch('tools.validation_tools.get_embedding') as mock_embedding:
                mock_embedding.side_effect = [
                    [0.1, 0.2, 0.3],  # query embedding
                    [0.15, 0.25, 0.35],  # response embedding
                    [0.12, 0.22, 0.32]   # document embedding
                ]
                
                result = await validate_citation_relevance(
                    mock_supabase,
                    mock_embedding_client,
                    "test123",
                    "What is AI safety?",
                    "AI safety is about preventing harmful AI"
                )
                
                assert result is True

    @pytest.mark.asyncio
    async def test_validate_citation_relevance_false(self):
        """Test citation relevance validation - irrelevant document"""
        mock_supabase = Mock()
        mock_embedding_client = AsyncMock()
        
        # Mock get_document_content_tool
        with patch('tools.validation_tools.get_document_content_tool') as mock_get_doc:
            mock_get_doc.return_value = "This document is about cooking recipes"
            
            # Mock get_embedding to return dissimilar embeddings
            with patch('tools.validation_tools.get_embedding') as mock_embedding:
                mock_embedding.side_effect = [
                    [1.0, 0.0, 0.0],  # query embedding
                    [1.0, 0.0, 0.0],  # response embedding
                    [0.0, 1.0, 0.0]   # document embedding (orthogonal, similarity = 0)
                ]
                
                result = await validate_citation_relevance(
                    mock_supabase,
                    mock_embedding_client,
                    "test123",
                    "What is AI safety?",
                    "AI safety is about preventing harmful AI"
                )
                
                # The cosine similarity should be low, so result should be False
                assert result is False

    @pytest.mark.asyncio
    async def test_validate_all_citations_valid(self):
        """Test validation of all citations - valid case"""
        mock_supabase = Mock()
        mock_embedding_client = AsyncMock()
        
        response_text = "AI safety is important. Source: https://docs.google.com/document/d/test123/"
        
        with patch('tools.validation_tools.validate_citation_exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('tools.validation_tools.validate_citation_relevance') as mock_relevance:
                mock_relevance.return_value = True
                
                result = await validate_all_citations(
                    mock_supabase,
                    mock_embedding_client,
                    response_text,
                    "What is AI safety?"
                )
                
                assert result["status"] == "valid"
                assert "valid and relevant" in result["feedback"]

    @pytest.mark.asyncio
    async def test_validate_all_citations_invalid(self):
        """Test validation of all citations - invalid case"""
        mock_supabase = Mock()
        mock_embedding_client = AsyncMock()
        
        response_text = "AI safety is important. Source: https://docs.google.com/document/d/test123/"
        
        with patch('tools.validation_tools.validate_citation_exists') as mock_exists:
            mock_exists.return_value = False
            
            result = await validate_all_citations(
                mock_supabase,
                mock_embedding_client,
                response_text,
                "What is AI safety?"
            )
            
            assert result["status"] == "invalid"
            assert "not found in knowledge base" in result["feedback"]

    @pytest.mark.asyncio
    async def test_validate_all_citations_no_urls(self):
        """Test validation when no citations are found"""
        mock_supabase = Mock()
        mock_embedding_client = AsyncMock()
        
        response_text = "AI safety is important but no citations provided."
        
        result = await validate_all_citations(
            mock_supabase,
            mock_embedding_client,
            response_text,
            "What is AI safety?"
        )
        
        assert result["status"] == "invalid"
        assert "No Google Drive citations found" in result["feedback"]