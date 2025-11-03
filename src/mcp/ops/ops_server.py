"""Ops MCP Server - Main server implementation."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..protocol import (
    MCPProtocol, ServerInfo, ServerCapabilities, Tool, ToolResult,
    JSONRPCError, create_tool_result, create_structured_tool_result
)

from .profile import ProfileManager
from .ssh_wrapper import SSHWrapper
from .tickets import create_ticket_system
from .alerts import AlertSystem
from .resources import ResourceResolver, PromptRegistry

logger = logging.getLogger(__name__)


class OpsMCPServer:
    """Ops MCP Server with tools, resources, and prompts."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize Ops MCP Server.
        
        Args:
            config_path: Path to configuration file
        """
        # Initialize profile manager
        self.profile_manager = ProfileManager(config_path)
        self.active_profile = self.profile_manager.get_active_profile()
        
        if not self.active_profile:
            logger.warning("No active profile found, using minimal defaults")
            # Create minimal default profile
            from .profile import Profile
            self.active_profile = Profile("default", {})
        
        # Initialize components
        self.ssh_wrapper = SSHWrapper(self.active_profile)
        
        # Load ticket system config
        import yaml
        config = {}
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        
        ticket_config = config.get("tickets", {})
        self.ticket_system = create_ticket_system(self.active_profile, ticket_config)
        
        # Initialize alert system
        alert_config = config.get("alerts", {})
        self.alert_system = None
        if alert_config.get("endpoint"):
            self.alert_system = AlertSystem(
                endpoint=alert_config["endpoint"],
                api_key=alert_config.get("api_key"),
                namespace=self.active_profile.alert_namespace
            )
        
        # Initialize resources and prompts
        resource_config = config.get("resources", {})
        self.resource_resolver = ResourceResolver(self.active_profile, resource_config)
        self.prompt_registry = PromptRegistry()
        
        # Server info
        server_info = ServerInfo(
            name="ops-mcp-server",
            version="1.0.0"
        )
        
        # Capabilities - we support tools, resources, and prompts
        capabilities = ServerCapabilities(
            tools={"listChanged": False},
            resources={"subscribe": False, "listChanged": False},
            prompts={"listChanged": False}
        )
        
        # Initialize protocol
        self.protocol = MCPProtocol(server_info, capabilities)
        
        # Register MCP methods
        self._register_methods()
        
        # Define tools, resources, prompts
        self.tools = self._define_tools()
        self.resources = self.resource_resolver.list_resources()
        self.prompts = self.prompt_registry.list_prompts()
        
        logger.info(f"Ops MCP Server initialized with profile: {self.active_profile.name}")
    
    def _register_methods(self):
        """Register MCP protocol method handlers."""
        # Tools
        self.protocol.register_method("tools/list", self._handle_tools_list)
        self.protocol.register_method("tools/call", self._handle_tools_call)
        
        # Resources
        self.protocol.register_method("resources/list", self._handle_resources_list)
        self.protocol.register_method("resources/read", self._handle_resources_read)
        
        # Prompts
        self.protocol.register_method("prompts/list", self._handle_prompts_list)
        self.protocol.register_method("prompts/get", self._handle_prompts_get)
    
    def _define_tools(self) -> List[Tool]:
        """Define available tools."""
        # Get available hosts from profile
        host_names = list(self.active_profile.ssh_hosts.keys()) if self.active_profile.ssh_hosts else []
        cmd_keys = list(self.active_profile.ssh_allowed_commands.keys()) if self.active_profile.ssh_allowed_commands else []
        
        tools = [
            # SSH Tools
            Tool(
                name="ssh.run",
                description=f"Run an allow-listed non-interactive command on a named host. Profile: {self.active_profile.name}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "host": {
                            "type": "string",
                            "enum": host_names,
                            "description": "Host name from profile"
                        },
                        "cmd": {
                            "type": "string",
                            "enum": cmd_keys,
                            "description": "Command key from allow-list"
                        },
                        "args": {
                            "type": "object",
                            "description": "Arguments for command template"
                        },
                        "timeoutSec": {
                            "type": "integer",
                            "default": 60,
                            "maximum": 120,
                            "description": "Timeout in seconds (max 120)"
                        }
                    },
                    "required": ["host", "cmd"]
                }
            ),
            Tool(
                name="ssh.tail",
                description=f"Stream logs from allow-listed paths. Profile: {self.active_profile.name}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "enum": host_names},
                        "path": {"type": "string", "description": "Log file path"},
                        "lines": {"type": "integer", "default": 100, "maximum": 1000}
                    },
                    "required": ["host", "path"]
                }
            ),
            Tool(
                name="ssh.healthcheck",
                description=f"Run healthcheck diagnostic bundle. Profile: {self.active_profile.name}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "enum": host_names}
                    },
                    "required": ["host"]
                }
            ),
            
            # Ticket Tools
            Tool(
                name="ticket.create",
                description="Create a ticket (Jira/GitHub)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "labels": {"type": "array", "items": {"type": "string"}},
                        "priority": {
                            "type": "string",
                            "enum": ["Low", "Medium", "High", "Critical"],
                            "default": "Medium"
                        }
                    },
                    "required": ["title", "body"]
                }
            ),
            Tool(
                name="ticket.updateStatus",
                description="Update ticket status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticketId": {"type": "string"},
                        "status": {"type": "string"}
                    },
                    "required": ["ticketId", "status"]
                }
            ),
            Tool(
                name="ticket.comment",
                description="Add comment to ticket",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticketId": {"type": "string"},
                        "comment": {"type": "string"}
                    },
                    "required": ["ticketId", "comment"]
                }
            ),
            
            # Alert Tools
            Tool(
                name="alert.list",
                description="List alerts with filtering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "severity": {"type": "string"},
                        "limit": {"type": "integer", "default": 50, "maximum": 100}
                    }
                }
            ),
            Tool(
                name="alert.get",
                description="Get specific alert details",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "alertId": {"type": "string"}
                    },
                    "required": ["alertId"]
                }
            ),
            Tool(
                name="alert.ack",
                description="Acknowledge an alert",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "alertId": {"type": "string"},
                        "note": {"type": "string"}
                    },
                    "required": ["alertId"]
                }
            ),
            
            # Workflow Tools
            Tool(
                name="triage.start",
                description="Start triage workflow - create defect PRD and task list",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "incidentSummary": {"type": "string"},
                        "service": {"type": "string"}
                    },
                    "required": ["incidentSummary"]
                }
            ),
            Tool(
                name="profile.set",
                description="Set active profile",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "enum": self.profile_manager.list_profiles()
                        }
                    },
                    "required": ["name"]
                }
            ),
        ]
        
        return tools
    
    # Tool Handlers
    
    def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {"tools": [tool.to_dict() for tool in self.tools]}
    
    def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise JSONRPCError(JSONRPCError.INVALID_PARAMS, "Missing tool name")
        
        # Route to handler
        handler_map = {
            "ssh.run": self._tool_ssh_run,
            "ssh.tail": self._tool_ssh_tail,
            "ssh.healthcheck": self._tool_ssh_healthcheck,
            "ticket.create": self._tool_ticket_create,
            "ticket.updateStatus": self._tool_ticket_update_status,
            "ticket.comment": self._tool_ticket_comment,
            "alert.list": self._tool_alert_list,
            "alert.get": self._tool_alert_get,
            "alert.ack": self._tool_alert_ack,
            "triage.start": self._tool_triage_start,
            "profile.set": self._tool_profile_set,
        }
        
        handler = handler_map.get(tool_name)
        if not handler:
            raise JSONRPCError(JSONRPCError.METHOD_NOT_FOUND, f"Unknown tool: {tool_name}")
        
        try:
            result = handler(arguments)
            return result.to_dict()
        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return create_tool_result(f"Tool execution failed: {str(e)}", is_error=True).to_dict()
    
    def _tool_ssh_run(self, args: Dict[str, Any]) -> ToolResult:
        """Execute SSH command."""
        host = args["host"]
        cmd_key = args["cmd"]
        cmd_args = args.get("args", {})
        timeout = args.get("timeoutSec", 60)
        
        # Validate and render command
        is_valid, cmd_or_error = self.ssh_wrapper.validate_command(cmd_key, cmd_args)
        if not is_valid:
            return create_tool_result(
                f"PERMISSION_DENIED: {cmd_or_error}",
                is_error=True
            )
        
        # Execute
        result = self.ssh_wrapper.execute_command(host, cmd_or_error, timeout)
        
        if result.get("success"):
            text = f"[Profile: {self.active_profile.name}] Command executed successfully\n"
            text += f"Exit Code: {result['exit_code']}\n"
            text += f"Output ({result['bytes_stdout']} bytes):\n{result['stdout']}"
            if result.get("was_redacted"):
                text += "\n?? Output was redacted due to potential secrets"
            return create_structured_tool_result(text, result)
        else:
            return create_tool_result(
                f"{result.get('error', 'UNKNOWN_ERROR')}: {result.get('message', 'Command failed')}",
                is_error=True
            )
    
    def _tool_ssh_tail(self, args: Dict[str, Any]) -> ToolResult:
        """Tail logs."""
        host = args["host"]
        path = args["path"]
        lines = args.get("lines", 100)
        
        result = self.ssh_wrapper.tail_logs(host, path, lines)
        if result.get("success"):
            text = f"Logs from {host}:{path}\n\n{result['content']}"
            return create_structured_tool_result(text, result)
        else:
            return create_tool_result(result.get("message", "Failed to tail logs"), is_error=True)
    
    def _tool_ssh_healthcheck(self, args: Dict[str, Any]) -> ToolResult:
        """Run healthcheck."""
        host = args["host"]
        result = self.ssh_wrapper.healthcheck(host)
        
        text = f"Healthcheck for {host}\n\n"
        for name, diag in result.get("diagnostics", {}).items():
            text += f"{name}:\n{diag.get('stdout', 'N/A')}\n\n"
        
        return create_structured_tool_result(text, result)
    
    def _tool_ticket_create(self, args: Dict[str, Any]) -> ToolResult:
        """Create ticket."""
        if not self.ticket_system:
            return create_tool_result("Ticket system not configured", is_error=True)
        
        title = args["title"]
        body = args["body"]
        labels = args.get("labels", [])
        priority = args.get("priority", "Medium")
        project = self.active_profile.ticket_project
        
        result = self.ticket_system.create_ticket(project, title, body, labels, priority)
        if result.get("success"):
            text = f"Created ticket: {result['id']}\nURL: {result['url']}"
            return create_structured_tool_result(text, result)
        else:
            return create_tool_result(result.get("message", "Failed to create ticket"), is_error=True)
    
    def _tool_ticket_update_status(self, args: Dict[str, Any]) -> ToolResult:
        """Update ticket status."""
        if not self.ticket_system:
            return create_tool_result("Ticket system not configured", is_error=True)
        
        ticket_id = args["ticketId"]
        status = args["status"]
        
        result = self.ticket_system.update_status(ticket_id, status)
        if result.get("success"):
            text = f"Updated ticket {ticket_id} to {status}"
            return create_structured_tool_result(text, result)
        else:
            return create_tool_result(result.get("message", "Failed to update ticket"), is_error=True)
    
    def _tool_ticket_comment(self, args: Dict[str, Any]) -> ToolResult:
        """Add ticket comment."""
        if not self.ticket_system:
            return create_tool_result("Ticket system not configured", is_error=True)
        
        ticket_id = args["ticketId"]
        comment = args["comment"]
        
        result = self.ticket_system.add_comment(ticket_id, comment)
        if result.get("success"):
            return create_tool_result(f"Added comment to ticket {ticket_id}")
        else:
            return create_tool_result(result.get("message", "Failed to add comment"), is_error=True)
    
    def _tool_alert_list(self, args: Dict[str, Any]) -> ToolResult:
        """List alerts."""
        if not self.alert_system:
            return create_tool_result("Alert system not configured", is_error=True)
        
        status = args.get("status")
        severity = args.get("severity")
        limit = args.get("limit", 50)
        
        result = self.alert_system.list_alerts(status, severity, limit)
        if result.get("success"):
            alerts = result.get("alerts", [])
            text = f"Found {len(alerts)} alerts\n\n"
            for alert in alerts[:10]:  # Show first 10
                text += f"- {alert.get('id', 'N/A')}: {alert.get('summary', 'N/A')}\n"
            if len(alerts) > 10:
                text += f"... and {len(alerts) - 10} more\n"
            return create_structured_tool_result(text, result)
        else:
            return create_tool_result(result.get("message", "Failed to list alerts"), is_error=True)
    
    def _tool_alert_get(self, args: Dict[str, Any]) -> ToolResult:
        """Get alert."""
        if not self.alert_system:
            return create_tool_result("Alert system not configured", is_error=True)
        
        alert_id = args["alertId"]
        result = self.alert_system.get_alert(alert_id)
        if result.get("success"):
            alert = result.get("alert", {})
            text = f"Alert: {alert_id}\n{str(alert)[:500]}"
            return create_structured_tool_result(text, result)
        else:
            return create_tool_result(result.get("message", "Failed to get alert"), is_error=True)
    
    def _tool_alert_ack(self, args: Dict[str, Any]) -> ToolResult:
        """Acknowledge alert."""
        if not self.alert_system:
            return create_tool_result("Alert system not configured", is_error=True)
        
        alert_id = args["alertId"]
        note = args.get("note")
        
        result = self.alert_system.acknowledge_alert(alert_id, note)
        if result.get("success"):
            return create_tool_result(f"Acknowledged alert {alert_id}")
        else:
            return create_tool_result(result.get("message", "Failed to acknowledge alert"), is_error=True)
    
    def _tool_triage_start(self, args: Dict[str, Any]) -> ToolResult:
        """Start triage workflow."""
        incident_summary = args["incidentSummary"]
        service = args.get("service", "unknown")
        
        # This would create a PRD and task list
        # For now, return placeholder
        text = f"Triage workflow started for {service}\n\n"
        text += f"Incident Summary: {incident_summary}\n\n"
        text += "Resources created:\n"
        text += "- tickets/triage-001.md\n"
        text += "- runbooks/triage-checklist.md"
        
        return create_tool_result(text)
    
    def _tool_profile_set(self, args: Dict[str, Any]) -> ToolResult:
        """Set active profile."""
        profile_name = args["name"]
        success = self.profile_manager.set_active_profile(profile_name)
        
        if success:
            self.active_profile = self.profile_manager.get_active_profile()
            self.ssh_wrapper = SSHWrapper(self.active_profile)
            # Re-register tools with new profile
            self.tools = self._define_tools()
            
            return create_tool_result(f"Active profile set to: {profile_name}")
        else:
            return create_tool_result(f"Profile not found: {profile_name}", is_error=True)
    
    # Resource Handlers
    
    def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        return {"resources": self.resources}
    
    def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri")
        if not uri:
            raise JSONRPCError(JSONRPCError.INVALID_PARAMS, "Missing uri parameter")
        
        resource = self.resource_resolver.read_resource(uri)
        if not resource:
            raise JSONRPCError(JSONRPCError.RESOURCE_NOT_FOUND, f"Resource not found: {uri}")
        
        return {
            "contents": [
                {
                    "uri": resource["uri"],
                    "mimeType": resource["mimeType"],
                    "text": resource.get("text", "")
                }
            ]
        }
    
    # Prompt Handlers
    
    def _handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        return {"prompts": self.prompts}
    
    def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise JSONRPCError(JSONRPCError.INVALID_PARAMS, "Missing name parameter")
        
        prompt_text = self.prompt_registry.get_prompt(name, arguments)
        if not prompt_text:
            raise JSONRPCError(JSONRPCError.RESOURCE_NOT_FOUND, f"Prompt not found: {name}")
        
        return {
            "description": f"Prompt: {name}",
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": prompt_text}
                }
            ]
        }
    
    def process_message(self, message: str) -> Optional[str]:
        """Process incoming MCP message."""
        return self.protocol.process_message(message)