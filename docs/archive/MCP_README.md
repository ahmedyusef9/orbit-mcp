# ?? MCP Server - AI-Powered DevOps Tool

**Transform your DevOps workflow with AI assistance through the Model Context Protocol**

[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blue.svg)](https://modelcontextprotocol.io/)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)]()

---

## ?? What's New: MCP Protocol Support!

The MCP Server now implements the **Model Context Protocol**, enabling seamless integration with AI assistants like **Cursor** and **Claude**. This means you can use natural language to manage your infrastructure!

### Try It in Cursor

```
"Check disk usage on prod-server"
"List all running Docker containers"  
"Get logs from the api-pod in production"
"Scale the web deployment to 5 replicas"
```

Cursor's AI will automatically use the appropriate MCP tools to execute these operations securely!

---

## ?? Two Ways to Use MCP Server

### 1. **Traditional CLI Mode**

Direct command-line access for scripts and manual operations:

```bash
# Execute SSH commands
mcp ssh exec prod-server "uptime"

# Manage Docker containers
mcp docker ps
mcp docker logs my-container -f

# Kubernetes operations
mcp k8s pods -n production
mcp k8s logs my-pod -f
```

### 2. **MCP Protocol Mode** (NEW! ??)

AI-powered access through Cursor or other MCP clients:

```bash
# Start MCP server
mcp-server --transport stdio
```

Then use natural language in Cursor to interact with your infrastructure!

---

## ?? Quick Start

### Installation

```bash
git clone <repository-url>
cd mcp-server
pip install -e .
```

### For CLI Usage

```bash
# Initialize configuration
mcp config init

# Add your servers
mcp config add-ssh prod-server server.example.com user --key ~/.ssh/id_rsa

# Execute commands
mcp ssh exec prod-server "df -h"
```

### For Cursor Integration

1. **Configure Cursor** (`~/.cursor/mcp_config.json`):

```json
{
  "mcpServers": {
    "devops": {
      "command": "mcp-server",
      "args": ["--transport", "stdio"]
    }
  }
}
```

2. **Restart Cursor**

3. **Start using AI commands!**

---

## ??? Available Tools (MCP Mode)

When using MCP Server with Cursor, the AI can access these tools:

### SSH Operations
- **ssh_execute** - Execute commands on remote servers
- **query_logs** - Query and filter log files
- **system_info** - Get system information
- **disk_usage** - Check disk usage

### Docker Management
- **docker_list_containers** - List containers
- **docker_start/stop/restart_container** - Container lifecycle
- **docker_logs** - Fetch container logs

### Kubernetes Operations
- **k8s_list_pods** - List pods in namespace
- **k8s_get_pod** - Get pod details
- **k8s_logs** - Fetch pod logs
- **k8s_scale_deployment** - Scale deployments
- **k8s_restart_deployment** - Restart deployments

All tools require your approval before execution (security feature)!

---

## ?? Documentation

### Complete Guides

- **[MCP Integration Guide](docs/MCP_INTEGRATION.md)** - Full MCP protocol documentation
- **[Quick Start](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Configuration Guide](docs/configuration.md)** - Detailed configuration reference
- **[Security Best Practices](docs/security.md)** - Keep your infrastructure secure
- **[Usage Examples](docs/examples.md)** - Real-world examples and workflows

### For Developers

- **[Contributing Guide](CONTRIBUTING.md)** - Contribute to the project
- **[API Reference](docs/MCP_INTEGRATION.md#api-reference)** - JSON-RPC API documentation

---

## ?? Example Workflows

### Using CLI

```bash
# Check system status
mcp ssh exec prod-server "uptime && free -h && df -h"

# Restart application
mcp docker restart my-app-container

# Scale Kubernetes deployment
mcp k8s scale my-deployment 5 -n production

# View recent errors
mcp ssh logs prod-server /var/log/app/error.log -n 100 | grep ERROR
```

### Using Cursor (Natural Language)

Ask Cursor:

- "What's the disk usage on all production servers?"
- "Show me the last 100 lines of logs from the api-pod"
- "List all stopped Docker containers"
- "Check if the nginx service is running on prod-server"
- "Scale the frontend deployment to 10 replicas"

The AI will translate these to the appropriate MCP tool calls!

---

## ?? Security

### Built-in Security Features

- ? **User Approval Required** - Cursor prompts for confirmation before each operation
- ? **Secure Credential Storage** - Config files have restricted permissions (0600)
- ? **SSH Key Authentication** - Preferred over passwords
- ? **Local-First Design** - No external API calls
- ? **Audit Logging** - All operations logged to stderr

### Best Practices

1. Use SSH keys instead of passwords
2. Limit server access to necessary hosts only
3. Review tool parameters before approving in Cursor
4. Keep configuration files private
5. Regularly rotate credentials

See [Security Guide](docs/security.md) for details.

---

## ?? Features

### Core Capabilities

- **Multi-Environment Access** - SSH, Docker, Kubernetes
- **Secure by Default** - Restricted permissions, key-based auth
- **Two Interfaces** - CLI for automation, MCP for AI interaction
- **Rich Output** - Colored terminal, structured data
- **Connection Pooling** - Efficient resource usage
- **Extensible** - Easy to add new tools and integrations

### MCP-Specific Features

- **Standardized Protocol** - JSON-RPC 2.0 based
- **Tool Discovery** - AI automatically finds available tools
- **Structured Schemas** - Input/output validation
- **Error Handling** - Clear error messages
- **Multiple Transports** - STDIO (local) and HTTP+SSE (network)

---

## ?? System Requirements

- **Python**: 3.8 or higher
- **OS**: Linux, macOS, Windows (WSL)
- **Dependencies**: SSH client, Docker (optional), kubectl (optional)

---

## ??? Roadmap

### Current: Phase 1 ?
- [x] CLI interface
- [x] SSH, Docker, Kubernetes support
- [x] MCP protocol implementation
- [x] Cursor integration

### Phase 2: Enhanced Features
- [ ] Real-time log streaming via SSE
- [ ] MCP resources for file access
- [ ] Encrypted credential storage
- [ ] OS keychain integration

### Phase 3: Advanced Capabilities
- [ ] Plugin system for custom tools
- [ ] Task queuing and scheduling
- [ ] Secret vault integration
- [ ] Multi-user support

### Phase 4: Enterprise Features
- [ ] Web UI dashboard
- [ ] Role-based access control
- [ ] SSO authentication
- [ ] Comprehensive audit system

---

## ?? Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ways to Contribute

- ?? Report bugs
- ?? Suggest features
- ?? Improve documentation
- ?? Submit pull requests
- ? Star the project

---

## ?? License

MIT License - see [LICENSE](LICENSE) file

---

## ?? Acknowledgments

- Built with [Paramiko](https://www.paramiko.org/), [Docker SDK](https://docker-py.readthedocs.io/), and [Kubernetes Client](https://github.com/kubernetes-client/python)
- Implements [Model Context Protocol](https://modelcontextprotocol.io/)
- Compatible with [Cursor](https://cursor.sh/)
- Inspired by DevOps best practices and internal developer platforms

---

## ?? Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourorg/mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourorg/mcp-server/discussions)

---

## ?? Use Cases

### For Developers

- Debug production issues without manual SSH
- View logs from multiple sources
- Check container and pod status
- Quick system diagnostics

### For DevOps

- Automate routine operations
- Provide developer self-service
- Centralize tool access
- Maintain security and audit trail

### For Teams

- Consistent tooling across environments
- Knowledge sharing through AI
- Reduced context switching
- Faster incident response

---

## ?? Integration Examples

### With Cursor

```typescript
// Cursor automatically translates natural language
// "Check the status of all pods in the production namespace"

// To MCP tool call:
{
  "method": "tools/call",
  "params": {
    "name": "k8s_list_pods",
    "arguments": {
      "namespace": "production"
    }
  }
}
```

### With Custom MCP Clients

```python
import json
import subprocess

# Send MCP request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "ssh_execute",
        "arguments": {
            "server": "prod-server",
            "command": "uptime"
        }
    }
}

# Call MCP server
proc = subprocess.Popen(
    ["mcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE
)

response = proc.communicate(
    input=json.dumps(request).encode()
)[0]

result = json.loads(response)
print(result["result"]["content"][0]["text"])
```

---

<div align="center">

**Made with ?? for the DevOps Community**

[? Star on GitHub](https://github.com/yourorg/mcp-server) ? 
[?? Documentation](docs/) ? 
[?? Report Bug](https://github.com/yourorg/mcp-server/issues) ? 
[?? Request Feature](https://github.com/yourorg/mcp-server/issues)

</div>
