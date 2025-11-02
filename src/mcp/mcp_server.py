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
        
        # Server info
        server_info = ServerInfo(
            name="mcp-devops-server",
            version="0.1.0"
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
            "disk_usage": self._tool_disk_usage
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
    
    def process_message(self, message: str) -> Optional[str]:
        """
        Process incoming MCP message.
        
        Args:
            message: JSON-RPC message
            
        Returns:
            Response message (or None for notifications)
        """
        return self.protocol.process_message(message)
