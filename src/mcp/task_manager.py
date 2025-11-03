"""Task Master - Task management and PRD parsing for project management."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""
    BACKLOG = "backlog"
    IN_PROGRESS = "in-progress"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task data structure."""
    id: str
    description: str
    status: TaskStatus = TaskStatus.BACKLOG
    dependencies: List[str] = None
    subtasks: List[str] = None
    priority: int = 0
    created_at: str = None
    updated_at: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.subtasks is None:
            self.subtasks = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "dependencies": self.dependencies,
            "subtasks": self.subtasks,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            status=TaskStatus(data.get("status", "backlog")),
            dependencies=data.get("dependencies", []),
            subtasks=data.get("subtasks", []),
            priority=data.get("priority", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            metadata=data.get("metadata", {})
        )


class TaskManager:
    """Manages tasks with persistent storage in .taskmaster directory."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize Task Manager.
        
        Args:
            project_root: Root directory for project (defaults to current working directory)
        """
        if project_root is None:
            project_root = Path.cwd()
        
        self.project_root = Path(project_root)
        self.taskmaster_dir = self.project_root / ".taskmaster"
        self.taskmaster_dir.mkdir(exist_ok=True)
        
        self.tasks_file = self.taskmaster_dir / "tasks.json"
        self.tasks: Dict[str, Task] = {}
        
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from persistent storage."""
        if not self.tasks_file.exists():
            logger.info(f"Tasks file not found at {self.tasks_file}, starting with empty task list")
            self.tasks = {}
            return
        
        try:
            with open(self.tasks_file, 'r') as f:
                data = json.load(f)
            
            self.tasks = {}
            for task_data in data.get("tasks", []):
                task = Task.from_dict(task_data)
                self.tasks[task.id] = task
            
            logger.info(f"Loaded {len(self.tasks)} tasks from {self.tasks_file}")
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            self.tasks = {}
    
    def _save_tasks(self):
        """Save tasks to persistent storage."""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "tasks": [task.to_dict() for task in self.tasks.values()]
            }
            
            with open(self.tasks_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.tasks)} tasks to {self.tasks_file}")
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
            raise
    
    def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        include_done: bool = True
    ) -> List[Task]:
        """
        Get all tasks, optionally filtered by status.
        
        Args:
            status: Filter by status
            include_done: Whether to include done tasks
            
        Returns:
            List of tasks
        """
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if not include_done:
            tasks = [t for t in tasks if t.status != TaskStatus.DONE]
        
        # Sort by priority (higher first), then by created_at
        tasks.sort(key=lambda t: (-t.priority, t.created_at))
        
        return tasks
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID."""
        return self.tasks.get(task_id)
    
    def add_task(
        self,
        description: str,
        task_id: Optional[str] = None,
        status: TaskStatus = TaskStatus.BACKLOG,
        dependencies: Optional[List[str]] = None,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Add a new task.
        
        Args:
            description: Task description
            task_id: Optional task ID (auto-generated if not provided)
            status: Initial status
            dependencies: List of task IDs this task depends on
            priority: Priority (higher = more important)
            metadata: Additional metadata
            
        Returns:
            Created task
        """
        if task_id is None:
            # Generate ID from description
            task_id = f"task-{len(self.tasks) + 1}"
        
        if task_id in self.tasks:
            raise ValueError(f"Task with ID {task_id} already exists")
        
        task = Task(
            id=task_id,
            description=description,
            status=status,
            dependencies=dependencies or [],
            priority=priority,
            metadata=metadata or {}
        )
        
        self.tasks[task.id] = task
        self._save_tasks()
        
        logger.info(f"Added task: {task.id} - {description}")
        return task
    
    def update_task(
        self,
        task_id: str,
        description: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        dependencies: Optional[List[str]] = None,
        priority: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Update an existing task.
        
        Args:
            task_id: Task ID
            description: New description
            status: New status
            dependencies: New dependencies
            priority: New priority
            metadata: Metadata to merge (shallow merge)
            
        Returns:
            Updated task
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status
        if dependencies is not None:
            task.dependencies = dependencies
        if priority is not None:
            task.priority = priority
        if metadata is not None:
            task.metadata.update(metadata)
        
        task.updated_at = datetime.now().isoformat()
        self._save_tasks()
        
        logger.info(f"Updated task: {task_id}")
        return task
    
    def set_task_status(self, task_id: str, status: TaskStatus) -> Task:
        """Set task status."""
        return self.update_task(task_id, status=status)
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was removed, False if not found
        """
        if task_id not in self.tasks:
            return False
        
        # Check if other tasks depend on this one
        dependent_tasks = [
            t for t in self.tasks.values()
            if task_id in t.dependencies
        ]
        
        if dependent_tasks:
            dep_ids = [t.id for t in dependent_tasks]
            raise ValueError(
                f"Cannot remove task {task_id}: other tasks depend on it: {dep_ids}"
            )
        
        del self.tasks[task_id]
        self._save_tasks()
        
        logger.info(f"Removed task: {task_id}")
        return True
    
    def next_task(self) -> Optional[Task]:
        """
        Get the next highest-priority task that is ready to work on.
        A task is ready if:
        1. Status is BACKLOG or BLOCKED
        2. All dependencies are DONE
        
        Returns:
            Next task to work on, or None if no tasks are ready
        """
        backlog_tasks = [
            t for t in self.tasks.values()
            if t.status in (TaskStatus.BACKLOG, TaskStatus.BLOCKED)
        ]
        
        if not backlog_tasks:
            return None
        
        # Filter tasks whose dependencies are all done
        ready_tasks = []
        for task in backlog_tasks:
            if not task.dependencies:
                ready_tasks.append(task)
            else:
                all_deps_done = all(
                    dep_id in self.tasks
                    and self.tasks[dep_id].status == TaskStatus.DONE
                    for dep_id in task.dependencies
                )
                if all_deps_done:
                    ready_tasks.append(task)
        
        if not ready_tasks:
            return None
        
        # Sort by priority (higher first), then by created_at
        ready_tasks.sort(key=lambda t: (-t.priority, t.created_at))
        return ready_tasks[0]
    
    def validate_dependencies(self) -> Dict[str, Any]:
        """
        Validate task dependencies.
        
        Returns:
            Validation result with any issues found
        """
        issues = {
            "circular_dependencies": [],
            "missing_dependencies": [],
            "orphaned_tasks": []
        }
        
        # Check for missing dependencies
        all_task_ids = set(self.tasks.keys())
        for task in self.tasks.values():
            for dep_id in task.dependencies:
                if dep_id not in all_task_ids:
                    issues["missing_dependencies"].append({
                        "task": task.id,
                        "missing_dependency": dep_id
                    })
        
        # Check for circular dependencies (simple DFS)
        def has_cycle(task_id: str, visited: set, rec_stack: set) -> Optional[List[str]]:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if dep_id not in visited:
                        cycle = has_cycle(dep_id, visited, rec_stack)
                        if cycle:
                            return [task_id] + cycle
                    elif dep_id in rec_stack:
                        return [task_id, dep_id]
            
            rec_stack.remove(task_id)
            return None
        
        visited = set()
        for task_id in self.tasks.keys():
            if task_id not in visited:
                cycle = has_cycle(task_id, visited, set())
                if cycle:
                    issues["circular_dependencies"].append(cycle)
        
        # Check for orphaned tasks (no dependencies, no dependents, not done)
        for task in self.tasks.values():
            if task.status != TaskStatus.DONE:
                has_dependents = any(
                    task.id in t.dependencies
                    for t in self.tasks.values()
                )
                if not task.dependencies and not has_dependents:
                    issues["orphaned_tasks"].append(task.id)
        
        is_valid = (
            len(issues["circular_dependencies"]) == 0
            and len(issues["missing_dependencies"]) == 0
        )
        
        return {
            "valid": is_valid,
            "issues": issues,
            "total_tasks": len(self.tasks),
            "tasks_by_status": {
                status.value: len([t for t in self.tasks.values() if t.status == status])
                for status in TaskStatus
            }
        }
    
    def expand_task(self, task_id: str, subtasks: List[str]) -> Task:
        """
        Expand a task into subtasks.
        
        Args:
            task_id: Parent task ID
            subtasks: List of subtask descriptions
            
        Returns:
            Updated parent task with subtasks
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Create subtasks
        subtask_ids = []
        for i, subtask_desc in enumerate(subtasks):
            subtask_id = f"{task_id}-{i+1}"
            subtask = self.add_task(
                description=subtask_desc,
                task_id=subtask_id,
                status=TaskStatus.BACKLOG,
                dependencies=[task_id],  # Subtasks depend on parent
                priority=task.priority
            )
            subtask_ids.append(subtask_id)
        
        # Update parent task
        task.subtasks = subtask_ids
        task.updated_at = datetime.now().isoformat()
        self._save_tasks()
        
        return task