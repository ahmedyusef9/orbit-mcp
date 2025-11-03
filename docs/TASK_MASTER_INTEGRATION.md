# Task Master MCP Integration

## Overview

Task Master is an AI-powered project management system integrated into the MCP server. It provides structured task management, PRD parsing, dependency tracking, and task expansion capabilities that work seamlessly with Cursor and other MCP-compatible AI assistants.

## Features

### Task Management
- ? Create, read, update, and delete tasks
- ? Task status tracking (backlog, in-progress, done, blocked, cancelled)
- ? Priority-based task ordering
- ? Dependency management
- ? Subtask support
- ? Persistent storage in `.taskmaster/` directory

### PRD Parsing
- ? Parse Product Requirements Documents (PRD) using LLM
- ? Automatically generate structured task breakdowns
- ? Extract dependencies and priorities
- ? Create subtasks automatically

### Task Expansion
- ? Break down complex tasks into actionable subtasks
- ? Optional research integration for context gathering
- ? Smart task decomposition using AI

### Dependency Management
- ? Circular dependency detection
- ? Missing dependency validation
- ? Automatic task ordering based on dependencies
- ? Next task suggestion (highest priority, dependencies satisfied)

## Quick Start

### 1. Configure LLM Providers

Task Master requires LLM configuration for PRD parsing and task expansion. Add to your `~/.mcp/config.yaml`:

```yaml
llm:
  default_provider: anthropic  # or openai, ollama
  
  providers:
    anthropic:
      enabled: true
      model: claude-3-sonnet
      api_key: ${ANTHROPIC_API_KEY}
    
    openai:
      enabled: true
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
    
    ollama:
      enabled: true
      model: llama2
      base_url: http://localhost:11434
```

### 2. Configure Cursor

Create or update `~/.cursor/mcp_config.json` (or `%APPDATA%\Cursor\mcp_config.json` on Windows):

```json
{
  "mcpServers": {
    "task-master": {
      "command": "mcp-server",
      "args": ["--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      }
    }
  }
}
```

### 3. Restart Cursor

Cursor will automatically detect and connect to the Task Master MCP server.

## Usage Examples

### Parse a PRD

In Cursor, you can ask:

```
Parse the PRD file and create tasks
```

Or be more specific:

```
Parse prd.txt and generate a task breakdown
```

The AI will:
1. Call `parse_prd` with the PRD path
2. Use LLM to analyze the PRD
3. Generate structured tasks with dependencies
4. Store them in `.taskmaster/tasks.json`

### Get Next Task

```
What should I work on next?
```

or

```
What's the next task?
```

The AI will call `next_task` to find the highest-priority task with all dependencies satisfied.

### Add a Task

```
Add a task to implement user authentication with high priority
```

or directly:

```
add_task: Implement user authentication, priority 8
```

### Update Task Status

```
Mark task-3 as done
```

```
Set task-5 to in-progress
```

### List Tasks

```
Show me all tasks
```

```
What tasks are in the backlog?
```

```
List all done tasks
```

### Expand a Task

```
Break down task-7 into subtasks
```

```
Expand task-12 with research on best practices
```

### Validate Dependencies

```
Check if task dependencies are valid
```

```
Validate the task dependency graph
```

## Available Tools

### `parse_prd`
Parse a Product Requirements Document and generate structured tasks.

**Parameters:**
- `prd_path` (required): Path to PRD file (e.g., `prd.txt`, `prd.md`)
- `provider` (optional): LLM provider to use (`anthropic`, `openai`, `ollama`)

**Example:**
```json
{
  "name": "parse_prd",
  "arguments": {
    "prd_path": "prd.txt",
    "provider": "anthropic"
  }
}
```

### `get_tasks`
Get all tasks, optionally filtered by status.

**Parameters:**
- `status` (optional): Filter by status (`backlog`, `in-progress`, `done`, `blocked`, `cancelled`)
- `include_done` (optional): Whether to include completed tasks (default: `true`)

### `get_task`
Get details of a specific task.

**Parameters:**
- `task_id` (required): Task ID

### `add_task`
Add a new task to the task list.

**Parameters:**
- `description` (required): Task description
- `task_id` (optional): Task ID (auto-generated if not provided)
- `status` (optional): Initial status (default: `backlog`)
- `dependencies` (optional): List of task IDs this task depends on
- `priority` (optional): Priority 0-10 (default: `0`)

### `set_task_status`
Update the status of a task.

**Parameters:**
- `task_id` (required): Task ID
- `status` (required): New status

### `remove_task`
Remove a task from the task list.

**Parameters:**
- `task_id` (required): Task ID to remove

### `next_task`
Get the next highest-priority task ready to work on (dependencies satisfied).

**Parameters:** None

### `expand_task`
Expand a task into subtasks using LLM analysis.

**Parameters:**
- `task_id` (required): Task ID to expand
- `research_query` (optional): Research query for gathering context
- `provider` (optional): LLM provider to use

### `validate_dependencies`
Validate task dependencies and check for issues.

**Parameters:** None

## Task Storage

Tasks are stored in `.taskmaster/tasks.json` in the project root directory. The file structure is:

```json
{
  "version": "1.0",
  "updated_at": "2024-01-15T10:30:00",
  "tasks": [
    {
      "id": "task-1",
      "description": "Implement user authentication",
      "status": "in-progress",
      "dependencies": [],
      "subtasks": ["task-1-1", "task-1-2"],
      "priority": 8,
      "created_at": "2024-01-15T10:00:00",
      "updated_at": "2024-01-15T10:30:00",
      "metadata": {}
    }
  ]
}
```

## PRD Format

PRD files can be plain text (`.txt`) or Markdown (`.md`). The LLM will analyze the content and extract:

- Project summary
- Features and requirements
- Task breakdown
- Dependencies
- Priorities

Example PRD:

```
# User Authentication System

## Overview
Build a secure user authentication system for our web application.

## Requirements

1. User Registration
   - Email validation
   - Password strength requirements
   - Email verification

2. User Login
   - Email/password authentication
   - Remember me functionality
   - Password reset

3. Security
   - JWT tokens
   - Session management
   - Rate limiting

## Technical Requirements
- Use JWT for authentication
- Store passwords securely (bcrypt)
- Implement rate limiting
- Support OAuth2 in future
```

## Workflow Examples

### Starting a New Project

1. **Create PRD**: Write your PRD in `prd.txt` or `prd.md`
2. **Parse PRD**: Ask Cursor to "Parse the PRD and create tasks"
3. **Review Tasks**: Check generated tasks with "List all tasks"
4. **Validate**: Run "Validate dependencies"
5. **Start Working**: Ask "What's the next task?" and begin

### Working Through Tasks

1. **Get Next Task**: "What should I work on next?"
2. **Expand if Needed**: "Break this task into subtasks"
3. **Mark In Progress**: "Set task-3 to in-progress"
4. **Work on Task**: Implement the feature
5. **Mark Done**: "Mark task-3 as done"
6. **Repeat**: Go back to step 1

### Handling Complex Tasks

1. **Identify Complex Task**: "Expand task-7 into subtasks"
2. **Use Research**: "Expand task-7 with research on JWT best practices"
3. **Review Subtasks**: Check the generated subtasks
4. **Work on Subtasks**: Complete each subtask in order

## Integration with Other Tools

Task Master can be combined with other MCP servers:

- **GitHub MCP**: Create issues from tasks
- **Atlassian MCP**: Sync tasks with Jira
- **Slack MCP**: Send task updates to channels

Example workflow:
1. Parse PRD ? Create tasks
2. Create GitHub issues for each task
3. Work on tasks
4. Update task status ? Update GitHub issue
5. Mark task done ? Close GitHub issue

## Best Practices

### Task Descriptions
- Be specific and actionable
- Include acceptance criteria when possible
- Use clear, concise language

### Dependencies
- Keep dependency chains short (max 3-4 levels)
- Validate dependencies regularly
- Document why dependencies exist

### Priorities
- Use 0-3 for low priority
- Use 4-7 for normal priority
- Use 8-10 for high/critical priority

### PRD Writing
- Include clear requirements
- Specify technical constraints
- Mention dependencies between features
- Add priorities or timelines if known

## Troubleshooting

### PRD Parsing Fails

**Problem**: `PRD parsing requires LLM client to be configured`

**Solution**: Configure LLM providers in `~/.mcp/config.yaml` and set API keys in environment variables.

### No Tasks Found

**Problem**: `next_task` returns no tasks

**Solution**: 
- Check if tasks exist: "List all tasks"
- Verify task status: Tasks should be `backlog` or `blocked`
- Check dependencies: All dependencies must be `done`

### Circular Dependencies

**Problem**: `validate_dependencies` shows circular dependencies

**Solution**: 
- Review the dependency chain
- Break the cycle by removing or adjusting dependencies
- Consider combining dependent tasks

### Tasks Not Persisting

**Problem**: Tasks disappear after restart

**Solution**: 
- Check `.taskmaster/` directory exists
- Verify write permissions on project directory
- Check server logs for save errors

## Advanced Usage

### Custom Task Metadata

Tasks support custom metadata:

```python
task = task_manager.add_task(
    description="Implement feature X",
    metadata={
        "estimate": "2 days",
        "assignee": "developer@example.com",
        "tags": ["frontend", "urgent"]
    }
)
```

### Programmatic Access

You can also use Task Master programmatically:

```python
from src.mcp.task_manager import TaskManager, TaskStatus

# Initialize
task_manager = TaskManager(project_root="/path/to/project")

# Add task
task = task_manager.add_task(
    description="Implement user login",
    priority=8,
    dependencies=["task-1"]
)

# Get next task
next_task = task_manager.next_task()

# Update status
task_manager.set_task_status(next_task.id, TaskStatus.IN_PROGRESS)
```

## References

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Cursor Documentation](https://cursor.sh/docs)
- [Task Master GitHub](https://github.com/claude-task-master)

---

**Task Master makes AI-assisted development more structured and manageable by providing persistent task context and intelligent task decomposition.**