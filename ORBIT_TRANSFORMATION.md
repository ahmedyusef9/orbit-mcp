# ?? Transformation to orbit-mcp

## Overview

The MCP Server is being transformed into **orbit-mcp** - a comprehensive, production-grade DevOps automation platform with AI integration.

## Key Changes

### Naming
- **Project**: mcp-server ? **orbit-mcp**
- **CLI Command**: mcp ? **orbit**
- **MCP Server Command**: mcp-server ? **orbit** (same binary, different modes)

### Architecture Enhancements

#### 1. Profile Management System
- Multiple environment profiles (prod, staging, dev, etc.)
- Per-profile configuration (SSH, Kubernetes, Docker, allowlists)
- Easy switching with `profile.set`
- Context awareness with `context.show`

#### 2. Safety & Allowlist Engine
- Allowlist system for passthrough commands
- Per-profile safety rules
- Redaction of sensitive data (tokens, passwords)
- Audit logging of all operations

#### 3. Multi-Namespace Kubernetes
- Operations across multiple namespaces
- kubectl passthrough for complete coverage
- Ergonomic wrappers for common operations
- Multi-pod log streaming (stern-like)

#### 4. Docker Compose Support
- Full Docker Compose v2 integration
- compose.cli passthrough
- Multi-file compose support
- Profile-based configurations

#### 5. Version Awareness
- Detect kubectl, docker, compose, helm versions
- Gate features based on availability
- Version compatibility checks
- Upgrade recommendations

#### 6. Comprehensive Tool Surface

**Total Tools: 40+**

**Session Management (3 tools):**
- profile.set
- context.show
- allowlist.show / allowlist.test

**SSH & Linux (6 tools):**
- ssh.run
- sys.top
- sys.df
- sys.free
- sys.journal
- ssh.script

**Docker Engine (15 tools):**
- docker.version
- docker.ps
- docker.inspect
- docker.logs
- docker.start/stop/restart/kill
- docker.rm/exec/cp
- docker.pull/push/build
- docker.images/rmi
- docker.network.*
- docker.volume.*
- docker.cli (passthrough)

**Docker Compose (8 tools):**
- compose.version
- compose.up/down
- compose.ps/logs
- compose.pull/build
- compose.config/restart
- compose.cli (passthrough)

**Kubernetes (12 tools):**
- k8s.contexts / k8s.useContext
- k8s.namespaces / k8s.useNamespace
- k8s.get
- k8s.describe
- k8s.logs
- k8s.exec
- k8s.apply/delete
- k8s.kubectl (passthrough)

**Helm (5 tools):**
- helm.version
- helm.releases
- helm.get
- helm.upgrade/uninstall

**Logs (2 tools):**
- logs.tail
- logs.search

**Tickets (4 tools):**
- ticket.create/update/list/get

#### 7. Audit & Security
- Comprehensive audit log (~/.orbit/audit.log)
- Redaction engine for secrets
- Per-operation logging
- User approval workflow (via Cursor)

### Configuration Structure

New configuration at `~/.orbit/config.yaml`:

```yaml
version: "1.0"

# Default profile
default_profile: staging

# Profiles
profiles:
  production:
    ssh_bastion: prod-bastion
    kube_context: prod-cluster
    kube_namespace: production
    docker_host: unix:///var/run/docker.sock
    allowlist:
      kubectl:
        - get
        - describe
        - logs
        - exec
      docker:
        - ps
        - logs
        - inspect
      dangerous_allowed: false
    
  staging:
    ssh_bastion: staging-bastion
    kube_context: staging-cluster
    kube_namespace: staging
    docker_host: unix:///var/run/docker.sock
    allowlist:
      kubectl:
        - get
        - describe
        - logs
        - exec
        - apply
        - delete
      docker:
        - ps
        - logs
        - start
        - stop
        - restart
      compose:
        - up
        - down
        - ps
        - logs
      dangerous_allowed: true

# SSH Hosts (inherited by all profiles, can override)
ssh_hosts:
  - name: prod-bastion
    host: bastion.prod.example.com
    user: ops
    key_path: ~/.ssh/prod_key
  
  - name: staging-bastion
    host: bastion.staging.example.com
    user: ops
    key_path: ~/.ssh/staging_key

# Kubernetes Clusters
kubernetes_clusters:
  - name: prod-cluster
    kubeconfig_path: ~/.kube/config
    context: prod-cluster
  
  - name: staging-cluster
    kubeconfig_path: ~/.kube/config
    context: staging-cluster

# Docker Hosts
docker_hosts:
  - name: local
    type: local
  
  - name: remote-prod
    type: ssh
    ssh_host: prod-docker.example.com
    ssh_user: docker
    ssh_key: ~/.ssh/docker_key

# Redaction Patterns
redaction:
  patterns:
    - "token"
    - "password"
    - "secret"
    - "apikey"
    - "bearer"

# Audit Settings
audit:
  enabled: true
  log_path: ~/.orbit/audit.log
  log_level: info
```

### Cursor Integration

New `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "orbit-mcp": {
      "command": "orbit",
      "args": [],
      "disabled": false,
      "env": {
        "ORBIT_CONFIG": "~/.orbit/config.yaml",
        "ORBIT_PROFILE": "staging"
      }
    }
  }
}
```

## Implementation Plan

### Phase 1: Core Transformation (Current)
1. ? Rename project to orbit-mcp
2. ? Create new architecture with profiles
3. ? Implement allowlist/safety engine
4. ? Add comprehensive tool definitions
5. ? Implement audit logging
6. ? Add version detection
7. ? Update all documentation

### Phase 2: Enhanced Features
- Multi-namespace operations
- Real-time streaming improvements
- Helm integration
- Advanced allowlist rules
- Performance optimizations

### Phase 3: Advanced Integrations
- GitOps tools (Argo CD, Flux)
- Observability (Prometheus, OpenTelemetry)
- Service Mesh (Linkerd)
- Security scanning (Trivy, Cosign)
- IaC (Terraform)

## Migration from MCP Server

For existing users:

```bash
# Backup old config
cp ~/.mcp/config.yaml ~/.mcp/config.yaml.backup

# Install orbit-mcp
cd /workspace
pip install -e .

# Initialize orbit config (migrates from old config)
orbit init --migrate-from ~/.mcp/config.yaml

# Test with new CLI
orbit --help
orbit context show
orbit profile set staging
```

## Benefits

1. **More Comprehensive**: 40+ tools vs 14 previously
2. **Safer**: Allowlist engine + audit logging
3. **More Flexible**: Passthrough commands for full coverage
4. **Better Organized**: Profile-based configuration
5. **Production Ready**: Version awareness + redaction
6. **Future Proof**: Easy to add new integrations

## Next Steps

1. Review the new architecture
2. Test with your infrastructure
3. Configure profiles for your environments
4. Set up allowlists for your team
5. Integrate with Cursor
6. Provide feedback for Phase 2

---

**orbit-mcp: AI-Powered DevOps Automation at Scale** ??
