# MCP Server - Quick Start Guide

Get up and running with MCP Server in 5 minutes!

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-server

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install MCP Server
pip install -e .

# Verify installation
mcp --help
```

## Initial Configuration

### Step 1: Initialize Configuration

```bash
mcp config init
```

This creates `~/.mcp/config.yaml` with default settings.

### Step 2: Add Your First Server

```bash
mcp config add-ssh my-server \
    your-server.example.com \
    your-username \
    --key ~/.ssh/id_rsa
```

### Step 3: Test Connection

```bash
mcp ssh exec my-server "echo 'Hello from MCP Server!'"
```

## Common Operations

### Execute Remote Commands

```bash
# Check system status
mcp ssh exec my-server "uptime"

# View disk usage
mcp ssh exec my-server "df -h"

# Check running processes
mcp ssh exec my-server "ps aux | head -10"
```

### View Logs

```bash
# Tail log file
mcp ssh logs my-server /var/log/syslog -n 50

# Follow logs in real-time
mcp ssh logs my-server /var/log/app/app.log -f
```

### Docker Operations

```bash
# List containers
mcp docker ps

# View container logs
mcp docker logs my-container -n 100

# Restart container
mcp docker restart my-container
```

### Kubernetes Operations

```bash
# Add Kubernetes cluster
mcp config add-k8s my-cluster ~/.kube/config

# List pods
mcp k8s pods -n default

# View pod logs
mcp k8s logs my-pod -n default

# Scale deployment
mcp k8s scale my-deployment 3 -n default
```

## Create Shortcuts

```bash
# Add common commands as aliases
mcp config add-alias restart-app "systemctl restart myapp"
mcp config add-alias check-health "curl http://localhost:8080/health"

# Use alias
mcp ssh exec my-server restart-app
```

## View All Configurations

```bash
mcp config list
```

## Next Steps

- Read the [full documentation](../README.md)
- Check out [usage examples](examples.md)
- Review [security best practices](security.md)

## Troubleshooting

### Connection Issues

```bash
# Verify SSH key permissions
chmod 600 ~/.ssh/id_rsa

# Test SSH manually
ssh -i ~/.ssh/id_rsa username@server.example.com

# Enable verbose mode
mcp --verbose ssh exec my-server "uptime"
```

### Configuration Issues

```bash
# View current configuration
cat ~/.mcp/config.yaml

# Reconfigure server
mcp config add-ssh my-server server.example.com username --key ~/.ssh/id_rsa
```

## Getting Help

```bash
# General help
mcp --help

# Command-specific help
mcp ssh --help
mcp docker --help
mcp k8s --help
```

---

?? You're ready to start using MCP Server!
