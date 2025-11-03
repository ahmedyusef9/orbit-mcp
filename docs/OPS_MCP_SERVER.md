# Ops MCP Server - Global DevOps Operations Server

## Overview

The Ops MCP Server is a production-ready, globally deployable MCP server that provides secure DevOps operations through Cursor and other AI assistants. It supports per-account customization via profiles and integrates SSH, ticketing, alerts, and workflow automation.

## Features

### Core Capabilities

- ? **Tools** - 11+ actionable tools for SSH, tickets, alerts, workflows
- ? **Resources** - Read-only access to runbooks, ticket metadata, incidents
- ? **Prompts** - Reusable templates for triage, rollback, deployment verification
- ? **Profiles** - Per-account customization (prod, staging, dev)
- ? **Security** - Allow-listed commands, secret redaction, audit logging

### Tools

#### SSH Operations
- `ssh.run` - Execute allow-listed commands on remote hosts
- `ssh.tail` - Stream logs from remote servers
- `ssh.healthcheck` - Run diagnostic bundle

#### Ticket Management
- `ticket.create` - Create tickets (Jira/GitHub)
- `ticket.updateStatus` - Update ticket status
- `ticket.comment` - Add comments to tickets

#### Alert Management
- `alert.list` - List alerts with filtering
- `alert.get` - Get specific alert details
- `alert.ack` - Acknowledge alerts

#### Workflow Automation
- `triage.start` - Start incident triage workflow
- `profile.set` - Switch active profile

### Resources

- `runbooks/<service>.md` - Service runbooks from Confluence/wiki
- `tickets/<id>.md` - Ticket metadata
- `incidents/current` - Current active incidents

### Prompts

- `triage` - Triage a defect
- `rollback` - Prepare rollback plan
- `deploy_verify` - Verify deployment

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
# Also install: paramiko, requests, pyyaml
```

### 2. Create Configuration

```bash
# Global config
sudo mkdir -p /etc/ops-mcp
sudo cp configs/ops-mcp.config.example.yaml /etc/ops-mcp/config.yaml
sudo vim /etc/ops-mcp/config.yaml  # Edit with your settings
```

### 3. Configure Cursor (Global)

Create/edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ops-global": {
      "command": "python3",
      "args": ["-m", "src.mcp.ops_main", "--transport", "stdio"],
      "env": {
        "MCP_PROFILE": "prod",
        "OPS_CONFIG": "/etc/ops-mcp/config.yaml",
        "JIRA_EMAIL": "${JIRA_EMAIL}",
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}",
        "GITHUB_TOKEN": "${GITHUB_TOKEN}",
        "ALERTA_API_KEY": "${ALERTA_API_KEY}"
      }
    }
  }
}
```

### 4. Set Environment Variables

```bash
export JIRA_EMAIL="your@email.com"
export JIRA_API_TOKEN="your-token"
export GITHUB_TOKEN="ghp_..."
export ALERTA_API_KEY="your-key"
```

### 5. Restart Cursor

Cursor will automatically detect and connect to the Ops MCP Server.

## Configuration

### Profile Structure

Each profile defines:
- **SSH hosts** - Remote servers with connection details
- **Allowed commands** - Command key ? template mapping
- **Redaction rules** - Regex patterns for secret detection
- **Ticket settings** - Project, labels, system type
- **Alert settings** - Endpoint, namespace
- **Knowledge base** - Confluence/wiki configuration

### Example Profile

```yaml
profiles:
  prod:
    ssh:
      hosts:
        prod-web-01:
          host: 192.168.1.100
          user: admin
          key_path: ~/.ssh/id_rsa
      
      allowed_commands:
        service_status:
          template: "systemctl status {service_name}"
        
        disk_usage:
          template: "df -h"
    
    tickets:
      system: jira
      project: PROD
      labels: [production, ops]
```

### Security

#### Command Allow-Listing

Only commands in the `allowed_commands` section can be executed. The AI must use command keys (e.g., `service_status`) not raw shell commands.

#### Secret Redaction

Automatic redaction of:
- Passwords (`password: value`)
- API keys (`api_key: value`)
- Tokens (`token: value`)
- Email addresses
- Credit card numbers

Custom patterns via `redaction_rules` in profile config.

#### Audit Logging

All tool calls are logged server-side with:
- Timestamp
- Profile name
- Tool name
- Arguments (hashed for sensitive data)
- Host (if applicable)
- Exit code
- Byte counts

## Usage Examples

### In Cursor

```
User: Check disk usage on prod-web-01
AI: [Calls ssh.run] Disk usage: / 45%, /var 78%...

User: Create a ticket for service outage
AI: [Calls ticket.create] Created ticket PROD-1234...

User: List all open alerts
AI: [Calls alert.list] Found 3 open alerts: ...

User: Switch to staging profile
AI: [Calls profile.set] Active profile set to: staging
```

### Tool Contracts

#### ssh.run

```json
{
  "name": "ssh.run",
  "arguments": {
    "host": "prod-web-01",
    "cmd": "service_status",
    "args": {
      "service_name": "nginx"
    },
    "timeoutSec": 30
  }
}
```

**Response:**
- `success`: boolean
- `exit_code`: integer
- `stdout`: string (redacted if needed)
- `stderr`: string
- `was_redacted`: boolean

**Errors:**
- `PERMISSION_DENIED` - Command not in allow-list
- `TIMEOUT` - Command exceeded timeout
- `HOST_UNREACHABLE` - SSH connection failed
- `REDACTION_TRIGGERED` - Output contained secrets

## Per-Project Customization

Create `.cursor/ops-config.yaml` in your project:

```yaml
default_profile: staging

profiles:
  staging:
    ssh:
      hosts:
        staging-api-01:
          host: staging-api.internal
          user: deploy
          key_path: ~/.ssh/staging_key
```

This overrides global config for project-specific settings.

## Architecture

```
???????????????????
?   Cursor AI     ?
???????????????????
         ? MCP (stdio)
         ?
???????????????????????????????????
?   Ops MCP Server                ?
?   ????????????????????????????  ?
?   ?  Profile Manager         ?  ?
?   ?  - Active profile        ?  ?
?   ?  - Profile switching     ?  ?
?   ????????????????????????????  ?
?              ?                   ?
?   ????????????????????????????  ?
?   ?  SSH Wrapper             ?  ?
?   ?  - Allow-listing         ?  ?
?   ?  - Secret redaction      ?  ?
?   ????????????????????????????  ?
?   ????????????????????????????  ?
?   ?  Ticket System           ?  ?
?   ?  - Jira/GitHub           ?  ?
?   ????????????????????????????  ?
?   ????????????????????????????  ?
?   ?  Alert System            ?  ?
?   ?  - Alerta/SLM            ?  ?
?   ????????????????????????????  ?
?   ????????????????????????????  ?
?   ?  Resources & Prompts     ?  ?
?   ?  - Runbooks              ?  ?
?   ?  - Templates             ?  ?
?   ????????????????????????????  ?
????????????????????????????????????
```

## Testing

### Test Server Independently

```bash
python3 -m src.mcp.ops_main --transport stdio --verbose
```

### Test with MCP Inspector

```bash
npm i -g @modelcontextprotocol/inspector
mcp-inspector "python3 -m src.mcp.ops_main --transport stdio"
```

### Manual JSON-RPC Test

```bash
# Initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
  python3 -m src.mcp.ops_main --transport stdio

# List tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
  python3 -m src.mcp.ops_main --transport stdio
```

## Security Best Practices

1. **Use SSH keys** - Never store passwords
2. **Restrict command allow-list** - Only include necessary commands
3. **Use bastion hosts** - For production environments
4. **Store secrets in env vars** - Never in config files
5. **Review audit logs** - Regularly check tool usage
6. **Use profiles** - Separate prod/staging/dev access
7. **Enable redaction** - Protect sensitive output

## Troubleshooting

### Server Won't Start

- Check config file path and syntax
- Verify environment variables are set
- Check logs: `--verbose` flag

### Commands Fail

- Verify command key is in allow-list
- Check SSH connectivity manually
- Review command template rendering

### Profile Not Found

- Check `MCP_PROFILE` env var
- Verify profile exists in config
- Check default_profile setting

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Cursor MCP Docs](https://cursor.sh/docs)
- Configuration examples in `configs/` directory

---

**Ops MCP Server provides secure, profile-based DevOps operations through AI assistants.**