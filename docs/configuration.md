# MCP Server Configuration Guide

This document provides detailed information about configuring MCP Server for your environment.

## Configuration File Location

MCP Server uses a YAML configuration file located at:
```
~/.mcp/config.yaml
```

You can specify a custom location using the `--config` flag:
```bash
mcp --config /path/to/custom/config.yaml [command]
```

## Configuration File Structure

### Complete Configuration Example

```yaml
version: "1.0"

# SSH Server Configurations
ssh_servers:
  - name: prod-web
    host: web.example.com
    user: deploy
    port: 22
    key_path: ~/.ssh/prod_key
  
  - name: dev-server
    host: dev.example.com
    user: developer
    port: 22
    key_path: ~/.ssh/dev_key

# Docker Host Configurations
docker_hosts:
  - name: local-docker
    host: localhost
    connection_type: local
  
  - name: remote-docker
    host: docker.example.com
    connection_type: ssh
    ssh_config:
      user: admin
      key_path: ~/.ssh/docker_key
      port: 22

# Kubernetes Cluster Configurations
kubernetes_clusters:
  - name: prod-k8s
    kubeconfig_path: ~/.kube/config
    context: prod-cluster
  
  - name: staging-k8s
    kubeconfig_path: ~/.kube/staging-config
    context: staging-context

# Command Aliases
aliases:
  restart-app: "systemctl restart myapp"
  check-disk: "df -h"
  app-status: "systemctl status myapp"
  deploy-frontend: "cd /app/frontend && git pull && docker-compose up -d"

# General Settings
settings:
  log_level: INFO
  timeout: 30
  retry_count: 3
  colored_output: true
  default_k8s_namespace: default
  default_log_lines: 100
```

## Configuration Sections

### SSH Servers

Defines SSH servers for remote access.

```yaml
ssh_servers:
  - name: server-name          # Unique identifier
    host: hostname.example.com # Server hostname or IP
    user: username             # SSH username
    port: 22                   # SSH port (default: 22)
    key_path: ~/.ssh/key_file  # Path to private key
    password: optional         # Password (not recommended)
```

#### Parameters:

- **name** (required): Unique name to identify this server
- **host** (required): Server hostname or IP address
- **user** (required): SSH username
- **port** (optional): SSH port, defaults to 22
- **key_path** (optional): Path to SSH private key file
- **password** (optional): SSH password (use keys instead when possible)

#### Authentication Methods:

1. **SSH Key (Recommended)**
   ```bash
   mcp config add-ssh prod-server host user --key ~/.ssh/id_rsa
   ```

2. **SSH Agent**
   - If neither `key_path` nor `password` is specified, MCP will try SSH agent
   - Most secure option for development machines

3. **Password (Not Recommended)**
   ```bash
   mcp config add-ssh server host user --password 'mypass'
   ```
   ?? Stores password in plain text

### Docker Hosts

Defines Docker hosts for container management.

```yaml
docker_hosts:
  - name: docker-host-name
    host: docker.example.com
    connection_type: ssh        # 'local' or 'ssh'
    ssh_config:                 # Required if connection_type is 'ssh'
      user: username
      key_path: ~/.ssh/key
      port: 22
```

#### Parameters:

- **name** (required): Unique identifier for this Docker host
- **host** (required): Docker host address
- **connection_type** (required): Either `local` or `ssh`
- **ssh_config** (optional): SSH configuration for remote access

#### Connection Types:

1. **Local Docker**
   ```yaml
   docker_hosts:
     - name: local
       host: localhost
       connection_type: local
   ```

2. **Remote Docker via SSH**
   ```yaml
   docker_hosts:
     - name: remote
       host: docker.example.com
       connection_type: ssh
       ssh_config:
         user: admin
         key_path: ~/.ssh/docker_key
   ```

### Kubernetes Clusters

Defines Kubernetes clusters for orchestration.

```yaml
kubernetes_clusters:
  - name: cluster-name
    kubeconfig_path: ~/.kube/config
    context: cluster-context
```

#### Parameters:

- **name** (required): Unique identifier for this cluster
- **kubeconfig_path** (required): Path to kubeconfig file
- **context** (optional): Specific context to use from kubeconfig

#### Multiple Clusters:

```yaml
kubernetes_clusters:
  # Production cluster
  - name: prod-k8s
    kubeconfig_path: ~/.kube/config
    context: prod-cluster
  
  # Staging cluster (different kubeconfig)
  - name: staging-k8s
    kubeconfig_path: ~/.kube/staging-config
    context: staging-cluster
  
  # AWS EKS cluster
  - name: eks-prod
    kubeconfig_path: ~/.kube/eks-config
    context: arn:aws:eks:region:account:cluster/name
```

### Command Aliases

Define shortcuts for frequently used commands.

```yaml
aliases:
  alias-name: "command to execute"
```

#### Examples:

```yaml
aliases:
  # Service management
  restart-nginx: "sudo systemctl restart nginx"
  stop-app: "systemctl stop myapp"
  
  # System checks
  check-disk: "df -h"
  check-memory: "free -h"
  
  # Multi-step operations
  deploy-app: "cd /app && git pull && docker-compose up -d"
  
  # Log viewing
  app-errors: "tail -100 /var/log/app/error.log | grep ERROR"
```

#### Using Aliases:

```bash
# Instead of:
mcp ssh exec server "systemctl restart nginx"

# Use:
mcp ssh exec server restart-nginx
```

### General Settings

Global configuration settings.

```yaml
settings:
  log_level: INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
  timeout: 30                        # Connection timeout (seconds)
  retry_count: 3                     # Number of retry attempts
  colored_output: true               # Enable colored terminal output
  default_k8s_namespace: default     # Default Kubernetes namespace
  default_log_lines: 100             # Default number of log lines to tail
```

#### Log Levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages
- **ERROR**: Error messages only
- **CRITICAL**: Critical errors only

## Managing Configuration

### Command-Line Configuration

#### Initialize Configuration

```bash
mcp config init
```

Creates default configuration file.

#### Add SSH Server

```bash
mcp config add-ssh NAME HOST USER [OPTIONS]

Options:
  --port PORT        SSH port (default: 22)
  --key PATH         Path to SSH private key
  --password PASS    SSH password (not recommended)
```

Examples:
```bash
mcp config add-ssh prod-web web.example.com deploy --key ~/.ssh/prod_key
mcp config add-ssh dev-db db-dev.example.com admin --port 2222
```

#### Add Docker Host

```bash
mcp config add-docker NAME HOST [OPTIONS]

Options:
  --ssh-server NAME  SSH server profile to use
```

Examples:
```bash
mcp config add-docker local localhost
mcp config add-docker remote-docker docker.example.com --ssh-server prod-web
```

#### Add Kubernetes Cluster

```bash
mcp config add-k8s NAME KUBECONFIG [OPTIONS]

Options:
  --context CONTEXT  Kubernetes context
```

Examples:
```bash
mcp config add-k8s prod-k8s ~/.kube/config --context prod-cluster
mcp config add-k8s staging-k8s ~/.kube/staging-config
```

#### Add Alias

```bash
mcp config add-alias NAME "COMMAND"
```

Examples:
```bash
mcp config add-alias restart-app "systemctl restart myapp"
mcp config add-alias check-health "curl localhost:8080/health"
```

#### List Configuration

```bash
mcp config list
```

Shows all configured profiles and aliases.

### Manual Configuration

You can also edit the configuration file directly:

```bash
# Edit with your preferred editor
vim ~/.mcp/config.yaml
nano ~/.mcp/config.yaml
code ~/.mcp/config.yaml
```

After manual edits, verify the configuration:

```bash
mcp config list
```

## Environment-Specific Configurations

### Separate Configurations per Environment

Create different configuration files:

```bash
~/.mcp/config-dev.yaml
~/.mcp/config-staging.yaml
~/.mcp/config-prod.yaml
```

Use with the `--config` flag:

```bash
mcp --config ~/.mcp/config-prod.yaml ssh exec prod-web "uptime"
```

### Shell Aliases

Create shell aliases for convenience:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias mcp-dev="mcp --config ~/.mcp/config-dev.yaml"
alias mcp-staging="mcp --config ~/.mcp/config-staging.yaml"
alias mcp-prod="mcp --config ~/.mcp/config-prod.yaml"

# Usage:
mcp-prod ssh exec server "command"
```

## Configuration Templates

### Development Environment

```yaml
version: "1.0"

ssh_servers:
  - name: dev-app
    host: dev.example.com
    user: developer
    port: 22
    key_path: ~/.ssh/dev_key

docker_hosts:
  - name: local
    host: localhost
    connection_type: local

kubernetes_clusters:
  - name: minikube
    kubeconfig_path: ~/.kube/config
    context: minikube

aliases:
  test-app: "npm test"
  dev-logs: "tail -f /var/log/app/dev.log"

settings:
  log_level: DEBUG
  timeout: 60
```

### Production Environment

```yaml
version: "1.0"

ssh_servers:
  - name: prod-web
    host: web.prod.example.com
    user: deploy
    port: 22
    key_path: ~/.ssh/prod_key
  
  - name: prod-api
    host: api.prod.example.com
    user: deploy
    port: 22
    key_path: ~/.ssh/prod_key

kubernetes_clusters:
  - name: prod-k8s
    kubeconfig_path: ~/.kube/prod-config
    context: prod-cluster

aliases:
  emergency-restart: "systemctl restart critical-service && journalctl -u critical-service -n 50"
  health-check: "curl -f https://api.example.com/health || exit 1"

settings:
  log_level: WARNING
  timeout: 30
  retry_count: 5
```

## Security Best Practices

### File Permissions

MCP automatically sets secure permissions:
- Configuration directory: `0700` (owner only)
- Configuration file: `0600` (owner read/write only)

Verify permissions:
```bash
ls -la ~/.mcp/
```

### Credential Management

1. **Use SSH Keys, Not Passwords**
   ```bash
   # Generate key if needed
   ssh-keygen -t ed25519 -f ~/.ssh/mcp_key
   
   # Add to server
   ssh-copy-id -i ~/.ssh/mcp_key user@server
   
   # Configure MCP
   mcp config add-ssh server host user --key ~/.ssh/mcp_key
   ```

2. **Separate Keys per Environment**
   ```bash
   ~/.ssh/dev_key    # Development
   ~/.ssh/stage_key  # Staging
   ~/.ssh/prod_key   # Production
   ```

3. **Never Commit Configuration**
   - Configuration files are in `.gitignore`
   - Never override this behavior

4. **Regular Rotation**
   - Rotate SSH keys every 90 days
   - Update configuration after rotation

## Troubleshooting

### Configuration Not Found

```bash
# Check if config exists
ls -la ~/.mcp/config.yaml

# Reinitialize if needed
mcp config init
```

### Permission Denied

```bash
# Fix directory permissions
chmod 700 ~/.mcp

# Fix file permissions
chmod 600 ~/.mcp/config.yaml
```

### Invalid YAML Syntax

```bash
# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('~/.mcp/config.yaml'))"
```

### SSH Key Issues

```bash
# Check key permissions
ls -l ~/.ssh/id_rsa
# Should be 600

# Fix if needed
chmod 600 ~/.ssh/id_rsa
```

## Migration and Backup

### Backup Configuration

```bash
# Backup current configuration
cp ~/.mcp/config.yaml ~/.mcp/config.yaml.backup

# With timestamp
cp ~/.mcp/config.yaml ~/.mcp/config.yaml.$(date +%Y%m%d)
```

### Restore Configuration

```bash
# Restore from backup
cp ~/.mcp/config.yaml.backup ~/.mcp/config.yaml
```

### Export/Import

```bash
# Export (sanitized)
mcp config list > mcp-config-export.txt

# Import (manual setup required)
cat mcp-config-export.txt
# Then recreate using config add-* commands
```

---

For more information, see the [main documentation](../README.md) or [security guide](security.md).
