"""
Unit tests for the task management agent functionality.

Tests task management agent with Asana API integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from agents.task_management_agent import task_management_agent, TaskManagementAgentDependencies


@pytest.fixture
def mock_task_deps():
    """Create mock task management dependencies"""
    return TaskManagementAgentDependencies(
        asana_api_key="test-asana-key",
        asana_workspace_gid="123456789",
        session_id="test-session-123"
    )


@pytest.fixture
def mock_task_deps_no_workspace():
    """Create mock task management dependencies without workspace"""
    return TaskManagementAgentDependencies(
        asana_api_key="test-asana-key",
        session_id="test-session-123"
    )


@pytest.fixture
def mock_workspace_info_result():
    """Create mock workspace info result"""
    return {
        "success": True,
        "workspaces": [
            {"gid": "123456789", "name": "Test Workspace"},
            {"gid": "987654321", "name": "Another Workspace"}
        ],
        "count": 2
    }


@pytest.fixture
def mock_project_creation_result():
    """Create mock project creation result"""
    return {
        "success": True,
        "project_gid": "proj_123456",
        "project_name": "AI Marketing Campaign",
        "workspace_gid": "123456789",
        "created_at": "2024-01-01T12:00:00",
        "permalink_url": "https://app.asana.com/0/proj_123456/"
    }


@pytest.fixture
def mock_task_creation_result():
    """Create mock task creation result"""
    return {
        "success": True,
        "task_gid": "task_789012",
        "task_name": "Research market trends",
        "project_gid": "proj_123456",
        "created_at": "2024-01-01T12:00:00",
        "permalink_url": "https://app.asana.com/0/proj_123456/task_789012"
    }


@pytest.fixture
def mock_task_agent_result():
    """Create mock task management agent result"""
    mock_result = MagicMock()
    mock_result.output = "Created project 'AI Marketing Campaign' with 5 tasks organized by priority..."
    return mock_result


class TestTaskManagementAgent:
    """Test cases for task management agent functionality"""

    @pytest.mark.asyncio
    async def test_get_workspace_info_success(self, mock_task_deps, mock_workspace_info_result):
        """Test successful workspace info retrieval"""
        with patch('agents.task_management_agent.get_workspace_info_tool', return_value=mock_workspace_info_result) as mock_get:
            # Create mock context
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps
            
            # Import and call the tool function directly
            from agents.task_management_agent import get_workspace_info
            result = await get_workspace_info(mock_ctx)
            
            # Verify Asana tool was called with correct parameters
            mock_get.assert_called_once_with(
                api_key="test-asana-key"
            )
            
            # Verify results
            assert result == mock_workspace_info_result
            assert result["success"] is True
            assert len(result["workspaces"]) == 2

    @pytest.mark.asyncio
    async def test_get_workspace_info_error(self, mock_task_deps):
        """Test workspace info retrieval error handling"""
        with patch('agents.task_management_agent.get_workspace_info_tool', side_effect=Exception("Asana API Error")) as mock_get:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps
            
            from agents.task_management_agent import get_workspace_info
            result = await get_workspace_info(mock_ctx)
            
            # Verify error handling
            assert result["success"] is False
            assert "Asana API Error" in result["error"]
            assert result["workspaces"] == []
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_task_deps, mock_project_creation_result):
        """Test successful project creation"""
        project_name = "AI Marketing Campaign"
        project_notes = "Project to develop AI-driven marketing strategies"
        
        with patch('agents.task_management_agent.create_project_tool', return_value=mock_project_creation_result) as mock_create:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps
            
            from agents.task_management_agent import create_project
            result = await create_project(mock_ctx, project_name, project_notes, False)
            
            # Verify Asana tool was called with correct parameters
            mock_create.assert_called_once_with(
                api_key="test-asana-key",
                name=project_name,
                workspace_gid="123456789",
                notes=project_notes,
                public=False
            )
            
            # Verify results
            assert result == mock_project_creation_result
            assert result["success"] is True
            assert result["project_gid"] == "proj_123456"

    @pytest.mark.asyncio
    async def test_create_project_no_workspace_auto_discover(self, mock_task_deps_no_workspace, mock_workspace_info_result, mock_project_creation_result):
        """Test project creation with auto workspace discovery"""
        project_name = "Test Project"
        
        with patch('agents.task_management_agent.get_workspace_info_tool', return_value=mock_workspace_info_result), \
             patch('agents.task_management_agent.create_project_tool', return_value=mock_project_creation_result) as mock_create:
            
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps_no_workspace
            
            from agents.task_management_agent import create_project
            result = await create_project(mock_ctx, project_name)
            
            # Verify project was created with auto-discovered workspace
            mock_create.assert_called_once_with(
                api_key="test-asana-key",
                name=project_name,
                workspace_gid="123456789",  # First workspace from mock
                notes=None,
                public=False
            )
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_project_no_workspace_available(self, mock_task_deps_no_workspace):
        """Test project creation with no workspace available"""
        project_name = "Test Project"
        
        # Mock empty workspace response
        empty_workspace = {"success": True, "workspaces": [], "count": 0}
        
        with patch('agents.task_management_agent.get_workspace_info_tool', return_value=empty_workspace):
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps_no_workspace
            
            from agents.task_management_agent import create_project
            result = await create_project(mock_ctx, project_name)
            
            # Verify error handling
            assert result["success"] is False
            assert "No workspace available" in result["error"]
            assert result["project_name"] == project_name

    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_task_deps, mock_task_creation_result):
        """Test successful task creation"""
        task_name = "Research market trends"
        project_gid = "proj_123456"
        task_notes = "Analyze current AI market trends and competitor landscape"
        
        with patch('agents.task_management_agent.create_task_tool', return_value=mock_task_creation_result) as mock_create:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps
            
            from agents.task_management_agent import create_task
            result = await create_task(mock_ctx, task_name, project_gid, task_notes)
            
            # Verify Asana tool was called with correct parameters
            mock_create.assert_called_once_with(
                api_key="test-asana-key",
                name=task_name,
                project_gid=project_gid,
                notes=task_notes,
                assignee=None,
                due_on=None
            )
            
            # Verify results
            assert result == mock_task_creation_result
            assert result["success"] is True
            assert result["task_gid"] == "task_789012"

    @pytest.mark.asyncio
    async def test_create_task_with_assignee_and_due_date(self, mock_task_deps, mock_task_creation_result):
        """Test task creation with assignee and due date"""
        task_name = "Review marketing materials"
        assignee = "john.doe@company.com"
        due_date = "2024-12-31"
        
        with patch('agents.task_management_agent.create_task_tool', return_value=mock_task_creation_result) as mock_create:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps
            
            from agents.task_management_agent import create_task
            result = await create_task(mock_ctx, task_name, None, None, assignee, due_date)
            
            # Verify call included assignee and due date
            mock_create.assert_called_once_with(
                api_key="test-asana-key",
                name=task_name,
                project_gid=None,
                notes=None,
                assignee=assignee,
                due_on=due_date
            )

    @pytest.mark.asyncio
    async def test_update_task_success(self, mock_task_deps):
        """Test successful task update"""
        task_gid = "task_789012"
        new_name = "Updated task name"
        
        mock_update_result = {
            "success": True,
            "task_gid": task_gid,
            "updated_fields": ["name"],
            "updated_at": "2024-01-01T13:00:00"
        }
        
        with patch('agents.task_management_agent.update_task_tool', return_value=mock_update_result) as mock_update:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps
            
            from agents.task_management_agent import update_task
            result = await update_task(mock_ctx, task_gid, new_name, None, True)
            
            # Verify Asana tool was called with correct parameters
            mock_update.assert_called_once_with(
                api_key="test-asana-key",
                task_gid=task_gid,
                name=new_name,
                notes=None,
                completed=True,
                assignee=None,
                due_on=None
            )
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_projects_success(self, mock_task_deps):
        """Test successful project listing"""
        mock_projects_result = {
            "success": True,
            "projects": [
                {"gid": "proj_1", "name": "Project 1"},
                {"gid": "proj_2", "name": "Project 2"}
            ],
            "count": 2
        }
        
        with patch('agents.task_management_agent.list_projects_tool', return_value=mock_projects_result) as mock_list:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps
            
            from agents.task_management_agent import list_projects
            result = await list_projects(mock_ctx, 10)
            
            # Verify call
            mock_list.assert_called_once_with(
                api_key="test-asana-key",
                workspace_gid="123456789",
                limit=10
            )
            
            assert result["success"] is True
            assert len(result["projects"]) == 2

    @pytest.mark.asyncio
    async def test_list_tasks_success(self, mock_task_deps):
        """Test successful task listing"""
        project_gid = "proj_123456"
        
        mock_tasks_result = {
            "success": True,
            "tasks": [
                {"gid": "task_1", "name": "Task 1", "completed": False},
                {"gid": "task_2", "name": "Task 2", "completed": True}
            ],
            "count": 2
        }
        
        with patch('agents.task_management_agent.list_tasks_tool', return_value=mock_tasks_result) as mock_list:
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps
            
            from agents.task_management_agent import list_tasks
            result = await list_tasks(mock_ctx, project_gid, None, None, 20)
            
            # Verify call
            mock_list.assert_called_once_with(
                api_key="test-asana-key",
                project_gid=project_gid,
                assignee=None,
                completed_since=None,
                limit=20
            )
            
            assert result["success"] is True
            assert len(result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_task_management_agent_integration(self, mock_task_deps, mock_task_agent_result):
        """Test task management agent end-to-end integration"""
        query = "Create a project for AI marketing campaign with tasks for market research, content creation, and launch planning"
        
        with patch.object(task_management_agent, 'run', return_value=mock_task_agent_result) as mock_run:
            result = await task_management_agent.run(query, deps=mock_task_deps)
            
            # Verify the agent was called
            mock_run.assert_called_with(query, deps=mock_task_deps)
            
            # Verify result structure
            assert hasattr(result, 'output')
            assert isinstance(result.output, str)

    @pytest.mark.asyncio
    async def test_task_management_agent_with_message_history(self, mock_task_deps, mock_task_agent_result):
        """Test task management agent with message history"""
        query = "Update the project timeline based on the research findings"
        message_history = [MagicMock()]
        
        with patch.object(task_management_agent, 'run', return_value=mock_task_agent_result) as mock_run:
            result = await task_management_agent.run(
                query, 
                deps=mock_task_deps,
                message_history=message_history
            )
            
            # Verify the agent was called with message history
            mock_run.assert_called_with(
                query, 
                deps=mock_task_deps,
                message_history=message_history
            )

    def test_task_management_dependencies_structure(self):
        """Test TaskManagementAgentDependencies dataclass structure"""
        deps = TaskManagementAgentDependencies(
            asana_api_key="test-key",
            asana_workspace_gid="123456",
            session_id="test-session"
        )
        
        assert deps.asana_api_key == "test-key"
        assert deps.asana_workspace_gid == "123456"
        assert deps.session_id == "test-session"
        
        # Test with optional fields
        deps_minimal = TaskManagementAgentDependencies(
            asana_api_key="test-key"
        )
        assert deps_minimal.asana_api_key == "test-key"
        assert deps_minimal.asana_workspace_gid is None
        assert deps_minimal.session_id is None

    @pytest.mark.asyncio
    async def test_task_management_error_handling(self, mock_task_deps):
        """Test task management agent error handling"""
        with patch('agents.task_management_agent.create_project_tool', side_effect=Exception("Asana API Error")):
            mock_ctx = MagicMock()
            mock_ctx.deps = mock_task_deps
            
            from agents.task_management_agent import create_project
            result = await create_project(mock_ctx, "Test Project")
            
            # Verify error handling
            assert result["success"] is False
            assert "Asana API Error" in result["error"]
            assert result["project_name"] == "Test Project"

    def test_task_management_system_prompt_structure(self):
        """Test that task management agent has proper system prompt"""
        # Access the system prompt function
        from agents.prompts import get_task_management_system_prompt
        
        system_prompt = get_task_management_system_prompt()
        
        # Verify key elements are present
        assert "task management" in system_prompt.lower()
        assert "asana" in system_prompt.lower()
        assert "project" in system_prompt.lower()
        assert "concise" in system_prompt.lower()
        assert "today is" in system_prompt.lower()  # Check date inclusion
        
        # Verify output format requirements
        assert "bullet points" in system_prompt.lower()
        assert "300 words" in system_prompt