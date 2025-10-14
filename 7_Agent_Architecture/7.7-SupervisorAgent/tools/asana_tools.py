"""
Asana API tool functions for the supervisor agent system.

These are standalone async functions for project and task management operations
with intelligent workspace detection, team handling, and permission fallbacks.

✅ ALL TOOLS VERIFIED WORKING with Asana Python SDK v5.2.0

Key Features:
- Auto-detects accessible workspaces when none specified
- Handles organization vs workspace differences automatically  
- Uses team-specific APIs when required (missing team field errors)
- Intelligent fallback for 403 permission errors
- Comprehensive error handling and logging

Example Usage:
```python
# Get workspace info (always works)
workspaces = await get_workspace_info_tool(api_key)

# List projects with auto-detection  
projects = await list_projects_tool(api_key, workspace_gid=None)

# Create project with team auto-detection
project = await create_project_tool(
    api_key=api_key,
    name="AI Research Project", 
    workspace_gid=None,  # Auto-detects
    notes="Research latest AI developments"
)

# Create and manage tasks
task = await create_task_tool(
    api_key=api_key,
    name="Research task",
    project_gid=project["project_gid"],
    due_on="2024-12-31"
)

# Update task completion
await update_task_tool(
    api_key=api_key,
    task_gid=task["task_gid"],
    completed=True
)
```

All tools handle workspace permissions and team requirements automatically.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
import asana

logger = logging.getLogger(__name__)


def _create_asana_client(api_key: str) -> asana.ApiClient:
    """
    Create and configure Asana API client.
    
    Args:
        api_key: Asana personal access token
        
    Returns:
        Configured Asana API client
        
    Raises:
        ValueError: If API key is missing
        Exception: If client creation fails
    """
    if not api_key or not api_key.strip():
        raise ValueError("Asana API key is required")
    
    try:
        configuration = asana.Configuration()
        configuration.access_token = api_key
        return asana.ApiClient(configuration)
    except Exception as e:
        logger.error(f"Failed to create Asana client: {e}")
        raise Exception(f"Asana client creation failed: {str(e)}")


async def get_workspace_info_tool(api_key: str) -> Dict[str, Any]:
    """
    Get workspace information for the authenticated user.
    
    Args:
        api_key: Asana personal access token
        
    Returns:
        Dictionary with workspace information
        
    Raises:
        ValueError: If API key is missing
        Exception: If API request fails
    """
    if not api_key or not api_key.strip():
        raise ValueError("Asana API key is required")
    
    logger.info("Getting Asana workspace information")
    
    try:
        api_client = _create_asana_client(api_key)
        workspaces_api = asana.WorkspacesApi(api_client)
        
        # Use asyncio.to_thread for sync API calls with required opts parameter
        opts = {
            'opt_fields': 'gid,name,resource_type,is_organization,email_domains'
        }
        workspaces = await asyncio.to_thread(workspaces_api.get_workspaces, opts)
        
        workspace_list = []
        for workspace in workspaces:
            workspace_list.append({
                "gid": workspace.get("gid"),
                "name": workspace.get("name"),
                "resource_type": workspace.get("resource_type")
            })
        
        logger.info(f"Found {len(workspace_list)} workspaces")
        return {
            "success": True,
            "workspaces": workspace_list,
            "count": len(workspace_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to get workspace info: {e}")
        return {
            "success": False,
            "error": str(e),
            "workspaces": [],
            "count": 0
        }


async def get_teams_for_workspace_tool(api_key: str, workspace_gid: str) -> Dict[str, Any]:
    """
    Get teams for a specific workspace.
    
    Args:
        api_key: Asana personal access token
        workspace_gid: Workspace GID to get teams from
        
    Returns:
        Dictionary with teams information
        
    Raises:
        ValueError: If API key is missing
        Exception: If API request fails
    """
    if not api_key or not api_key.strip():
        raise ValueError("Asana API key is required")
    
    if not workspace_gid or not workspace_gid.strip():
        raise ValueError("Workspace GID is required")
    
    logger.info(f"Getting teams for workspace: {workspace_gid}")
    
    try:
        api_client = _create_asana_client(api_key)
        teams_api = asana.TeamsApi(api_client)
        
        # Get teams for workspace using sync API with asyncio.to_thread
        opts = {
            'workspace': workspace_gid,
            'opt_fields': 'gid,name,description,resource_type'
        }
        teams = await asyncio.to_thread(teams_api.get_teams_for_workspace, workspace_gid, opts)
        
        team_list = []
        for team in teams:
            team_list.append({
                "gid": team.get("gid"),
                "name": team.get("name"),
                "description": team.get("description"),
                "resource_type": team.get("resource_type")
            })
        
        logger.info(f"Found {len(team_list)} teams")
        return {
            "success": True,
            "teams": team_list,
            "count": len(team_list),
            "workspace_gid": workspace_gid
        }
        
    except Exception as e:
        logger.error(f"Failed to get teams: {e}")
        return {
            "success": False,
            "error": str(e),
            "teams": [],
            "count": 0,
            "workspace_gid": workspace_gid
        }


async def create_project_tool(
    api_key: str,
    name: str,
    workspace_gid: Optional[str] = None,
    notes: Optional[str] = None,
    public: bool = False
) -> Dict[str, Any]:
    """
    Create a new project in Asana.
    
    Args:
        api_key: Asana personal access token
        name: Project name
        workspace_gid: Optional workspace GID where project will be created (auto-detects if None)
        notes: Optional project description
        public: Whether project should be public (default False)
        
    Returns:
        Dictionary with project creation results
        
    Raises:
        ValueError: If required parameters are missing
        Exception: If API request fails
    """
    if not api_key or not api_key.strip():
        raise ValueError("Asana API key is required")
    
    if not name or not name.strip():
        raise ValueError("Project name is required")
    
    # Auto-detect workspace if not provided
    if not workspace_gid or not workspace_gid.strip():
        logger.info("No workspace GID provided, auto-detecting from available workspaces...")
        workspace_info = await get_workspace_info_tool(api_key)
        if workspace_info.get("success") and workspace_info.get("workspaces"):
            workspace_gid = workspace_info["workspaces"][0]["gid"]
            logger.info(f"Using auto-detected workspace: {workspace_gid}")
        else:
            raise ValueError("Unable to auto-detect workspace GID")
    
    logger.info(f"Creating Asana project: {name}")
    
    try:
        api_client = _create_asana_client(api_key)
        projects_api = asana.ProjectsApi(api_client)
        
        # Prepare project data
        project_data = {
            "name": name,
            "workspace": workspace_gid,
            "public": public
        }
        
        if notes:
            project_data["notes"] = notes
        
        # Create project using sync API with asyncio.to_thread
        body = {"data": project_data}
        opts = {
            'opt_fields': 'gid,name,permalink_url,created_at,modified_at,public'
        }
        
        try:
            # Try direct project creation first
            project = await asyncio.to_thread(projects_api.create_project, body, opts)
        except Exception as create_error:
            # If team field is required, try getting teams and using create_project_for_team
            if "team" in str(create_error).lower():
                logger.info("Direct project creation failed due to team requirement, trying team-based creation...")
                
                # Get teams for this workspace
                teams_result = await get_teams_for_workspace_tool(api_key, workspace_gid)
                if teams_result.get("success") and teams_result.get("teams"):
                    # Use the first available team
                    team_gid = teams_result["teams"][0]["gid"]
                    team_name = teams_result["teams"][0]["name"]
                    logger.info(f"Using team: {team_name} ({team_gid})")
                    
                    # Create project for team using the team-specific API
                    project = await asyncio.to_thread(projects_api.create_project_for_team, body, team_gid, opts)
                    
                    result = {
                        "success": True,
                        "project_gid": project.get("gid"),
                        "project_name": project.get("name"),
                        "project_url": project.get("permalink_url"),
                        "workspace_gid": workspace_gid,
                        "team_gid": team_gid,
                        "team_name": team_name,
                        "public": public,
                        "used_team_api": True
                    }
                    
                    logger.info(f"Project created successfully using team API: {result['project_gid']}")
                    return result
                else:
                    # Re-raise the original error if no teams found
                    raise create_error
            else:
                # Re-raise for other types of errors
                raise create_error
        
        result = {
            "success": True,
            "project_gid": project.get("gid"),
            "project_name": project.get("name"),
            "project_url": project.get("permalink_url"),
            "workspace_gid": workspace_gid,
            "public": public
        }
        
        logger.info(f"Project created successfully: {result['project_gid']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        
        # If 403 error and auto-detection available, try other workspaces
        if "403" in str(e) or "Forbidden" in str(e):
            logger.warning(f"Access forbidden for workspace {workspace_gid}, trying other workspaces...")
            workspace_info = await get_workspace_info_tool(api_key)
            if workspace_info.get("success") and workspace_info.get("workspaces"):
                for workspace in workspace_info["workspaces"]:
                    if workspace["gid"] != workspace_gid:
                        try:
                            logger.info(f"Trying workspace: {workspace['name']} ({workspace['gid']})")
                            project_data["workspace"] = workspace["gid"]
                            body = {"data": project_data}
                            project = await asyncio.to_thread(projects_api.create_project, body, opts)
                            
                            result = {
                                "success": True,
                                "project_gid": project.get("gid"),
                                "project_name": project.get("name"),
                                "project_url": project.get("permalink_url"),
                                "workspace_gid": workspace["gid"],
                                "workspace_name": workspace["name"],
                                "public": public,
                                "fallback_workspace": True
                            }
                            
                            logger.info(f"SUCCESS: Project created in workspace {workspace['name']}")
                            return result
                        except Exception as retry_error:
                            logger.warning(f"Also failed for workspace {workspace['name']}: {retry_error}")
                            continue
        
        return {
            "success": False,
            "error": str(e),
            "project_name": name,
            "workspace_gid": workspace_gid,
            "suggestion": "Check workspace permissions or try a different workspace GID"
        }


async def list_projects_tool(
    api_key: str,
    workspace_gid: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List projects in a workspace.
    
    Args:
        api_key: Asana personal access token
        workspace_gid: Optional workspace GID to list projects from (auto-detects if None)
        limit: Maximum number of projects to return (default 20)
        
    Returns:
        Dictionary with projects list
        
    Raises:
        ValueError: If required parameters are missing
        Exception: If API request fails
    """
    if not api_key or not api_key.strip():
        raise ValueError("Asana API key is required")
    
    # Auto-detect workspace if not provided
    if not workspace_gid or not workspace_gid.strip():
        logger.info("No workspace GID provided, auto-detecting from available workspaces...")
        workspace_info = await get_workspace_info_tool(api_key)
        if workspace_info.get("success") and workspace_info.get("workspaces"):
            workspace_gid = workspace_info["workspaces"][0]["gid"]
            logger.info(f"Using auto-detected workspace: {workspace_gid}")
        else:
            raise ValueError("Unable to auto-detect workspace GID")
    
    # Ensure limit is within reasonable range
    limit = min(max(limit, 1), 100)
    
    logger.info(f"Listing projects from workspace: {workspace_gid}")
    
    try:
        api_client = _create_asana_client(api_key)
        projects_api = asana.ProjectsApi(api_client)
        
        # Get projects using sync API with asyncio.to_thread
        opts = {
            'workspace': workspace_gid,
            'limit': limit,
            'opt_fields': 'gid,name,resource_type,permalink_url,created_at,modified_at'
        }
        projects = await asyncio.to_thread(projects_api.get_projects, opts)
        
        project_list = []
        for project in projects:
            project_list.append({
                "gid": project.get("gid"),
                "name": project.get("name"),
                "resource_type": project.get("resource_type"),
                "permalink_url": project.get("permalink_url")
            })
        
        logger.info(f"Found {len(project_list)} projects")
        return {
            "success": True,
            "projects": project_list,
            "count": len(project_list),
            "workspace_gid": workspace_gid
        }
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        
        # If 403 error and auto-detection available, try other workspaces
        if "403" in str(e) or "Forbidden" in str(e):
            logger.warning(f"Access forbidden for workspace {workspace_gid}, trying other workspaces...")
            workspace_info = await get_workspace_info_tool(api_key)
            if workspace_info.get("success") and workspace_info.get("workspaces"):
                for workspace in workspace_info["workspaces"]:
                    if workspace["gid"] != workspace_gid:
                        try:
                            logger.info(f"Trying workspace: {workspace['name']} ({workspace['gid']})")
                            opts['workspace'] = workspace["gid"]
                            projects = await asyncio.to_thread(projects_api.get_projects, opts)
                            
                            project_list = []
                            for project in projects:
                                project_list.append({
                                    "gid": project.get("gid"),
                                    "name": project.get("name"),
                                    "resource_type": project.get("resource_type"),
                                    "permalink_url": project.get("permalink_url")
                                })
                            
                            logger.info(f"SUCCESS: Found {len(project_list)} projects in workspace {workspace['name']}")
                            return {
                                "success": True,
                                "projects": project_list,
                                "count": len(project_list),
                                "workspace_gid": workspace["gid"],
                                "workspace_name": workspace["name"],
                                "fallback_workspace": True
                            }
                        except Exception as retry_error:
                            logger.warning(f"Also failed for workspace {workspace['name']}: {retry_error}")
                            continue
        
        return {
            "success": False,
            "error": str(e),
            "projects": [],
            "count": 0,
            "workspace_gid": workspace_gid,
            "suggestion": "Check workspace permissions or try a different workspace GID"
        }


async def get_project_details_tool(
    api_key: str,
    project_gid: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific project.
    
    Args:
        api_key: Asana personal access token
        project_gid: Project GID to get details for
        
    Returns:
        Dictionary with project details
        
    Raises:
        ValueError: If required parameters are missing
        Exception: If API request fails
    """
    if not api_key or not api_key.strip():
        raise ValueError("Asana API key is required")
    
    if not project_gid or not project_gid.strip():
        raise ValueError("Project GID is required")
    
    logger.info(f"Getting project details: {project_gid}")
    
    try:
        api_client = _create_asana_client(api_key)
        projects_api = asana.ProjectsApi(api_client)
        
        # Get project details using sync API with asyncio.to_thread
        opts = {
            'opt_fields': 'gid,name,notes,public,created_at,modified_at,permalink_url,resource_type,team'
        }
        project = await asyncio.to_thread(projects_api.get_project, project_gid, opts)
        
        result = {
            "success": True,
            "gid": project.get("gid"),
            "name": project.get("name"),
            "notes": project.get("notes"),
            "public": project.get("public", False),
            "created_at": project.get("created_at"),
            "modified_at": project.get("modified_at"),
            "permalink_url": project.get("permalink_url"),
            "resource_type": project.get("resource_type")
        }
        
        logger.info(f"Retrieved project details: {result['name']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get project details: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_gid": project_gid
        }


async def create_task_tool(
    api_key: str,
    name: str,
    project_gid: Optional[str] = None,
    notes: Optional[str] = None,
    assignee: Optional[str] = None,
    due_on: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new task in Asana.
    
    Args:
        api_key: Asana personal access token
        name: Task name
        project_gid: Optional project GID to add task to
        notes: Optional task description
        assignee: Optional assignee email or GID
        due_on: Optional due date in YYYY-MM-DD format
        
    Returns:
        Dictionary with task creation results
        
    Raises:
        ValueError: If required parameters are missing
        Exception: If API request fails
    """
    if not api_key or not api_key.strip():
        raise ValueError("Asana API key is required")
    
    if not name or not name.strip():
        raise ValueError("Task name is required")
    
    logger.info(f"Creating Asana task: {name}")
    
    try:
        api_client = _create_asana_client(api_key)
        tasks_api = asana.TasksApi(api_client)
        
        # Prepare task data
        task_data = {
            "name": name
        }
        
        if notes:
            task_data["notes"] = notes
        
        if assignee:
            task_data["assignee"] = assignee
        
        if due_on:
            task_data["due_on"] = due_on
        
        if project_gid:
            task_data["projects"] = [project_gid]
        
        # Create task using sync API with asyncio.to_thread
        body = {"data": task_data}
        opts = {
            'opt_fields': 'gid,name,permalink_url,created_at,modified_at,completed,assignee,due_on'
        }
        task = await asyncio.to_thread(tasks_api.create_task, body, opts)
        
        result = {
            "success": True,
            "task_gid": task.get("gid"),
            "task_name": task.get("name"),
            "permalink_url": task.get("permalink_url"),
            "created_at": task.get("created_at"),
            "project_gid": project_gid
        }
        
        logger.info(f"Task created successfully: {result['task_gid']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        return {
            "success": False,
            "error": str(e),
            "task_name": name,
            "project_gid": project_gid
        }


async def update_task_tool(
    api_key: str,
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
        api_key: Asana personal access token
        task_gid: Task GID to update
        name: Optional new task name
        notes: Optional new task description
        completed: Optional completion status
        assignee: Optional new assignee email or GID
        due_on: Optional new due date in YYYY-MM-DD format
        
    Returns:
        Dictionary with task update results
        
    Raises:
        ValueError: If required parameters are missing
        Exception: If API request fails
    """
    if not api_key or not api_key.strip():
        raise ValueError("Asana API key is required")
    
    if not task_gid or not task_gid.strip():
        raise ValueError("Task GID is required")
    
    logger.info(f"Updating Asana task: {task_gid}")
    
    try:
        api_client = _create_asana_client(api_key)
        tasks_api = asana.TasksApi(api_client)
        
        # Prepare update data - only include fields that are being updated
        update_data = {}
        
        if name is not None:
            update_data["name"] = name
        
        if notes is not None:
            update_data["notes"] = notes
        
        if completed is not None:
            update_data["completed"] = completed
        
        if assignee is not None:
            update_data["assignee"] = assignee
        
        if due_on is not None:
            update_data["due_on"] = due_on
        
        if not update_data:
            return {
                "success": False,
                "error": "No update fields provided",
                "task_gid": task_gid
            }
        
        # Update task using sync API with asyncio.to_thread
        body = {"data": update_data}
        opts = {
            'opt_fields': 'gid,name,completed,modified_at,assignee,due_on,notes'
        }
        task = await asyncio.to_thread(tasks_api.update_task, body, task_gid, opts)
        
        result = {
            "success": True,
            "task_gid": task.get("gid"),
            "task_name": task.get("name"),
            "completed": task.get("completed", False),
            "modified_at": task.get("modified_at"),
            "updated_fields": list(update_data.keys())
        }
        
        logger.info(f"Task updated successfully: {result['task_gid']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update task: {e}")
        return {
            "success": False,
            "error": str(e),
            "task_gid": task_gid
        }


async def list_tasks_tool(
    api_key: str,
    project_gid: Optional[str] = None,
    assignee: Optional[str] = None,
    completed_since: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List tasks from a project or for an assignee.
    
    Args:
        api_key: Asana personal access token
        project_gid: Optional project GID to filter tasks
        assignee: Optional assignee email or GID to filter tasks
        completed_since: Optional date to filter completed tasks (YYYY-MM-DD)
        limit: Maximum number of tasks to return (default 20)
        
    Returns:
        Dictionary with tasks list
        
    Raises:
        ValueError: If required parameters are missing
        Exception: If API request fails
    """
    if not api_key or not api_key.strip():
        raise ValueError("Asana API key is required")
    
    # Ensure limit is within reasonable range
    limit = min(max(limit, 1), 100)
    
    logger.info(f"Listing tasks with filters - project: {project_gid}, assignee: {assignee}")
    
    try:
        api_client = _create_asana_client(api_key)
        tasks_api = asana.TasksApi(api_client)
        
        # Prepare opts parameters for Asana SDK v5.2.0
        opts = {
            "limit": limit,
            'opt_fields': 'gid,name,completed,assignee,due_on,created_at,modified_at,permalink_url,resource_type'
        }
        
        if project_gid:
            opts["project"] = project_gid
        
        if assignee:
            opts["assignee"] = assignee
        
        if completed_since:
            opts["completed_since"] = completed_since
        
        # Get tasks using sync API with asyncio.to_thread
        tasks = await asyncio.to_thread(tasks_api.get_tasks, opts)
        
        task_list = []
        for task in tasks:
            task_list.append({
                "gid": task.get("gid"),
                "name": task.get("name"),
                "completed": task.get("completed", False),
                "assignee": task.get("assignee"),
                "due_on": task.get("due_on"),
                "created_at": task.get("created_at"),
                "modified_at": task.get("modified_at"),
                "permalink_url": task.get("permalink_url"),
                "resource_type": task.get("resource_type")
            })
        
        logger.info(f"Found {len(task_list)} tasks")
        return {
            "success": True,
            "tasks": task_list,
            "count": len(task_list),
            "filters": {
                "project_gid": project_gid,
                "assignee": assignee,
                "completed_since": completed_since
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        return {
            "success": False,
            "error": str(e),
            "tasks": [],
            "count": 0,
            "filters": {
                "project_gid": project_gid,
                "assignee": assignee,
                "completed_since": completed_since
            }
        }