# MCP Server - Multi-Cloud Platform Management Tool

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**MCP Server** is an internal DevOps tool that empowers developers and DevOps teams to manage and interact with various environments (on-premises servers and cloud instances) from a unified command-line interface.

## ?? Overview

MCP Server provides a single, secure interface for managing:
- **SSH Access** - Execute remote commands on Linux servers
- **Docker Management** - Control containers across different hosts
- **Kubernetes Operations** - Manage pods, services, and deployments
- **Log Access** - Retrieve and tail logs from multiple sources
- **Command Aliases** - Create shortcuts for frequently used operations

## ? Key Features

### Multi-Environment Support
- Connect to on-premises servers, AWS EC2, Azure VMs, and more
- Manage multiple environments from one tool
- Switch between contexts seamlessly

### Secure Credential Management
- Store credentials in local configuration files (with restricted permissions)
- Support for SSH keys, passwords, and Kubernetes configs
- Future integration with secret management systems (Vault, AWS Secrets Manager)

### Comprehensive Operations
- **SSH**: Execute commands, tail logs, transfer files
- **Docker**: List, start, stop, restart containers; view logs and stats
- **Kubernetes**: Manage pods, services, deployments; scale and restart workloads
- **Aliases**: Define custom shortcuts for complex command sequences

### Developer-Friendly CLI
- Rich terminal output with tables and colors
- Intuitive command structure
- Verbose mode for debugging

## ?? Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- SSH client installed on your system
- (Optional) Docker for local Docker operations
- (Optional) kubectl for Kubernetes operations

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd mcp-server

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install MCP in development mode
pip install -e .
```

### Verify Installation

```bash
mcp --help
```

## ?? Quick Start

### 1. Initialize Configuration

```bash
mcp config init
```

This creates a configuration directory at `~/.mcp/config.yaml`.

### 2. Add Your First SSH Server

```bash
mcp config add-ssh prod-server \
    server.example.com \
    myuser \
    --key ~/.ssh/id_rsa \
    --port 22
```

### 3. Execute a Remote Command

```bash
mcp ssh exec prod-server "uptime"
```

### 4. Tail Remote Logs

```bash
mcp ssh logs prod-server /var/log/app/app.log -n 100 -f
```

## ?? Usage Guide

### Configuration Management

#### List All Configured Profiles

```bash
mcp config list
```

#### Add Docker Host

```bash
mcp config add-docker my-docker-host docker.example.com --ssh-server prod-server
```

#### Add Kubernetes Cluster

```bash
mcp config add-k8s prod-k8s ~/.kube/config --context prod-cluster
```

#### Create Command Alias

```bash
mcp config add-alias restart-app "systemctl restart myapp"
```

### SSH Operations

#### Execute Single Command

```bash
mcp ssh exec prod-server "df -h"
```

#### Execute Alias

```bash
mcp ssh exec prod-server restart-app
```

#### Tail Logs

```bash
# Last 50 lines
mcp ssh logs prod-server /var/log/app/error.log

# Follow logs in real-time
mcp ssh logs prod-server /var/log/app/error.log -f

# Custom number of lines
mcp ssh logs prod-server /var/log/app/error.log -n 200
```

### Docker Operations

#### List Containers

```bash
# Running containers
mcp docker ps

# All containers (including stopped)
mcp docker ps -a
```

#### Manage Container Lifecycle

```bash
# Start container
mcp docker start my-container

# Stop container
mcp docker stop my-container

# Restart container
mcp docker restart my-container
```

#### View Container Logs

```bash
# Last 100 lines
mcp docker logs my-container

# Follow logs
mcp docker logs my-container -f

# Custom tail
mcp docker logs my-container -n 500
```

### Kubernetes Operations

#### List Contexts

```bash
mcp k8s contexts
```

#### Switch to Cluster

```bash
mcp k8s use prod-k8s
```

#### List Resources

```bash
# List pods
mcp k8s pods -n default

# List pods in specific namespace
mcp k8s pods -n production

# List services
mcp k8s services -n default

# List deployments
mcp k8s deployments -n production
```

#### View Pod Logs

```bash
# Basic logs
mcp k8s logs my-pod -n default

# Specific container in multi-container pod
mcp k8s logs my-pod -c app-container -n default

# Follow logs
mcp k8s logs my-pod -f -n default

# Tail specific number of lines
mcp k8s logs my-pod --tail 500 -n default
```

#### Manage Deployments

```bash
# Scale deployment
mcp k8s scale my-deployment 5 -n production

# Restart deployment
mcp k8s restart my-deployment -n production
```

## ?? Configuration File Format

The configuration is stored in `~/.mcp/config.yaml`:

```yaml
version: "1.0"

ssh_servers:
  - name: prod-server
    host: server.example.com
    user: admin
    port: 22
    key_path: ~/.ssh/id_rsa

docker_hosts:
  - name: docker-prod
    host: docker.example.com
    connection_type: ssh
    ssh_config:
      user: admin
      key_path: ~/.ssh/id_rsa

kubernetes_clusters:
  - name: prod-k8s
    kubeconfig_path: ~/.kube/config
    context: prod-cluster

aliases:
  restart-app: "systemctl restart myapp"
  check-disk: "df -h"
  app-status: "systemctl status myapp"

settings:
  log_level: INFO
  timeout: 30
  retry_count: 3
```

## ?? Security Considerations

### Current Implementation (MVP)
- Credentials stored in local configuration file at `~/.mcp/config.yaml`
- Configuration directory has restricted permissions (0700)
- Configuration file has restricted permissions (0600)
- SSH key-based authentication is strongly recommended over passwords
- Supports SSH agent for key management

### Security Best Practices
1. **Never commit configuration files to version control**
   - `.mcp/` directory is included in `.gitignore`
   - Never share configuration files containing credentials

2. **Use SSH Keys Instead of Passwords**
   ```bash
   # Good - uses SSH key
   mcp config add-ssh server host user --key ~/.ssh/id_rsa
   
   # Avoid - stores password in plain text
   mcp config add-ssh server host user --password mypass
   ```

3. **Limit Credential Scope**
   - Use service accounts with minimal required permissions
   - For Kubernetes, use RBAC to limit access
   - For SSH, restrict user permissions on remote systems

4. **Regular Credential Rotation**
   - Rotate SSH keys periodically
   - Update Kubernetes tokens when they expire
   - Monitor access logs for suspicious activity

### Future Security Enhancements
- Integration with HashiCorp Vault
- Support for AWS Secrets Manager
- Support for Azure Key Vault
- Kubernetes Secrets integration
- Encrypted credential storage
- Audit logging of all operations
- Multi-factor authentication for central server mode

## ??? Architecture

### Current Design (Phase 1 - MVP)
```
???????????????????????????
?   MCP CLI (Local)       ?
?                         ?
?  ?????????????????????  ?
?  ? Config Manager    ?  ?
?  ?????????????????????  ?
?  ?????????????????????  ?
?  ? SSH Manager       ?  ?
?  ?????????????????????  ?
?  ?????????????????????  ?
?  ? Docker Manager    ?  ?
?  ?????????????????????  ?
?  ?????????????????????  ?
?  ? K8s Manager       ?  ?
?  ?????????????????????  ?
???????????????????????????
         ?
         ? SSH/API Calls
         ???????????????????????
         ?                     ?
    ???????????         ??????????????
    ?  Remote ?         ? Kubernetes ?
    ? Servers ?         ?  Cluster   ?
    ???????????         ??????????????
```

### Future Architecture (Phase 4 - Central Server)
```
????????????????????????       ????????????????????????
?  Developer Client    ?       ?  Developer Client    ?
?      (CLI/UI)        ?       ?      (CLI/UI)        ?
????????????????????????       ????????????????????????
           ?                               ?
           ?         REST/WebSocket        ?
           ?????????????????????????????????
                           ?
                  ???????????????????
                  ?  MCP Server     ?
                  ?  (Central)      ?
                  ?                 ?
                  ?  ?????????????  ?
                  ?  ? Auth &    ?  ?
                  ?  ? RBAC      ?  ?
                  ?  ?????????????  ?
                  ?  ?????????????  ?
                  ?  ? Task      ?  ?
                  ?  ? Manager   ?  ?
                  ?  ?????????????  ?
                  ?  ?????????????  ?
                  ?  ? Secrets   ?  ?
                  ?  ? Manager   ?  ?
                  ?  ?????????????  ?
                  ???????????????????
                           ?
         ?????????????????????????????????????
         ?                 ?                 ?
    ???????????     ???????????????   ??????????????
    ?  SSH    ?     ?   Docker    ?   ? Kubernetes ?
    ? Servers ?     ?   Hosts     ?   ?  Clusters  ?
    ???????????     ???????????????   ??????????????
```

## ??? Roadmap

### Phase 1: Prototype/MVP ? (Current)
- [x] Core architecture and project structure
- [x] SSH access and remote command execution
- [x] Docker container management
- [x] Log access and retrieval
- [x] Kubernetes service integration
- [x] Command aliases
- [x] CLI interface with rich output

### Phase 2: Stabilization and Hardening
- [ ] Enhanced error handling and retries
- [ ] Support for additional authentication methods
- [ ] Encrypted local credential storage
- [ ] OS keychain integration
- [ ] Performance optimization
- [ ] Cross-platform testing (Linux, macOS, Windows)
- [ ] Comprehensive test suite

### Phase 3: Extended Features
- [ ] Plugin system for extensibility
- [ ] Task queuing and scheduling
- [ ] Basic web API
- [ ] Secret vault integration (Vault, AWS, Azure)
- [ ] Multi-server parallel operations
- [ ] Enhanced logging and audit trails
- [ ] Configuration templates and imports

### Phase 4: Central Server Mode
- [ ] Multi-user support
- [ ] Role-based access control (RBAC)
- [ ] Web UI dashboard
- [ ] Real-time notifications
- [ ] Alerting and monitoring integration
- [ ] SSO authentication
- [ ] Advanced audit logging
- [ ] Team collaboration features

## ?? Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=mcp --cov-report=html
```

### Code Style

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

### Project Structure

```
mcp-server/
??? src/
?   ??? mcp/
?       ??? __init__.py
?       ??? cli.py              # CLI interface
?       ??? config.py           # Configuration management
?       ??? ssh_manager.py      # SSH operations
?       ??? docker_manager.py   # Docker operations
?       ??? k8s_manager.py      # Kubernetes operations
??? tests/
?   ??? test_config.py
?   ??? test_ssh.py
?   ??? test_docker.py
?   ??? test_k8s.py
??? docs/
?   ??? security.md
?   ??? configuration.md
?   ??? examples.md
??? setup.py
??? requirements.txt
??? README.md
??? .gitignore
```

## ?? Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ?? License

This project is licensed under the MIT License - see the LICENSE file for details.

## ?? Support

For issues, questions, or feature requests, please:
- Open an issue on GitHub
- Contact the DevOps team
- Check the documentation in the `docs/` directory

## ?? Acknowledgments

- Built with Python, Paramiko, Docker SDK, and Kubernetes Client
- Inspired by best practices in DevOps tooling and internal developer platforms
- Thanks to the open-source community for excellent libraries

---

**Note**: This is an internal DevOps tool. Handle credentials with care and follow your organization's security policies.
