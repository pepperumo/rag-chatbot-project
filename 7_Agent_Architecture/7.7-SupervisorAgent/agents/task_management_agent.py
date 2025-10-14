"""
Task Management Agent for project and task operations using Asana API.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from clients import get_model
from tools.asana_tools import (
    create_project_tool,
    list_projects_tool,
    get_project_details_tool,
    create_task_tool,
    update_task_tool,
    list_tasks_tool,
    get_workspace_info_tool
)
from .prompts import get_task_management_system_prompt

logger = logging.getLogger(__name__)




@dataclass
class TaskManagementAgentDependencies:
    """Dependencies for the task management agent - only configuration, no tool instances."""
    asana_api_key: str
    asana_workspace_gid: Optional[str] = None
    session_id: Optional[str] = None


# Initialize the task management agent
task_management_agent = Agent(
    get_model(),
    deps_type=TaskManagementAgentDependencies,
    system_prompt=get_task_management_system_prompt(),
    instrument=True
)


@task_management_agent.tool
async def get_workspace_info(
    ctx: RunContext[TaskManagementAgentDependencies]
) -> Dict[str, Any]:
    """
    Get workspace information for the authenticated user.
    
    Returns:
        Dictionary with workspace information
    """
    try:
        result = await get_workspace_info_tool(
            api_key=ctx.deps.asana_api_key
        )
        
        logger.info(f"Retrieved workspace info: {result.get('count', 0)} workspaces")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get workspace info: {e}")
        return {
            "success": False,
            "error": str(e),
            "workspaces": [],
            "count": 0
        }


@task_management_agent.tool
async def create_project(
    ctx: RunContext[TaskManagementAgentDependencies],
    name: str,
    notes: Optional[str] = None,
    public: bool = False
) -> Dict[str, Any]:
    """
    Create a new project in Asana.
    
    Args:
        name: Project name
        notes: Optional project description
        public: Whether project should be public (default False)
    
    Returns:
        Dictionary with project creation results
    """
    try:
        # Use configured workspace or get default workspace
        workspace_gid = ctx.deps.asana_workspace_gid
        
        if not workspace_gid:
            # Get first available workspace if not configured
            workspace_info = await get_workspace_info_tool(ctx.deps.asana_api_key)
            if workspace_info.get("success") and workspace_info.get("workspaces"):
                workspace_gid = workspace_info["workspaces"][0]["gid"]
            else:
                return {
                    "success": False,
                    "error": "No workspace available for project creation",
                    "project_name": name
                }
        
        result = await create_project_tool(
            api_key=ctx.deps.asana_api_key,
            name=name,
            workspace_gid=workspace_gid,
            notes=notes,
            public=public
        )
        
        logger.info(f"Project creation result: {result.get('success')}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_name": name
        }


@task_management_agent.tool
async def list_projects(
    ctx: RunContext[TaskManagementAgentDependencies],
    limit: int = 20
) -> Dict[str, Any]:
    """
    List projects in the workspace.
    
    Args:
        limit: Maximum number of projects to return (default 20)
    
    Returns:
        Dictionary with projects list
    """
    try:
        # Use configured workspace or get default workspace
        workspace_gid = ctx.deps.asana_workspace_gid
        
        if not workspace_gid:
            # Get first available workspace if not configured
            workspace_info = await get_workspace_info_tool(ctx.deps.asana_api_key)
            if workspace_info.get("success") and workspace_info.get("workspaces"):
                workspace_gid = workspace_info["workspaces"][0]["gid"]
            else:
                return {
                    "success": False,
                    "error": "No workspace available for listing projects",
                    "projects": [],
                    "count": 0
                }
        
        result = await list_projects_tool(
            api_key=ctx.deps.asana_api_key,
            workspace_gid=workspace_gid,
            limit=limit
        )
        
        logger.info(f"Listed {result.get('count', 0)} projects")
        return result
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return {
            "success": False,
            "error": str(e),
            "projects": [],
            "count": 0
        }


@task_management_agent.tool
async def get_project_details(
    ctx: RunContext[TaskManagementAgentDependencies],
    project_gid: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific project.
    
    Args:
        project_gid: Project GID to get details for
    
    Returns:
        Dictionary with project details
    """
    try:
        result = await get_project_details_tool(
            api_key=ctx.deps.asana_api_key,
            project_gid=project_gid
        )
        
        logger.info(f"Retrieved project details for: {project_gid}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get project details: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_gid": project_gid
        }


@task_management_agent.tool
async def create_task(
    ctx: RunContext[TaskManagementAgentDependencies],
    name: str,
    project_gid: Optional[str] = None,
    notes: Optional[str] = None,
    assignee: Optional[str] = None,
    due_on: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new task in Asana.
    
    Args:
        name: Task name
        project_gid: Optional project GID to add task to
        notes: Optional task description
        assignee: Optional assignee email or GID
        due_on: Optional due date in YYYY-MM-DD format
    
    Returns:
        Dictionary with task creation results
    """
    try:
        result = await create_task_tool(
            api_key=ctx.deps.asana_api_key,
            name=name,
            project_gid=project_gid,
            notes=notes,
            assignee=assignee,
            due_on=due_on
        )
        
        logger.info(f"Task creation result: {result.get('success')}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        return {
            "success": False,
            "error": str(e),
            "task_name": name
        }


@task_management_agent.tool
async def update_task(
    ctx: RunContext[TaskManagementAgentDependencies],
    task_gid: str,
    name: Optional[str] = None,
    notes: Optional[str] = None,
    completed: Optional[bool] = None,
    assignee: Optional[str] = None,
    due_on: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing task in Asana.
    
    Args:
        task_gid: Task GID to update
        name: Optional new task name
        notes: Optional new task description
        completed: Optional completion status
        assignee: Optional new assignee email or GID
        due_on: Optional new due date in YYYY-MM-DD format
    
    Returns:
        Dictionary with task update results
    """
    try:
        result = await update_task_tool(
            api_key=ctx.deps.asana_api_key,
            task_gid=task_gid,
            name=name,
            notes=notes,
            completed=completed,
            assignee=assignee,
            due_on=due_on
        )
        
        logger.info(f"Task update result: {result.get('success')}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update task: {e}")
        return {
            "success": False,
            "error": str(e),
            "task_gid": task_gid
        }


@task_management_agent.tool
async def list_tasks(
    ctx: RunContext[TaskManagementAgentDependencies],
    project_gid: Optional[str] = None,
    assignee: Optional[str] = None,
    completed_since: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List tasks from a project or for an assignee.
    
    Args:
        project_gid: Optional project GID to filter tasks
        assignee: Optional assignee email or GID to filter tasks
        completed_since: Optional date to filter completed tasks (YYYY-MM-DD)
        limit: Maximum number of tasks to return (default 20)
    
    Returns:
        Dictionary with tasks list
    """
    try:
        result = await list_tasks_tool(
            api_key=ctx.deps.asana_api_key,
            project_gid=project_gid,
            assignee=assignee,
            completed_since=completed_since,
            limit=limit
        )
        
        logger.info(f"Listed {result.get('count', 0)} tasks")
        return result
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        return {
            "success": False,
            "error": str(e),
            "tasks": [],
            "count": 0
        }


# Convenience function to create task management agent with dependencies
def create_task_management_agent(
    asana_api_key: str,
    asana_workspace_gid: Optional[str] = None,
    session_id: Optional[str] = None
) -> Agent:
    """
    Create a task management agent with specified dependencies.
    
    Args:
        asana_api_key: Asana API key
        asana_workspace_gid: Optional workspace GID
        session_id: Optional session identifier
        
    Returns:
        Configured task management agent
    """
    return task_management_agent