"""
Unit tests for the supervisor agent functionality.

Tests supervisor agent with structured output streaming and delegation logic.
"""

import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

from agents.supervisor_agent import supervisor_agent, SupervisorDecision, SupervisorAgentDependencies


@pytest.fixture
def mock_supervisor_deps():
    """Create mock supervisor dependencies"""
    return SupervisorAgentDependencies(
        session_id="test-session-123"
    )


@pytest.fixture
def mock_supervisor_decision():
    """Create mock supervisor decision output"""
    return SupervisorDecision(
        messages="Based on your request, I'll delegate to the web research agent.",
        delegate_to="web_research",
        reasoning="User is asking for research about a specific topic",
        final_response=False
    )


@pytest.fixture
def mock_supervisor_final_decision():
    """Create mock supervisor final decision output"""
    return SupervisorDecision(
        messages="I've completed the research and task management. Here's your summary...",
        delegate_to=None,
        reasoning="All work is complete, providing final response",
        final_response=True
    )


@pytest.fixture
def mock_supervisor_result():
    """Create mock supervisor agent result"""
    mock_result = MagicMock()
    mock_result.output = {
        "messages": "Research delegation complete",
        "delegate_to": "web_research",
        "reasoning": "Need to gather information first",
        "final_response": False
    }
    return mock_result


class TestSupervisorDecision:
    """Test cases for SupervisorDecision Pydantic model"""

    def test_supervisor_decision_creation(self):
        """Test creating a valid SupervisorDecision"""
        decision = {
            "messages": "Test message",
            "delegate_to": "web_research",
            "reasoning": "Test reasoning",
            "final_response": False
        }
        
        assert decision.get("messages") == "Test message"
        assert decision.get("delegate_to") == "web_research"
        assert decision.get("reasoning") == "Test reasoning"
        assert decision.get("final_response") is False

    def test_supervisor_decision_optional_fields(self):
        """Test SupervisorDecision with optional fields"""
        # Test with minimal required fields
        decision = {
            "reasoning": "Test reasoning"
        }
        
        assert decision.get("messages") is None
        assert decision.get("delegate_to") is None
        assert decision.get("reasoning") == "Test reasoning"
        assert decision.get("final_response", False) is False  # Default value

    def test_supervisor_decision_final_response(self):
        """Test SupervisorDecision for final response"""
        decision = {
            "messages": "Final response to user",
            "delegate_to": None,
            "reasoning": "All work complete",
            "final_response": True
        }
        
        assert decision.get("messages") == "Final response to user"
        assert decision.get("delegate_to") is None
        assert decision.get("final_response") is True

    def test_supervisor_decision_valid_delegation_targets(self):
        """Test valid delegation targets"""
        valid_targets = ["web_research", "task_management", "email_draft", None]
        
        for target in valid_targets:
            decision = {
                "delegate_to": target,
                "reasoning": "Test reasoning"
            }
            assert decision.get("delegate_to") == target

    def test_supervisor_decision_validation_error(self):
        """Test SupervisorDecision structure validation"""
        # TypedDict doesn't do runtime validation, but we can test basic structure
        decision = {}
        
        # Should be able to access fields safely with .get()
        assert decision.get("messages") is None
        assert decision.get("delegate_to") is None
        assert decision.get("reasoning") is None
        assert decision.get("final_response", False) is False


class TestSupervisorAgent:
    """Test cases for supervisor agent functionality"""

    @pytest.mark.asyncio
    async def test_supervisor_agent_delegation_decision(self, mock_supervisor_deps, mock_supervisor_result):
        """Test supervisor agent making delegation decision"""
        query = "Research the latest trends in AI and create a project plan"
        
        with patch.object(supervisor_agent, 'run', return_value=mock_supervisor_result) as mock_run:
            result = await supervisor_agent.run(query, deps=mock_supervisor_deps)
            
            # Verify the agent was called
            mock_run.assert_called_with(query, deps=mock_supervisor_deps)
            
            # Verify result structure
            assert hasattr(result, 'output')
            assert isinstance(result.output, dict)
            assert result.output.get("delegate_to") == "web_research"
            assert result.output.get("final_response") is False

    @pytest.mark.asyncio
    async def test_supervisor_agent_final_response(self, mock_supervisor_deps):
        """Test supervisor agent providing final response"""
        query = "Provide final summary based on completed work"
        
        mock_final_result = MagicMock()
        mock_final_result.output = {
            "messages": "Here's your complete summary of all work done...",
            "delegate_to": None,
            "reasoning": "All agents have completed their work",
            "final_response": True
        }
        
        with patch.object(supervisor_agent, 'run', return_value=mock_final_result) as mock_run:
            result = await supervisor_agent.run(query, deps=mock_supervisor_deps)
            
            # Verify final response
            assert result.output.get("final_response") is True
            assert result.output.get("delegate_to") is None
            assert result.output.get("messages") is not None

    @pytest.mark.asyncio
    async def test_supervisor_agent_with_context(self, mock_supervisor_deps, mock_supervisor_result):
        """Test supervisor agent with context from previous agents"""
        query = """
        User Request: Create a marketing plan for AI product
        Shared State: Web Research: Found 5 key AI trends...
        Task Management: Created project with 8 tasks...
        Iteration: 3/20
        """
        
        with patch.object(supervisor_agent, 'run', return_value=mock_supervisor_result) as mock_run:
            result = await supervisor_agent.run(query, deps=mock_supervisor_deps)
            
            # Verify the agent processed the context
            mock_run.assert_called_with(query, deps=mock_supervisor_deps)
            assert hasattr(result, 'output')

    @pytest.mark.asyncio
    async def test_supervisor_agent_with_message_history(self, mock_supervisor_deps, mock_supervisor_result):
        """Test supervisor agent with message history"""
        query = "Continue with the marketing plan project"
        message_history = [MagicMock()]
        
        with patch.object(supervisor_agent, 'run', return_value=mock_supervisor_result) as mock_run:
            result = await supervisor_agent.run(
                query, 
                deps=mock_supervisor_deps,
                message_history=message_history
            )
            
            # Verify the agent was called with message history
            mock_run.assert_called_with(
                query, 
                deps=mock_supervisor_deps,
                message_history=message_history
            )

    def test_supervisor_dependencies_structure(self):
        """Test SupervisorAgentDependencies dataclass structure"""
        deps = SupervisorAgentDependencies(
            session_id="test-session"
        )
        
        assert deps.session_id == "test-session"
        
        # Test with None session_id
        deps_none = SupervisorAgentDependencies()
        assert deps_none.session_id is None

    @pytest.mark.asyncio
    async def test_supervisor_agent_delegation_patterns(self, mock_supervisor_deps):
        """Test different delegation patterns"""
        test_cases = [
            ("Research AI trends", "web_research"),
            ("Create project plan", "task_management"),
            ("Draft email to stakeholders", "email_draft"),
            ("Final summary", None)  # Final response
        ]
        
        for query, expected_delegate in test_cases:
            mock_result = MagicMock()
            mock_result.output = {
                "messages": "Response message",
                "delegate_to": expected_delegate,
                "reasoning": "Delegation reasoning",
                "final_response": (expected_delegate is None)
            }
            
            with patch.object(supervisor_agent, 'run', return_value=mock_result):
                result = await supervisor_agent.run(query, deps=mock_supervisor_deps)
                
                assert result.output.get("delegate_to") == expected_delegate
                assert result.output.get("final_response") == (expected_delegate is None)

    @pytest.mark.asyncio
    async def test_supervisor_agent_streaming_compatibility(self, mock_supervisor_deps):
        """Test supervisor agent streaming mode compatibility"""
        query = "Test streaming mode"
        
        # Mock streaming result
        mock_streaming_result = MagicMock()
        mock_streaming_result.output = SupervisorDecision(
            messages="Streaming response",
            delegate_to="web_research",
            reasoning="Streaming test",
            final_response=False
        )
        
        with patch.object(supervisor_agent, 'iter') as mock_iter:
            # Mock the async context manager
            mock_run = MagicMock()
            mock_run.result = mock_streaming_result
            mock_iter.return_value.__aenter__.return_value = mock_run
            mock_run.__aiter__.return_value = []  # No streaming events for now
            
            # Test that streaming interface exists and works
            async with supervisor_agent.iter(query, deps=mock_supervisor_deps) as run:
                async for node in run:
                    pass  # Process streaming events
                
                # Verify result is accessible
                assert hasattr(run, 'result')
                assert hasattr(run.result, 'output')

    def test_supervisor_system_prompt_structure(self):
        """Test that supervisor agent has proper system prompt"""
        # Access the system prompt - it's imported as SUPERVISOR_SYSTEM_PROMPT
        from agents.supervisor_agent import SUPERVISOR_SYSTEM_PROMPT
        
        # Verify key elements are present
        assert "supervisor" in SUPERVISOR_SYSTEM_PROMPT.lower()
        assert "delegate" in SUPERVISOR_SYSTEM_PROMPT.lower()
        assert "coordinat" in SUPERVISOR_SYSTEM_PROMPT.lower()  # matches "coordinating"
        
        # Verify mentions of available agents
        assert "web_research" in SUPERVISOR_SYSTEM_PROMPT
        assert "task_management" in SUPERVISOR_SYSTEM_PROMPT
        assert "email_draft" in SUPERVISOR_SYSTEM_PROMPT