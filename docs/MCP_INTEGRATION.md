# MCP Server - Model Context Protocol Integration

## Overview

The MCP Server now implements the **Model Context Protocol** (MCP), making it compatible with MCP clients like Cursor. This allows AI assistants to securely invoke DevOps tools through a standardized JSON-RPC 2.0 based protocol.

## What is MCP?

The Model Context Protocol (MCP) is an open standard that enables seamless integration between AI assistants and external tools/data sources. MCP provides:

- **Standardized communication** via JSON-RPC 2.0
- **Tool discovery** and invocation
- **Secure execution** with user approval
- **Multiple transports** (STDIO, HTTP+SSE)

## Architecture

```
???????????????????????
?  MCP Client         ?
?  (Cursor, Claude)   ?
???????????????????????
           ? JSON-RPC 2.0
           ? (STDIO or HTTP+SSE)
           ?
???????????????????????
?  MCP DevOps Server  ?
?  ?????????????????  ?
?  ? Protocol      ?  ?
?  ? Handler       ?  ?
?  ?????????????????  ?
?  ?????????????????  ?
?  ? Tool Registry ?  ?
?  ?????????????????  ?
?  ?????????????????  ?
?  ? SSH Manager   ?  ?
?  ? Docker Mgr    ?  ?
?  ? K8s Manager   ?  ?
?  ?????????????????  ?
???????????????????????
           ?
           ?
???????????????????????
?  Infrastructure     ?
?  ? Servers          ?
?  ? Containers       ?
?  ? K8s Clusters     ?
???????????????????????
```

## MCP Server Features

### Protocol Implementation

The MCP Server implements the complete MCP protocol:

- ? **initialize** - Handshake and capability negotiation
- ? **initialized** - Client ready notification
- ? **ping** - Connection health check
- ? **tools/list** - Discover available DevOps tools
- ? **tools/call** - Execute DevOps operations

### Supported Transports

#### 1. STDIO Transport (Local)

Best for local integration with IDE tools like Cursor.

```bash
# Start MCP server with STDIO
mcp-server --transport stdio
```

- Communication via stdin/stdout
- No network exposure
- Secure by default
- Recommended for local development

#### 2. HTTP+SSE Transport (Network)

For remote deployments or web-based clients.

```bash
# Start MCP server with HTTP
mcp-server --transport http --host 127.0.0.1 --port 3000
```

- REST API endpoint
- Server-Sent Events for streaming
- Suitable for remote access
- Requires network security measures

## Available Tools

The MCP Server exposes the following DevOps tools:

### SSH Operations

1. **ssh_execute**
   - Execute shell commands on remote servers
   - Input: server name, command, timeout
   - Output: stdout, stderr, exit code
   - Example: Check disk usage, restart services

### Docker Management

2. **docker_list_containers**
   - List all Docker containers
   - Input: show all (boolean)
   - Output: Container list with status

3. **docker_start_container**
   - Start a Docker container
   - Input: container name/ID
   
4. **docker_stop_container**
   - Stop a Docker container
   - Input: container name/ID, timeout

5. **docker_restart_container**
   - Restart a Docker container
   
6. **docker_logs**
   - Fetch container logs
   - Input: container, tail lines
   - Output: Log content

### Kubernetes Operations

7. **k8s_list_pods**
   - List pods in a namespace
   - Input: namespace, cluster (optional)
   - Output: Pod list with status

8. **k8s_get_pod**
   - Get detailed pod information
   - Input: pod name, namespace
   
9. **k8s_logs**
   - Fetch pod logs
   - Input: pod, namespace, container, tail

10. **k8s_scale_deployment**
    - Scale a deployment
    - Input: deployment, replicas, namespace

11. **k8s_restart_deployment**
    - Restart a deployment
    - Input: deployment, namespace

### System Monitoring

12. **query_logs**
    - Query log files from servers
    - Input: server, log path, filter, tail

13. **system_info**
    - Get system information
    - Input: server name

14. **disk_usage**
    - Get disk usage statistics
    - Input: server name

## Integration with Cursor

### Setup for Cursor

1. **Install MCP Server**

```bash
cd /workspace
pip install -e .
```

2. **Configure Cursor**

Create or edit Cursor's MCP configuration file:

**On macOS/Linux:** `~/.cursor/mcp_config.json`
**On Windows:** `%APPDATA%\Cursor\mcp_config.json`

```json
{
  "mcpServers": {
    "devops": {
      "command": "mcp-server",
      "args": ["--transport", "stdio"],
      "env": {}
    }
  }
}
```

3. **Initialize MCP Configuration**

```bash
# Initialize your MCP configuration
mcp config init

# Add your servers
mcp config add-ssh prod-server server.example.com user --key ~/.ssh/id_rsa
mcp config add-k8s prod-k8s ~/.kube/config --context prod-cluster
```

4. **Restart Cursor**

Cursor will automatically detect and connect to the MCP server.

### Using in Cursor

Once configured, you can interact with your infrastructure through Cursor's AI:

**Example Prompts:**

- "Check the disk usage on prod-server"
- "List all running Docker containers"
- "Get logs from the api-pod in the production namespace"
- "Scale the web-deployment to 5 replicas"
- "Execute 'systemctl status nginx' on prod-server"

Cursor will:
1. Recognize your request as a DevOps operation
2. Call the appropriate MCP tool
3. Ask for your confirmation (security feature)
4. Execute the operation
5. Display the results

### Security & Permissions

#### User Approval Required

Cursor will **always ask for permission** before executing tools. This ensures:
- No unauthorized operations
- User awareness of all actions
- Ability to review parameters before execution

#### Configuration Security

- MCP Server uses your existing `~/.mcp/config.yaml`
- Credentials are stored with restricted permissions (0600)
- SSH keys are preferred over passwords
- All operations logged to stderr

## API Reference

### Initialize Handshake

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": {},
      "sampling": {}
    },
    "clientInfo": {
      "name": "cursor",
      "version": "1.0.0"
    }
  }
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "mcp-devops-server",
      "version": "0.1.0"
    },
    "capabilities": {
      "tools": {
        "listChanged": false
      }
    }
  }
}
```

### List Tools

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}

// Response
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "ssh_execute",
        "description": "Execute a shell command on a remote server via SSH",
        "inputSchema": {
          "type": "object",
          "properties": {
            "server": {
              "type": "string",
              "description": "Server name from configuration"
            },
            "command": {
              "type": "string",
              "description": "Shell command to execute"
            }
          },
          "required": ["server", "command"]
        }
      }
      // ... more tools ...
    ]
  }
}
```

### Call Tool

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "ssh_execute",
    "arguments": {
      "server": "prod-server",
      "command": "uptime"
    }
  }
}

// Response - Success
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Exit Code: 0\n\nSTDOUT:\n 14:23:45 up 10 days,  4:17,  2 users,  load average: 0.00, 0.01, 0.05\n"
      }
    ],
    "isError": false
  }
}

// Response - Error
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "SSH execution failed: Connection timeout"
      }
    ],
    "isError": true
  }
}
```

## Command-Line Usage

### STDIO Mode (Default)

```bash
# Start server (reads from stdin, writes to stdout)
mcp-server

# With custom config
mcp-server --config /path/to/config.yaml

# Verbose logging
mcp-server --verbose
```

### HTTP Mode

```bash
# Start HTTP server on default port (3000)
mcp-server --transport http

# Custom host and port
mcp-server --transport http --host 0.0.0.0 --port 8080

# Access endpoints
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Testing

### Test with JSON-RPC

```bash
# Start server in STDIO mode
mcp-server --verbose

# Send initialization (in another terminal)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | mcp-server

# Send initialized notification
echo '{"jsonrpc":"2.0","method":"initialized","params":{}}' | mcp-server

# List tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | mcp-server
```

### Test with Cursor

1. Configure Cursor (see setup above)
2. Open a project in Cursor
3. Ask the AI: "List all Docker containers"
4. Approve the tool call when prompted
5. View results in the chat

## Error Handling

### JSON-RPC Errors

The server returns standard JSON-RPC error codes:

- `-32700` Parse error
- `-32600` Invalid request
- `-32601` Method not found
- `-32602` Invalid params
- `-32603` Internal error

### Tool Execution Errors

Tool execution errors are returned as successful JSON-RPC responses with `isError: true`:

```json
{
  "content": [
    {"type": "text", "text": "Error message"}
  ],
  "isError": true
}
```

## Logging

Logs are written to **stderr** to avoid interfering with STDIO protocol:

```bash
# View logs while running
mcp-server --verbose 2> mcp-server.log

# Monitor logs
tail -f mcp-server.log
```

## Best Practices

### Security

1. **Use SSH Keys**: Prefer key-based authentication over passwords
2. **Restrict Permissions**: Keep config file permissions at 0600
3. **Review Before Approval**: Always review tool parameters in Cursor
4. **Limit Scope**: Configure only necessary servers/clusters
5. **Monitor Logs**: Regularly check server logs for suspicious activity

### Performance

1. **Connection Pooling**: SSH connections are reused automatically
2. **Timeouts**: Set appropriate command timeouts
3. **Resource Limits**: Be cautious with log tail sizes

### Integration

1. **Test Locally First**: Use STDIO transport for testing
2. **Start Simple**: Begin with read-only tools
3. **Incremental Setup**: Add servers/clusters gradually
4. **Document Tools**: Keep track of what each tool does

## Troubleshooting

### Server Won't Start

```bash
# Check if port is in use (HTTP mode)
lsof -i :3000

# Verify configuration
mcp config list

# Test with verbose logging
mcp-server --verbose
```

### Cursor Can't Connect

1. Check Cursor's MCP configuration file
2. Ensure `mcp-server` is in PATH
3. Restart Cursor after configuration changes
4. Check Cursor logs for connection errors

### Tool Execution Fails

1. Verify server configuration: `mcp config list`
2. Test SSH connectivity manually
3. Check credentials and permissions
4. Review server logs for detailed errors

### Authentication Issues

```bash
# Test SSH manually
ssh -i ~/.ssh/id_rsa user@server

# Verify key permissions
chmod 600 ~/.ssh/id_rsa

# Check server config
cat ~/.mcp/config.yaml
```

## Advanced Configuration

### Multiple Environments

```json
{
  "mcpServers": {
    "devops-prod": {
      "command": "mcp-server",
      "args": ["--config", "~/.mcp/prod-config.yaml"]
    },
    "devops-staging": {
      "command": "mcp-server",
      "args": ["--config", "~/.mcp/staging-config.yaml"]
    }
  }
}
```

### Custom Tool Timeouts

Edit tool implementations in `src/mcp/mcp_server.py` to adjust timeouts.

### Adding New Tools

1. Define tool schema in `_define_tools()`
2. Implement handler method (e.g., `_tool_my_operation()`)
3. Add handler to `handler_map` in `_handle_tools_call()`
4. Restart server

## Future Enhancements

Planned features for future versions:

- **Streaming Support**: Real-time log streaming via SSE
- **Resource Support**: Expose files and data as MCP resources
- **Prompt Templates**: Predefined DevOps workflows
- **Progress Notifications**: Long-running operation updates
- **Tool Composition**: Chain multiple tools together
- **Authentication**: OAuth/API key support for HTTP transport
- **Rate Limiting**: Prevent abuse in HTTP mode

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol)
- [Cursor Documentation](https://cursor.sh/docs)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

## Support

For issues or questions:
- Check logs: `mcp-server --verbose`
- Review configuration: `mcp config list`
- Test connectivity: Manual SSH/Docker/K8s access
- Open an issue on GitHub

---

**The MCP Server bridges AI assistants with DevOps infrastructure through a secure, standardized protocol.**
