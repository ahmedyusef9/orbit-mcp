"""MCP Server implementation exposing DevOps tools via Model Context Protocol."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import json

from .protocol import (
    MCPProtocol, ServerInfo, ServerCapabilities, Tool, ToolResult,
    JSONRPCError, create_tool_result, create_structured_tool_result
)
from .config import ConfigManager
from .ssh_manager import SSHManager
from .docker_manager import DockerManager
from .k8s_manager import KubernetesManager
from .task_manager import TaskManager, TaskStatus
from .prd_parser import PRDParser
from .llm.providers import LLMClient

logger = logging.getLogger(__name__)


class MCPDevOpsServer:
    """MCP Server for DevOps operations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize MCP DevOps Server.
        
        Args:
            config_path: Path to configuration file
        """
        # Initialize managers
        self.config = ConfigManager(config_path)
        self.ssh_manager = SSHManager()
        self.docker_manager = DockerManager(self.ssh_manager)
        self.k8s_manager = KubernetesManager()
        
        # Initialize task management
        self.task_manager = TaskManager()
        
        # Initialize LLM client for PRD parsing and task expansion
        try:
            llm_config = self.config.config.get("llm", {})
            self.llm_client = LLMClient(llm_config)
            self.prd_parser = PRDParser(self.llm_client)
        except Exception as e:
            logger.warning(f"Failed to initialize LLM client: {e}. Task parsing features will be limited.")
            self.llm_client = None
            self.prd_parser = None
        
        # Server info
        server_info = ServerInfo(
            name="mcp-devops-server",
            version="0.2.0"
        )
        
        # Capabilities - we support tools
        capabilities = ServerCapabilities(
            tools={
                "listChanged": False  # Tool list doesn't change dynamically
            }
        )
        
        # Initialize protocol
        self.protocol = MCPProtocol(server_info, capabilities)
        
        # Register MCP methods
        self._register_methods()
        
        # Define tools
        self.tools = self._define_tools()
        
        logger.info("MCP DevOps Server initialized")
    
    def _register_methods(self):
        """Register MCP protocol method handlers."""
        self.protocol.register_method("tools/list", self._handle_tools_list)
        self.protocol.register_method("tools/call", self._handle_tools_call)
    
    def _define_tools(self) -> List[Tool]:
        """
        Define available DevOps tools.
        
        Returns:
            List of Tool definitions
        """
        return [
            # SSH Tools
            Tool(
                name="ssh_execute",
                description="Execute a shell command on a remote server via SSH",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server": {
                            "type": "string",
                            "description": "Server name from configuration"
                        },
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Command timeout in seconds (optional)",
                            "default": 30
                        }
                    },
                    "required": ["server", "command"]
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "stdout": {"type": "string"},
                        "stderr": {"type": "string"},
                        "exit_code": {"type": "integer"}
                    }
                }
            ),
            
            # Docker Tools
            Tool(
                name="docker_list_containers",
                description="List Docker containers and their status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "description": "Include stopped containers",
                            "default": False
                        }
                    }
                },
                outputSchema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "status": {"type": "string"},
                            "image": {"type": "string"}
                        }
                    }
                }
            ),
            
            Tool(
                name="docker_start_container",
                description="Start a Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "Container name or ID"
                        }
                    },
                    "required": ["container"]
                }
            ),
            
            Tool(
                name="docker_stop_container",
                description="Stop a Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "Container name or ID"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Stop timeout in seconds",
                            "default": 10
                        }
                    },
                    "required": ["container"]
                }
            ),
            
            Tool(
                name="docker_restart_container",
                description="Restart a Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "Container name or ID"
                        }
                    },
                    "required": ["container"]
                }
            ),
            
            Tool(
                name="docker_logs",
                description="Fetch logs from a Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "Container name or ID"
                        },
                        "tail": {
                            "type": "integer",
                            "description": "Number of lines to retrieve",
                            "default": 100
                        },
                        "follow": {
                            "type": "boolean",
                            "description": "Stream logs in real-time",
                            "default": False
                        }
                    },
                    "required": ["container"]
                }
            ),
            
            # Kubernetes Tools
            Tool(
                name="k8s_list_pods",
                description="List Kubernetes pods in a namespace",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cluster": {
                            "type": "string",
                            "description": "Cluster name from configuration (optional)"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    }
                },
                outputSchema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "namespace": {"type": "string"},
                            "status": {"type": "string"},
                            "node": {"type": "string"},
                            "ip": {"type": "string"}
                        }
                    }
                }
            ),
            
            Tool(
                name="k8s_get_pod",
                description="Get detailed information about a Kubernetes pod",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pod name"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    },
                    "required": ["name"]
                }
            ),
            
            Tool(
                name="k8s_logs",
                description="Fetch logs from a Kubernetes pod",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pod": {
                            "type": "string",
                            "description": "Pod name"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        },
                        "container": {
                            "type": "string",
                            "description": "Container name (for multi-container pods)"
                        },
                        "tail": {
                            "type": "integer",
                            "description": "Number of lines to retrieve",
                            "default": 100
                        },
                        "follow": {
                            "type": "boolean",
                            "description": "Stream logs in real-time",
                            "default": False
                        }
                    },
                    "required": ["pod"]
                }
            ),
            
            Tool(
                name="k8s_scale_deployment",
                description="Scale a Kubernetes deployment",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deployment": {
                            "type": "string",
                            "description": "Deployment name"
                        },
                        "replicas": {
                            "type": "integer",
                            "description": "Desired number of replicas"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    },
                    "required": ["deployment", "replicas"]
                }
            ),
            
            Tool(
                name="k8s_restart_deployment",
                description="Restart a Kubernetes deployment",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deployment": {
                            "type": "string",
                            "description": "Deployment name"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    },
                    "required": ["deployment"]
                }
            ),
            
            # System Tools
            Tool(
                name="query_logs",
                description="Query and filter log files from a remote server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server": {
                            "type": "string",
                            "description": "Server name from configuration"
                        },
                        "log_path": {
                            "type": "string",
                            "description": "Path to log file"
                        },
                        "filter": {
                            "type": "string",
                            "description": "Filter pattern (grep)"
                        },
                        "tail": {
                            "type": "integer",
                            "description": "Number of lines to retrieve",
                            "default": 100
                        },
                        "follow": {
                            "type": "boolean",
                            "description": "Stream logs in real-time",
                            "default": False
                        }
                    },
                    "required": ["server", "log_path"]
                }
            ),
            
            Tool(
                name="system_info",
                description="Get system information from a remote server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server": {
                            "type": "string",
                            "description": "Server name from configuration"
                        }
                    },
                    "required": ["server"]
                }
            ),
            
            Tool(
                name="disk_usage",
                description="Get disk usage information from a remote server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server": {
                            "type": "string",
                            "description": "Server name from configuration"
                        }
                    },
                    "required": ["server"]
                }
            ),
            
            # Task Management Tools
            Tool(
                name="parse_prd",
                description="Parse a Product Requirements Document (PRD) and generate structured tasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prd_path": {
                            "type": "string",
                            "description": "Path to PRD file (e.g., prd.txt, prd.md, or .taskmaster/prd.txt)"
                        },
                        "provider": {
                            "type": "string",
                            "description": "LLM provider to use (anthropic, openai, ollama). Optional, uses default if not specified."
                        }
                    },
                    "required": ["prd_path"]
                }
            ),
            
            Tool(
                name="get_tasks",
                description="Get all tasks, optionally filtered by status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter by status (backlog, in-progress, done, blocked, cancelled)",
                            "enum": ["backlog", "in-progress", "done", "blocked", "cancelled"]
                        },
                        "include_done": {
                            "type": "boolean",
                            "description": "Whether to include completed tasks",
                            "default": True
                        }
                    }
                }
            ),
            
            Tool(
                name="get_task",
                description="Get details of a specific task by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            
            Tool(
                name="add_task",
                description="Add a new task to the task list",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Task description"
                        },
                        "task_id": {
                            "type": "string",
                            "description": "Optional task ID (auto-generated if not provided)"
                        },
                        "status": {
                            "type": "string",
                            "description": "Initial status",
                            "enum": ["backlog", "in-progress", "done", "blocked", "cancelled"],
                            "default": "backlog"
                        },
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task IDs this task depends on"
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Priority (0-10, higher = more important)",
                            "default": 0
                        }
                    },
                    "required": ["description"]
                }
            ),
            
            Tool(
                name="set_task_status",
                description="Update the status of a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID"
                        },
                        "status": {
                            "type": "string",
                            "description": "New status",
                            "enum": ["backlog", "in-progress", "done", "blocked", "cancelled"]
                        }
                    },
                    "required": ["task_id", "status"]
                }
            ),
            
            Tool(
                name="remove_task",
                description="Remove a task from the task list",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to remove"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            
            Tool(
                name="next_task",
                description="Get the next highest-priority task ready to work on (dependencies satisfied)",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            
            Tool(
                name="expand_task",
                description="Expand a task into subtasks using LLM analysis, optionally with research",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to expand"
                        },
                        "research_query": {
                            "type": "string",
                            "description": "Optional research query for gathering additional context"
                        },
                        "provider": {
                            "type": "string",
                            "description": "LLM provider to use for expansion"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            
            Tool(
                name="validate_dependencies",
                description="Validate task dependencies and check for circular dependencies or missing references",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/list request.
        
        Args:
            params: Request parameters (may include cursor for pagination)
            
        Returns:
            List of available tools
        """
        logger.info("Handling tools/list request")
        
        tools_list = [tool.to_dict() for tool in self.tools]
        
        return {
            "tools": tools_list
        }
    
    def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/call request.
        
        Args:
            params: Tool invocation parameters (name, arguments)
            
        Returns:
            Tool execution result
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"Handling tools/call: {tool_name}")
        logger.debug(f"Arguments: {arguments}")
        
        if not tool_name:
            raise JSONRPCError(
                JSONRPCError.INVALID_PARAMS,
                "Missing tool name"
            )
        
        # Route to appropriate handler
        handler_map = {
            "ssh_execute": self._tool_ssh_execute,
            "docker_list_containers": self._tool_docker_list_containers,
            "docker_start_container": self._tool_docker_start_container,
            "docker_stop_container": self._tool_docker_stop_container,
            "docker_restart_container": self._tool_docker_restart_container,
            "docker_logs": self._tool_docker_logs,
            "k8s_list_pods": self._tool_k8s_list_pods,
            "k8s_get_pod": self._tool_k8s_get_pod,
            "k8s_logs": self._tool_k8s_logs,
            "k8s_scale_deployment": self._tool_k8s_scale_deployment,
            "k8s_restart_deployment": self._tool_k8s_restart_deployment,
            "query_logs": self._tool_query_logs,
            "system_info": self._tool_system_info,
            "disk_usage": self._tool_disk_usage,
            # Task Management Tools
            "parse_prd": self._tool_parse_prd,
            "get_tasks": self._tool_get_tasks,
            "get_task": self._tool_get_task,
            "add_task": self._tool_add_task,
            "set_task_status": self._tool_set_task_status,
            "remove_task": self._tool_remove_task,
            "next_task": self._tool_next_task,
            "expand_task": self._tool_expand_task,
            "validate_dependencies": self._tool_validate_dependencies
        }
        
        handler = handler_map.get(tool_name)
        if not handler:
            raise JSONRPCError(
                JSONRPCError.METHOD_NOT_FOUND,
                f"Unknown tool: {tool_name}"
            )
        
        try:
            result = handler(arguments)
            return result.to_dict()
        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            error_result = create_tool_result(
                f"Tool execution failed: {str(e)}",
                is_error=True
            )
            return error_result.to_dict()
    
    # Tool Implementations
    
    def _tool_ssh_execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute SSH command."""
        server_name = args["server"]
        command = args["command"]
        timeout = args.get("timeout", 30)
        
        # Get server config
        server_config = self.config.get_ssh_server(server_name)
        if not server_config:
            return create_tool_result(
                f"Server not found in configuration: {server_name}",
                is_error=True
            )
        
        # Connect and execute
        try:
            client = self.ssh_manager.connect(
                server_config['host'],
                server_config['user'],
                server_config.get('port', 22),
                server_config.get('key_path'),
                server_config.get('password'),
                timeout=timeout
            )
            
            stdout, stderr, exit_code = self.ssh_manager.execute_command(
                client, command, timeout
            )
            
            # Format output
            output_text = f"Exit Code: {exit_code}\n\n"
            if stdout:
                output_text += f"STDOUT:\n{stdout}\n"
            if stderr:
                output_text += f"STDERR:\n{stderr}\n"
            
            structured_data = {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code
            }
            
            is_error = exit_code != 0
            
            return create_structured_tool_result(
                output_text,
                structured_data,
                is_error=is_error
            )
        
        except Exception as e:
            return create_tool_result(
                f"SSH execution failed: {str(e)}",
                is_error=True
            )
    
    def _tool_docker_list_containers(self, args: Dict[str, Any]) -> ToolResult:
        """List Docker containers."""
        show_all = args.get("all", False)
        
        try:
            containers = self.docker_manager.list_containers(all=show_all)
            
            # Format as text
            text = f"Docker Containers ({len(containers)} found):\n\n"
            for container in containers:
                text += f"? {container['name']} ({container['id']})\n"
                text += f"  Status: {container['status']}\n"
                text += f"  Image: {container['image']}\n\n"
            
            return create_structured_tool_result(text, containers)
        
        except Exception as e:
            return create_tool_result(
                f"Failed to list containers: {str(e)}",
                is_error=True
            )
    
    def _tool_docker_start_container(self, args: Dict[str, Any]) -> ToolResult:
        """Start Docker container."""
        container = args["container"]
        
        try:
            self.docker_manager.start_container(container)
            return create_tool_result(
                f"Successfully started container: {container}"
            )
        except Exception as e:
            return create_tool_result(
                f"Failed to start container: {str(e)}",
                is_error=True
            )
    
    def _tool_docker_stop_container(self, args: Dict[str, Any]) -> ToolResult:
        """Stop Docker container."""
        container = args["container"]
        timeout = args.get("timeout", 10)
        
        try:
            self.docker_manager.stop_container(container, timeout=timeout)
            return create_tool_result(
                f"Successfully stopped container: {container}"
            )
        except Exception as e:
            return create_tool_result(
                f"Failed to stop container: {str(e)}",
                is_error=True
            )
    
    def _tool_docker_restart_container(self, args: Dict[str, Any]) -> ToolResult:
        """Restart Docker container."""
        container = args["container"]
        
        try:
            self.docker_manager.restart_container(container)
            return create_tool_result(
                f"Successfully restarted container: {container}"
            )
        except Exception as e:
            return create_tool_result(
                f"Failed to restart container: {str(e)}",
                is_error=True
            )
    
    def _tool_docker_logs(self, args: Dict[str, Any]) -> ToolResult:
        """Get Docker container logs."""
        container = args["container"]
        tail = args.get("tail", 100)
        follow = args.get("follow", False)
        
        if follow:
            return create_tool_result(
                "Streaming logs not supported in current implementation",
                is_error=True
            )
        
        try:
            logs = []
            for line in self.docker_manager.get_container_logs(
                container, tail=tail, follow=False
            ):
                logs.append(line)
            
            log_text = "\n".join(logs)
            return create_tool_result(
                f"Logs for {container} (last {tail} lines):\n\n{log_text}"
            )
        except Exception as e:
            return create_tool_result(
                f"Failed to get logs: {str(e)}",
                is_error=True
            )
    
    def _tool_k8s_list_pods(self, args: Dict[str, Any]) -> ToolResult:
        """List Kubernetes pods."""
        namespace = args.get("namespace", "default")
        cluster = args.get("cluster")
        
        # Load cluster if specified
        if cluster:
            cluster_config = self.config.get_k8s_cluster(cluster)
            if not cluster_config:
                return create_tool_result(
                    f"Cluster not found: {cluster}",
                    is_error=True
                )
            self.k8s_manager.load_kubeconfig(
                cluster_config['kubeconfig_path'],
                cluster_config.get('context')
            )
        
        try:
            pods = self.k8s_manager.list_pods(namespace)
            
            # Format output
            text = f"Pods in namespace '{namespace}' ({len(pods)} found):\n\n"
            for pod in pods:
                text += f"? {pod['name']}\n"
                text += f"  Status: {pod['status']}\n"
                text += f"  Node: {pod.get('node', 'N/A')}\n"
                text += f"  IP: {pod.get('ip', 'N/A')}\n\n"
            
            return create_structured_tool_result(text, pods)
        
        except Exception as e:
            return create_tool_result(
                f"Failed to list pods: {str(e)}",
                is_error=True
            )
    
    def _tool_k8s_get_pod(self, args: Dict[str, Any]) -> ToolResult:
        """Get Kubernetes pod details."""
        name = args["name"]
        namespace = args.get("namespace", "default")
        
        try:
            pod_info = self.k8s_manager.get_pod(name, namespace)
            
            # Format output
            text = f"Pod: {pod_info['name']}\n"
            text += f"Namespace: {pod_info['namespace']}\n"
            text += f"Status: {pod_info['status']}\n"
            text += f"Node: {pod_info.get('node', 'N/A')}\n"
            text += f"IP: {pod_info.get('ip', 'N/A')}\n"
            text += f"Containers: {', '.join(pod_info.get('containers', []))}\n"
            
            if pod_info.get('conditions'):
                text += "\nConditions:\n"
                for condition in pod_info['conditions']:
                    text += f"  ? {condition['type']}: {condition['status']}\n"
            
            return create_structured_tool_result(text, pod_info)
        
        except Exception as e:
            return create_tool_result(
                f"Failed to get pod: {str(e)}",
                is_error=True
            )
    
    def _tool_k8s_logs(self, args: Dict[str, Any]) -> ToolResult:
        """Get Kubernetes pod logs."""
        pod = args["pod"]
        namespace = args.get("namespace", "default")
        container = args.get("container")
        tail = args.get("tail", 100)
        follow = args.get("follow", False)
        
        if follow:
            return create_tool_result(
                "Streaming logs not supported in current implementation",
                is_error=True
            )
        
        try:
            logs = self.k8s_manager.get_pod_logs(
                pod, namespace, container, tail, follow=False
            )
            
            return create_tool_result(
                f"Logs for pod {pod}:\n\n{logs}"
            )
        
        except Exception as e:
            return create_tool_result(
                f"Failed to get logs: {str(e)}",
                is_error=True
            )
    
    def _tool_k8s_scale_deployment(self, args: Dict[str, Any]) -> ToolResult:
        """Scale Kubernetes deployment."""
        deployment = args["deployment"]
        replicas = args["replicas"]
        namespace = args.get("namespace", "default")
        
        try:
            self.k8s_manager.scale_deployment(deployment, replicas, namespace)
            return create_tool_result(
                f"Successfully scaled deployment {deployment} to {replicas} replicas"
            )
        except Exception as e:
            return create_tool_result(
                f"Failed to scale deployment: {str(e)}",
                is_error=True
            )
    
    def _tool_k8s_restart_deployment(self, args: Dict[str, Any]) -> ToolResult:
        """Restart Kubernetes deployment."""
        deployment = args["deployment"]
        namespace = args.get("namespace", "default")
        
        try:
            self.k8s_manager.restart_deployment(deployment, namespace)
            return create_tool_result(
                f"Successfully restarted deployment: {deployment}"
            )
        except Exception as e:
            return create_tool_result(
                f"Failed to restart deployment: {str(e)}",
                is_error=True
            )
    
    def _tool_query_logs(self, args: Dict[str, Any]) -> ToolResult:
        """Query log files."""
        server_name = args["server"]
        log_path = args["log_path"]
        filter_pattern = args.get("filter")
        tail = args.get("tail", 100)
        follow = args.get("follow", False)
        
        if follow:
            return create_tool_result(
                "Streaming logs not supported in current implementation",
                is_error=True
            )
        
        # Get server config
        server_config = self.config.get_ssh_server(server_name)
        if not server_config:
            return create_tool_result(
                f"Server not found: {server_name}",
                is_error=True
            )
        
        try:
            client = self.ssh_manager.connect(
                server_config['host'],
                server_config['user'],
                server_config.get('port', 22),
                server_config.get('key_path'),
                server_config.get('password')
            )
            
            # Build command
            command = f"tail -n {tail} {log_path}"
            if filter_pattern:
                command += f" | grep '{filter_pattern}'"
            
            stdout, stderr, exit_code = self.ssh_manager.execute_command(
                client, command
            )
            
            if exit_code != 0 and stderr:
                return create_tool_result(
                    f"Failed to query logs: {stderr}",
                    is_error=True
                )
            
            return create_tool_result(
                f"Logs from {log_path}:\n\n{stdout}"
            )
        
        except Exception as e:
            return create_tool_result(
                f"Failed to query logs: {str(e)}",
                is_error=True
            )
    
    def _tool_system_info(self, args: Dict[str, Any]) -> ToolResult:
        """Get system information."""
        server_name = args["server"]
        
        server_config = self.config.get_ssh_server(server_name)
        if not server_config:
            return create_tool_result(
                f"Server not found: {server_name}",
                is_error=True
            )
        
        try:
            client = self.ssh_manager.connect(
                server_config['host'],
                server_config['user'],
                server_config.get('port', 22),
                server_config.get('key_path'),
                server_config.get('password')
            )
            
            # Gather system info
            commands = [
                "uname -a",
                "uptime",
                "cat /etc/os-release | head -2"
            ]
            
            results = self.ssh_manager.execute_commands(client, commands)
            
            info_text = f"System Information for {server_name}:\n\n"
            info_text += f"Kernel: {results[0][0]}\n"
            info_text += f"Uptime: {results[1][0]}\n"
            info_text += f"OS: {results[2][0]}\n"
            
            return create_tool_result(info_text)
        
        except Exception as e:
            return create_tool_result(
                f"Failed to get system info: {str(e)}",
                is_error=True
            )
    
    def _tool_disk_usage(self, args: Dict[str, Any]) -> ToolResult:
        """Get disk usage."""
        server_name = args["server"]
        
        server_config = self.config.get_ssh_server(server_name)
        if not server_config:
            return create_tool_result(
                f"Server not found: {server_name}",
                is_error=True
            )
        
        try:
            client = self.ssh_manager.connect(
                server_config['host'],
                server_config['user'],
                server_config.get('port', 22),
                server_config.get('key_path'),
                server_config.get('password')
            )
            
            stdout, stderr, exit_code = self.ssh_manager.execute_command(
                client, "df -h"
            )
            
            if exit_code != 0:
                return create_tool_result(
                    f"Failed to get disk usage: {stderr}",
                    is_error=True
                )
            
            return create_tool_result(
                f"Disk Usage for {server_name}:\n\n{stdout}"
            )
        
        except Exception as e:
            return create_tool_result(
                f"Failed to get disk usage: {str(e)}",
                is_error=True
            )
    
    # Task Management Tool Implementations
    
    def _tool_parse_prd(self, args: Dict[str, Any]) -> ToolResult:
        """Parse PRD and generate tasks."""
        prd_path = args["prd_path"]
        provider = args.get("provider")
        
        if not self.prd_parser:
            return create_tool_result(
                "PRD parsing requires LLM client to be configured. Please configure LLM providers in config.yaml",
                is_error=True
            )
        
        try:
            import asyncio
            
            # Run async PRD parsing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.prd_parser.parse_prd(prd_path, provider)
            )
            loop.close()
            
            if not result.get("success"):
                return create_tool_result(
                    "PRD parsing failed",
                    is_error=True
                )
            
            # Add tasks to task manager
            tasks_created = []
            for task_data in result.get("tasks", []):
                try:
                    task = self.task_manager.add_task(
                        description=task_data["description"],
                        task_id=task_data.get("id"),
                        status=TaskStatus(task_data.get("status", "backlog")),
                        dependencies=task_data.get("dependencies", []),
                        priority=task_data.get("priority", 0)
                    )
                    tasks_created.append(task.to_dict())
                except Exception as e:
                    logger.warning(f"Failed to add task {task_data.get('id')}: {e}")
            
            # Add subtasks if any
            subtasks_map = {st["id"]: st for st in result.get("subtasks", [])}
            for subtask_data in subtasks_map.values():
                parent_id = subtask_data.get("parent_task")
                if parent_id:
                    try:
                        task = self.task_manager.add_task(
                            description=subtask_data["description"],
                            task_id=subtask_data["id"],
                            status=TaskStatus.BACKLOG,
                            dependencies=[parent_id],
                            priority=self.task_manager.get_task(parent_id).priority if parent_id in self.task_manager.tasks else 0
                        )
                        # Update parent task's subtasks list
                        parent = self.task_manager.get_task(parent_id)
                        if parent and task.id not in parent.subtasks:
                            parent.subtasks.append(task.id)
                            self.task_manager._save_tasks()
                        tasks_created.append(task.to_dict())
                    except Exception as e:
                        logger.warning(f"Failed to add subtask {subtask_data.get('id')}: {e}")
            
            summary = result.get("summary", "")
            metadata = result.get("metadata", {})
            
            text = f"PRD parsed successfully!\n\nSummary: {summary}\n\nCreated {len(tasks_created)} tasks.\n\nTasks:\n"
            for task_dict in tasks_created[:10]:  # Show first 10
                text += f"- [{task_dict['id']}] {task_dict['description']} (priority: {task_dict['priority']})\n"
            if len(tasks_created) > 10:
                text += f"... and {len(tasks_created) - 10} more tasks\n"
            
            return create_structured_tool_result(
                text,
                {
                    "summary": summary,
                    "tasks_created": len(tasks_created),
                    "tasks": tasks_created,
                    "metadata": metadata
                }
            )
        
        except Exception as e:
            logger.error(f"PRD parsing failed: {e}", exc_info=True)
            return create_tool_result(
                f"Failed to parse PRD: {str(e)}",
                is_error=True
            )
    
    def _tool_get_tasks(self, args: Dict[str, Any]) -> ToolResult:
        """Get all tasks."""
        status_str = args.get("status")
        include_done = args.get("include_done", True)
        
        status = None
        if status_str:
            try:
                status = TaskStatus(status_str)
            except ValueError:
                return create_tool_result(
                    f"Invalid status: {status_str}",
                    is_error=True
                )
        
        tasks = self.task_manager.get_tasks(status=status, include_done=include_done)
        task_dicts = [task.to_dict() for task in tasks]
        
        text = f"Found {len(tasks)} tasks:\n\n"
        for task_dict in task_dicts[:20]:  # Show first 20
            text += f"- [{task_dict['status']}] {task_dict['id']}: {task_dict['description']}\n"
        if len(tasks) > 20:
            text += f"... and {len(tasks) - 20} more tasks\n"
        
        return create_structured_tool_result(text, {"tasks": task_dicts, "count": len(tasks)})
    
    def _tool_get_task(self, args: Dict[str, Any]) -> ToolResult:
        """Get a specific task."""
        task_id = args["task_id"]
        task = self.task_manager.get_task(task_id)
        
        if not task:
            return create_tool_result(
                f"Task not found: {task_id}",
                is_error=True
            )
        
        task_dict = task.to_dict()
        
        text = f"Task: {task_id}\n"
        text += f"Status: {task.status.value}\n"
        text += f"Description: {task.description}\n"
        text += f"Priority: {task.priority}\n"
        if task.dependencies:
            text += f"Dependencies: {', '.join(task.dependencies)}\n"
        if task.subtasks:
            text += f"Subtasks: {', '.join(task.subtasks)}\n"
        
        return create_structured_tool_result(text, task_dict)
    
    def _tool_add_task(self, args: Dict[str, Any]) -> ToolResult:
        """Add a new task."""
        description = args["description"]
        task_id = args.get("task_id")
        status_str = args.get("status", "backlog")
        dependencies = args.get("dependencies", [])
        priority = args.get("priority", 0)
        
        try:
            status = TaskStatus(status_str)
        except ValueError:
            return create_tool_result(
                f"Invalid status: {status_str}",
                is_error=True
            )
        
        try:
            task = self.task_manager.add_task(
                description=description,
                task_id=task_id,
                status=status,
                dependencies=dependencies,
                priority=priority
            )
            
            text = f"Added task: {task.id}\nDescription: {task.description}\nStatus: {task.status.value}\nPriority: {task.priority}"
            
            return create_structured_tool_result(text, task.to_dict())
        except Exception as e:
            return create_tool_result(
                f"Failed to add task: {str(e)}",
                is_error=True
            )
    
    def _tool_set_task_status(self, args: Dict[str, Any]) -> ToolResult:
        """Set task status."""
        task_id = args["task_id"]
        status_str = args["status"]
        
        try:
            status = TaskStatus(status_str)
        except ValueError:
            return create_tool_result(
                f"Invalid status: {status_str}",
                is_error=True
            )
        
        try:
            task = self.task_manager.set_task_status(task_id, status)
            text = f"Updated task {task_id} status to {status.value}"
            return create_structured_tool_result(text, task.to_dict())
        except ValueError as e:
            return create_tool_result(
                f"Failed to update task status: {str(e)}",
                is_error=True
            )
    
    def _tool_remove_task(self, args: Dict[str, Any]) -> ToolResult:
        """Remove a task."""
        task_id = args["task_id"]
        
        try:
            success = self.task_manager.remove_task(task_id)
            if success:
                return create_tool_result(f"Removed task: {task_id}")
            else:
                return create_tool_result(
                    f"Task not found: {task_id}",
                    is_error=True
                )
        except ValueError as e:
            return create_tool_result(
                f"Cannot remove task: {str(e)}",
                is_error=True
            )
    
    def _tool_next_task(self, args: Dict[str, Any]) -> ToolResult:
        """Get next task to work on."""
        next_task = self.task_manager.next_task()
        
        if not next_task:
            return create_tool_result(
                "No tasks ready to work on. All tasks are either done or have unmet dependencies.",
                is_error=False
            )
        
        text = f"Next task to work on:\n\n"
        text += f"ID: {next_task.id}\n"
        text += f"Description: {next_task.description}\n"
        text += f"Status: {next_task.status.value}\n"
        text += f"Priority: {next_task.priority}\n"
        if next_task.dependencies:
            text += f"Dependencies: {', '.join(next_task.dependencies)} (all satisfied)\n"
        
        return create_structured_tool_result(text, next_task.to_dict())
    
    def _tool_expand_task(self, args: Dict[str, Any]) -> ToolResult:
        """Expand a task into subtasks."""
        task_id = args["task_id"]
        research_query = args.get("research_query")
        provider = args.get("provider")
        
        task = self.task_manager.get_task(task_id)
        if not task:
            return create_tool_result(
                f"Task not found: {task_id}",
                is_error=True
            )
        
        if not self.prd_parser:
            return create_tool_result(
                "Task expansion requires LLM client to be configured.",
                is_error=True
            )
        
        try:
            import asyncio
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.prd_parser.expand_task_with_research(
                    task.description,
                    research_query,
                    provider
                )
            )
            loop.close()
            
            if not result.get("success"):
                return create_tool_result(
                    "Task expansion failed",
                    is_error=True
                )
            
            subtasks = result.get("subtasks", [])
            if not subtasks:
                return create_tool_result(
                    "No subtasks generated",
                    is_error=False
                )
            
            # Expand the task
            expanded = self.task_manager.expand_task(task_id, subtasks)
            
            text = f"Expanded task {task_id} into {len(subtasks)} subtasks:\n\n"
            for i, subtask_desc in enumerate(subtasks, 1):
                text += f"{i}. {subtask_desc}\n"
            
            return create_structured_tool_result(
                text,
                {
                    "task_id": task_id,
                    "subtasks": subtasks,
                    "analysis": result.get("analysis", ""),
                    "metadata": result.get("metadata", {})
                }
            )
        except Exception as e:
            logger.error(f"Task expansion failed: {e}", exc_info=True)
            return create_tool_result(
                f"Failed to expand task: {str(e)}",
                is_error=True
            )
    
    def _tool_validate_dependencies(self, args: Dict[str, Any]) -> ToolResult:
        """Validate task dependencies."""
        validation = self.task_manager.validate_dependencies()
        
        is_valid = validation["valid"]
        issues = validation["issues"]
        
        text = f"Dependency Validation Results:\n\n"
        text += f"Valid: {is_valid}\n"
        text += f"Total tasks: {validation['total_tasks']}\n\n"
        
        text += f"Tasks by status:\n"
        for status, count in validation["tasks_by_status"].items():
            if count > 0:
                text += f"  {status}: {count}\n"
        
        if not is_valid:
            text += "\nIssues found:\n"
            if issues["circular_dependencies"]:
                text += f"  Circular dependencies: {issues['circular_dependencies']}\n"
            if issues["missing_dependencies"]:
                text += f"  Missing dependencies: {len(issues['missing_dependencies'])} found\n"
                for issue in issues["missing_dependencies"][:5]:
                    text += f"    - Task {issue['task']} depends on missing task {issue['missing_dependency']}\n"
            if issues["orphaned_tasks"]:
                text += f"  Orphaned tasks: {len(issues['orphaned_tasks'])} found\n"
        else:
            text += "\nNo dependency issues found!\n"
        
        return create_structured_tool_result(text, validation)
    
    def process_message(self, message: str) -> Optional[str]:
        """
        Process incoming MCP message.
        
        Args:
            message: JSON-RPC message
            
        Returns:
            Response message (or None for notifications)
        """
        return self.protocol.process_message(message)
