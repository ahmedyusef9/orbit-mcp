"""MCP Protocol implementation - JSON-RPC 2.0 based Model Context Protocol."""

import json
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MCPVersion(str, Enum):
    """MCP Protocol versions."""
    V1 = "2024-11-05"


@dataclass
class ServerInfo:
    """Server information for MCP handshake."""
    name: str
    version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ServerCapabilities:
    """MCP server capabilities."""
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.tools is not None:
            result["tools"] = self.tools
        if self.resources is not None:
            result["resources"] = self.resources
        if self.prompts is not None:
            result["prompts"] = self.prompts
        if self.logging is not None:
            result["logging"] = self.logging
        return result


@dataclass
class Tool:
    """MCP Tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    outputSchema: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema
        }
        if self.outputSchema:
            result["outputSchema"] = self.outputSchema
        return result


@dataclass
class ToolResult:
    """Result from a tool execution."""
    content: List[Dict[str, Any]]
    isError: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "isError": self.isError
        }


class JSONRPCError(Exception):
    """JSON-RPC 2.0 error."""
    
    # Standard JSON-RPC error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32003
    
    # MCP-specific error codes
    RESOURCE_NOT_FOUND = -32002
    
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        error = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            error["data"] = self.data
        return error


class MCPProtocol:
    """Model Context Protocol handler."""
    
    def __init__(self, server_info: ServerInfo, capabilities: ServerCapabilities):
        """
        Initialize MCP protocol handler.
        
        Args:
            server_info: Server identification
            capabilities: Server capabilities
        """
        self.server_info = server_info
        self.capabilities = capabilities
        self.initialized = False
        self.client_info = None
        
        # Method handlers
        self.method_handlers: Dict[str, Callable] = {}
        
        # Register core protocol methods
        self._register_core_methods()
    
    def _register_core_methods(self):
        """Register core MCP protocol methods."""
        self.method_handlers["initialize"] = self._handle_initialize
        self.method_handlers["ping"] = self._handle_ping
    
    def register_method(self, method: str, handler: Callable):
        """
        Register a method handler.
        
        Args:
            method: Method name
            handler: Handler function
        """
        self.method_handlers[method] = handler
        logger.debug(f"Registered method handler: {method}")
    
    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle initialize request.
        
        Args:
            params: Initialize parameters (protocolVersion, capabilities, clientInfo)
            
        Returns:
            Initialize response with server info and capabilities
        """
        logger.info("Handling initialize request")
        
        # Extract client info
        self.client_info = params.get("clientInfo", {})
        protocol_version = params.get("protocolVersion")
        client_capabilities = params.get("capabilities", {})
        
        logger.info(f"Client: {self.client_info.get('name', 'unknown')} "
                   f"v{self.client_info.get('version', 'unknown')}")
        logger.info(f"Protocol version: {protocol_version}")
        
        # Validate protocol version
        if protocol_version != MCPVersion.V1:
            logger.warning(f"Client requested unsupported protocol version: {protocol_version}")
        
        # Return server capabilities
        return {
            "protocolVersion": MCPVersion.V1,
            "serverInfo": self.server_info.to_dict(),
            "capabilities": self.capabilities.to_dict()
        }
    
    def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle ping request.
        
        Args:
            params: Ping parameters (typically empty)
            
        Returns:
            Empty result
        """
        logger.debug("Handling ping request")
        return {}
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a JSON-RPC request.
        
        Args:
            request: JSON-RPC request object
            
        Returns:
            JSON-RPC response object
        """
        # Validate JSON-RPC structure
        if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
            raise JSONRPCError(
                JSONRPCError.INVALID_REQUEST,
                "Missing or invalid jsonrpc version"
            )
        
        if "method" not in request:
            raise JSONRPCError(
                JSONRPCError.INVALID_REQUEST,
                "Missing method field"
            )
        
        method = request["method"]
        params = request.get("params", {})
        request_id = request.get("id")
        
        logger.debug(f"Processing request: {method} (id: {request_id})")
        
        # Check if method exists
        if method not in self.method_handlers:
            raise JSONRPCError(
                JSONRPCError.METHOD_NOT_FOUND,
                f"Method not found: {method}"
            )
        
        # Check initialization for non-initialize methods
        if method != "initialize" and method != "ping" and not self.initialized:
            if method == "initialized":
                # Handle initialized notification
                self.initialized = True
                logger.info("Client sent initialized notification")
                # Notifications don't get responses
                return None
            
            raise JSONRPCError(
                JSONRPCError.INVALID_REQUEST,
                "Server not initialized"
            )
        
        # Call method handler
        try:
            result = self.method_handlers[method](params)
            
            # Mark as initialized after successful initialize
            if method == "initialize":
                # Don't set initialized yet - wait for initialized notification
                pass
            
            # Build response
            if request_id is not None:  # Not a notification
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                return response
            else:
                # Notification - no response
                return None
                
        except JSONRPCError:
            raise
        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            raise JSONRPCError(
                JSONRPCError.INTERNAL_ERROR,
                f"Internal error: {str(e)}"
            )
    
    def create_error_response(self, error: JSONRPCError, request_id: Any = None) -> Dict[str, Any]:
        """
        Create a JSON-RPC error response.
        
        Args:
            error: JSONRPCError instance
            request_id: Request ID (or None for parse errors)
            
        Returns:
            JSON-RPC error response
        """
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error.to_dict()
        }
    
    def process_message(self, message: str) -> Optional[str]:
        """
        Process a JSON-RPC message and return response.
        
        Args:
            message: JSON-RPC request string
            
        Returns:
            JSON-RPC response string (or None for notifications)
        """
        try:
            # Parse request
            try:
                request = json.loads(message)
            except json.JSONDecodeError as e:
                error = JSONRPCError(
                    JSONRPCError.PARSE_ERROR,
                    f"Parse error: {str(e)}"
                )
                return json.dumps(self.create_error_response(error))
            
            # Handle batch requests
            if isinstance(request, list):
                responses = []
                for req in request:
                    try:
                        response = self.handle_request(req)
                        if response is not None:  # Not a notification
                            responses.append(response)
                    except JSONRPCError as e:
                        responses.append(
                            self.create_error_response(e, req.get("id"))
                        )
                
                # Return batch response (empty if all notifications)
                if responses:
                    return json.dumps(responses)
                return None
            
            # Handle single request
            try:
                response = self.handle_request(request)
                if response is not None:
                    return json.dumps(response)
                return None
            except JSONRPCError as e:
                return json.dumps(
                    self.create_error_response(e, request.get("id"))
                )
        
        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}", exc_info=True)
            error = JSONRPCError(
                JSONRPCError.INTERNAL_ERROR,
                f"Internal error: {str(e)}"
            )
            return json.dumps(self.create_error_response(error))
    
    def send_notification(self, method: str, params: Dict[str, Any]) -> str:
        """
        Create a notification message (no response expected).
        
        Args:
            method: Notification method
            params: Notification parameters
            
        Returns:
            JSON-RPC notification string
        """
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        return json.dumps(notification)


def create_text_content(text: str) -> Dict[str, Any]:
    """
    Create a text content item for tool results.
    
    Args:
        text: Text content
        
    Returns:
        Content item dict
    """
    return {
        "type": "text",
        "text": text
    }


def create_tool_result(content: str, is_error: bool = False) -> ToolResult:
    """
    Create a tool result.
    
    Args:
        content: Result text
        is_error: Whether this is an error result
        
    Returns:
        ToolResult instance
    """
    return ToolResult(
        content=[create_text_content(content)],
        isError=is_error
    )


def create_structured_tool_result(
    text: str,
    structured_data: Dict[str, Any],
    is_error: bool = False
) -> ToolResult:
    """
    Create a tool result with both text and structured content.
    
    Args:
        text: Human-readable text
        structured_data: Machine-readable structured data
        is_error: Whether this is an error result
        
    Returns:
        ToolResult instance
    """
    content = [create_text_content(text)]
    
    # Add structured content
    content.append({
        "type": "resource",
        "resource": {
            "uri": "mcp://result/structured",
            "mimeType": "application/json",
            "text": json.dumps(structured_data, indent=2)
        }
    })
    
    return ToolResult(content=content, isError=is_error)
