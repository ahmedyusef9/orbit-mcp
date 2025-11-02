# Changelog

All notable changes to MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-02

### Added

#### Core Features
- **Configuration Management**: YAML-based configuration system with secure credential storage
- **SSH Manager**: Remote command execution, log tailing, and file transfer
- **Docker Manager**: Container lifecycle management, log viewing, and resource monitoring
- **Kubernetes Manager**: Pod, service, and deployment management across multiple clusters
- **Command Aliases**: User-defined shortcuts for frequently used commands
- **CLI Interface**: Rich terminal output with tables, colors, and intuitive commands

#### SSH Operations
- Connect to remote servers with SSH key or password authentication
- Execute single or multiple commands sequentially
- Tail logs with follow option (-f)
- Upload and download files via SFTP
- Connection pooling and reuse
- Support for SSH agent

#### Docker Operations
- List containers (running and all)
- Start, stop, restart, and remove containers
- View container logs with tail and follow options
- Execute commands in running containers
- Get container resource statistics (CPU, memory, network)
- List and pull Docker images
- Support for both local and remote Docker daemons

#### Kubernetes Operations
- Manage multiple clusters and contexts
- List and switch between Kubernetes contexts
- View pods, services, and deployments
- Get pod logs with follow option
- Scale deployments
- Restart deployments
- Execute commands in pods
- Get node information
- Support for custom kubeconfig paths

#### Configuration
- Initialize default configuration
- Add SSH servers, Docker hosts, and Kubernetes clusters via CLI
- Create and manage command aliases
- Support for multiple configuration files
- Automatic permission setting (0700 for directory, 0600 for file)
- List all configured profiles

#### Security
- Secure credential storage in local configuration file
- SSH key-based authentication support
- Restricted file permissions on configuration
- No credential logging in output
- SSH agent support

#### Documentation
- Comprehensive README with installation and usage instructions
- Security guide with best practices
- Configuration guide with examples
- Usage examples for common scenarios
- Quick start guide
- Example configuration files

#### Development
- Project structure with modular design
- Python package setup with dependencies
- Test suite with pytest
- Development requirements file
- Git ignore configuration
- MIT License

### Technical Details

#### Dependencies
- paramiko >= 3.0.0 (SSH functionality)
- docker >= 6.0.0 (Docker integration)
- kubernetes >= 25.0.0 (Kubernetes integration)
- click >= 8.0.0 (CLI framework)
- pyyaml >= 6.0 (Configuration parsing)
- cryptography >= 41.0.0 (Security)
- rich >= 13.0.0 (Terminal output)

#### Architecture
- Local-first design (runs on user's machine)
- Modular manager classes for each service type
- Extensible configuration system
- Clean separation of concerns

#### Testing
- Unit tests for configuration management
- Test fixtures for temporary configurations
- Mock support for SSH/Docker/K8s operations

### Known Limitations
- No centralized server mode (planned for Phase 4)
- No encrypted credential storage (planned for Phase 2)
- No secret vault integration (planned for Phase 3)
- No web UI (planned for Phase 4)
- No real-time monitoring or alerting (out of scope for MVP)
- Limited to Python 3.8+ environments

## [0.2.0] - 2025-11-02

### Added - MCP Protocol Support ??

#### Model Context Protocol Implementation
- **MCP Protocol Layer** (`protocol.py`): Complete JSON-RPC 2.0 based MCP implementation
  - Protocol handler with capability negotiation
  - Request/response processing
  - Error handling with standard codes
  - Batch request support
  - Tool result formatting (text + structured content)
  
- **MCP Server** (`mcp_server.py`): DevOps tools exposed via MCP
  - 14 fully-functional DevOps tools with JSON Schema
  - Tool discovery (tools/list)
  - Tool invocation (tools/call)
  - Structured input/output schemas
  - Integration with existing SSH/Docker/K8s managers

- **Transport Layers** (`transports.py`):
  - STDIO transport for local integration (Cursor)
  - HTTP+SSE transport for remote access
  - Async I/O support
  - Keep-alive and streaming infrastructure

- **Entry Point** (`mcp_main.py`): Command-line interface for MCP server
  - `mcp-server` command with transport selection
  - Verbose logging option
  - Custom configuration support

#### MCP Tools (14 Total)

**SSH Operations:**
- `ssh_execute` - Execute commands on remote servers
- `query_logs` - Query and filter log files  
- `system_info` - Get system information
- `disk_usage` - Check disk usage

**Docker Management:**
- `docker_list_containers` - List containers with status
- `docker_start_container` - Start containers
- `docker_stop_container` - Stop containers
- `docker_restart_container` - Restart containers
- `docker_logs` - Fetch container logs

**Kubernetes Operations:**
- `k8s_list_pods` - List pods in namespace
- `k8s_get_pod` - Get pod details
- `k8s_logs` - Fetch pod logs
- `k8s_scale_deployment` - Scale deployments
- `k8s_restart_deployment` - Restart deployments

#### Integration Features
- **Cursor Compatibility**: Out-of-the-box integration with Cursor IDE
- **Natural Language**: AI can use natural language to invoke tools
- **User Approval**: Security feature - all operations require confirmation
- **Structured Results**: Both human-readable and machine-parsable outputs

#### Documentation
- **MCP Integration Guide** (`docs/MCP_INTEGRATION.md`): Complete 800-line guide
  - MCP protocol overview
  - API reference with examples
  - Cursor setup instructions
  - Security best practices
  - Troubleshooting guide
  
- **MCP README** (`MCP_README.md`): User-friendly overview
- **Example Configurations**: Cursor integration examples
- **Implementation Summary**: Detailed technical documentation

### Changed
- **setup.py**: Added `mcp-server` entry point
- **requirements.txt**: Added `aiohttp>=3.9.0` for HTTP transport

### Technical Details

#### Architecture
- Layered design: Protocol ? Server ? Managers ? Infrastructure
- Reuses existing managers for consistency
- Transport abstraction for flexibility
- Schema-driven tool definitions

#### Code Statistics
- **New Python Code**: ~1,300 lines
- **New Documentation**: ~1,200 lines
- **Total Project**: ~3,000 lines code, ~4,200 lines docs

#### Security
- User approval required for all operations
- Secure credential storage (existing config system)
- Input validation via JSON Schema
- Audit logging to stderr
- No sensitive data in logs

## [Unreleased]

### Planned for Phase 2 (Stabilization)
- Enhanced error handling with retries
- Encrypted local credential storage
- OS keychain integration
- Performance optimizations
- Cross-platform testing
- Comprehensive test coverage

### Planned for Phase 3 (Extended Features)
- Plugin system for extensibility
- Task queuing and scheduling
- Basic web API
- Secret vault integration (Vault, AWS, Azure)
- Multi-server parallel operations
- Enhanced audit logging
- Configuration templates

### Planned for Phase 4 (Central Server)
- Multi-user support
- Role-based access control
- Web UI dashboard
- Real-time notifications
- Alerting integration
- SSO authentication
- Team collaboration features

---

[0.1.0]: https://github.com/yourorg/mcp-server/releases/tag/v0.1.0
