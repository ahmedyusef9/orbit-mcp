# ?? orbit-mcp Implementation Guide

## Executive Summary

**orbit-mcp** is the next generation of the MCP Server, designed for production DevOps automation with AI integration. This guide outlines the complete implementation.

---

## ?? Scope

### What's Being Built

**40+ Tools** across 8 categories:
- Session Management (3)
- SSH & Linux (6)  
- Docker Engine (15)
- Docker Compose (8)
- Kubernetes (12)
- Helm (5)
- Logs (2)
- Tickets (4)

**Core Systems:**
- Profile Management
- Allowlist/Safety Engine
- Version Detection
- Audit Logging
- Redaction Engine
- Multi-namespace K8s
- Passthrough Commands

---

## ??? Architecture

### File Structure

```
orbit-mcp/
??? src/orbit/
?   ??? __init__.py
?   ??? core/
?   ?   ??? profile.py          # Profile management
?   ?   ??? allowlist.py        # Safety engine
?   ?   ??? audit.py            # Audit logging
?   ?   ??? redaction.py        # Secret redaction
?   ?   ??? versions.py         # Version detection
?   ??? protocol/
?   ?   ??? mcp.py              # MCP protocol
?   ?   ??? transports.py       # STDIO/HTTP+SSE
?   ??? tools/
?   ?   ??? session.py          # profile.set, context.show
?   ?   ??? ssh.py              # SSH tools
?   ?   ??? docker.py           # Docker tools
?   ?   ??? compose.py          # Docker Compose
?   ?   ??? kubernetes.py       # K8s tools
?   ?   ??? helm.py             # Helm tools
?   ?   ??? logs.py             # Log tools
?   ?   ??? tickets.py          # Ticket system
?   ??? managers/
?   ?   ??? ssh_manager.py      # Existing
?   ?   ??? docker_manager.py   # Enhanced
?   ?   ??? k8s_manager.py      # Enhanced
?   ??? cli.py                  # Traditional CLI
?   ??? server.py               # MCP server
?   ??? main.py                 # Entry point
??? config/
?   ??? config.yaml.template    # Configuration template
?   ??? profiles/               # Profile examples
?       ??? production.yaml
?       ??? staging.yaml
?       ??? development.yaml
??? docs/
?   ??? ORBIT_README.md         # Main documentation
?   ??? TOOLS.md                # Complete tool reference
?   ??? PROFILES.md             # Profile guide
?   ??? ALLOWLIST.md            # Safety configuration
?   ??? CURSOR.md               # Cursor integration
??? tests/
    ??? test_profiles.py
    ??? test_allowlist.py
    ??? test_tools.py
```

---

## ?? Core Components

### 1. Profile Management (`src/orbit/core/profile.py`)

```python
class ProfileManager:
    """Manages profiles for different environments."""
    
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.current_profile = self.config.get('default_profile', 'staging')
    
    def set_profile(self, name: str):
        """Switch to a different profile."""
        if name not in self.config['profiles']:
            raise ProfileNotFoundError(name)
        self.current_profile = name
        return self.get_profile(name)
    
    def get_profile(self, name: str = None) -> Dict:
        """Get profile configuration."""
        name = name or self.current_profile
        profile = self.config['profiles'][name]
        
        return {
            'name': name,
            'ssh_bastion': profile.get('ssh_bastion'),
            'kube_context': profile.get('kube_context'),
            'kube_namespace': profile.get('kube_namespace'),
            'docker_host': profile.get('docker_host'),
            'allowlist': profile.get('allowlist', {})
        }
    
    def get_context(self) -> Dict:
        """Get current context with versions."""
        profile = self.get_profile()
        
        return {
            'profile': self.current_profile,
            'kube_context': profile['kube_context'],
            'namespace': profile['kube_namespace'],
            'docker_host': profile['docker_host'],
            'ssh_bastion': profile['ssh_bastion'],
            'versions': self.get_versions()
        }
    
    def get_versions(self) -> Dict:
        """Detect tool versions."""
        return {
            'kubectl': self._get_kubectl_version(),
            'docker': self._get_docker_version(),
            'compose': self._get_compose_version(),
            'helm': self._get_helm_version()
        }
```

### 2. Allowlist Engine (`src/orbit/core/allowlist.py`)

```python
class AllowlistEngine:
    """Safety engine for passthrough commands."""
    
    def __init__(self, profile: Dict):
        self.allowlist = profile.get('allowlist', {})
        self.dangerous_allowed = profile.get('dangerous_allowed', False)
    
    def check_kubectl(self, args: List[str]) -> bool:
        """Check if kubectl command is allowed."""
        if not args:
            return False
        
        verb = args[0]
        
        # Check allowlist
        if verb not in self.allowlist.get('kubectl', []):
            return False
        
        # Check for dangerous flags
        if not self.dangerous_allowed:
            dangerous_flags = ['--force', '--grace-period=0', '--delete-all']
            if any(flag in ' '.join(args) for flag in dangerous_flags):
                return False
        
        return True
    
    def check_docker(self, subcommand: str, args: List[str]) -> bool:
        """Check if docker command is allowed."""
        if subcommand not in self.allowlist.get('docker', []):
            return False
        
        # Block system prune without confirmation
        if subcommand == 'system' and 'prune' in args:
            if not self.dangerous_allowed:
                return False
        
        return True
    
    def check_compose(self, args: List[str]) -> bool:
        """Check if compose command is allowed."""
        if not args:
            return False
        
        command = args[0]
        
        if command not in self.allowlist.get('compose', []):
            return False
        
        # Check for destructive flags
        if command == 'down' and '-v' in args:
            if not self.dangerous_allowed:
                return False
        
        return True
```

### 3. Audit Logger (`src/orbit/core/audit.py`)

```python
class AuditLogger:
    """Comprehensive audit logging."""
    
    def __init__(self, config: Dict):
        self.enabled = config.get('audit', {}).get('enabled', True)
        self.log_path = Path(config.get('audit', {}).get('log_path', 
                                                         '~/.orbit/audit.log')).expanduser()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_operation(self, operation: Dict):
        """Log an operation."""
        if not self.enabled:
            return
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'tool': operation['tool'],
            'profile': operation.get('profile'),
            'args_hash': hashlib.sha256(
                json.dumps(operation.get('args', {})).encode()
            ).hexdigest()[:16],
            'context': operation.get('context'),
            'bytes_out': operation.get('bytes_out', 0),
            'exit_code': operation.get('exit_code', 0),
            'duration_ms': operation.get('duration_ms', 0)
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
```

### 4. Redaction Engine (`src/orbit/core/redaction.py`)

```python
class RedactionEngine:
    """Redacts sensitive data from outputs."""
    
    def __init__(self, patterns: List[str]):
        self.patterns = [
            re.compile(rf'{pattern}[:\s=]+[^\s]+', re.IGNORECASE)
            for pattern in patterns
        ]
    
    def redact(self, text: str) -> str:
        """Redact sensitive data from text."""
        for pattern in self.patterns:
            text = pattern.sub(lambda m: m.group(0).split()[0] + ' [REDACTED]', text)
        
        return text
    
    def redact_dict(self, data: Dict) -> Dict:
        """Redact sensitive data from dictionary."""
        redacted = {}
        for key, value in data.items():
            if any(pattern in key.lower() for pattern in ['token', 'password', 'secret', 'key']):
                redacted[key] = '[REDACTED]'
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value)
            elif isinstance(value, str):
                redacted[key] = self.redact(value)
            else:
                redacted[key] = value
        return redacted
```

---

## ??? Tool Definitions

### Complete Tool List (40+ tools)

#### Session Management
```python
# profile.set
{
    "name": "profile.set",
    "description": "Switch active profile (changes default context, namespace, allowlist)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "enum": ["production", "staging", "development"],
                "description": "Profile name"
            }
        },
        "required": ["name"]
    }
}

# context.show
{
    "name": "context.show",
    "description": "Show current context with versions",
    "inputSchema": {"type": "object", "properties": {}},
    "outputSchema": {
        "type": "object",
        "properties": {
            "profile": {"type": "string"},
            "kubeContext": {"type": "string"},
            "namespace": {"type": "string"},
            "dockerHost": {"type": "string"},
            "sshBastion": {"type": "string"},
            "versions": {
                "type": "object",
                "properties": {
                    "kubectl": {"type": "string"},
                    "docker": {"type": "string"},
                    "compose": {"type": "string"},
                    "helm": {"type": "string"}
                }
            }
        }
    }
}

# allowlist.show
{
    "name": "allowlist.show",
    "description": "Show current allowlist configuration",
    "inputSchema": {"type": "object", "properties": {}}
}
```

#### SSH & Linux
```python
# ssh.run
{
    "name": "ssh.run",
    "description": "Execute command on remote host via SSH",
    "inputSchema": {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "Host name or user@host"
            },
            "cmd": {
                "type": "string",
                "description": "Command to execute"
            },
            "timeoutSec": {
                "type": "integer",
                "default": 120,
                "description": "Timeout in seconds"
            }
        },
        "required": ["host", "cmd"]
    }
}

# sys.journal
{
    "name": "sys.journal",
    "description": "Query systemd journal (journalctl)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "unit": {
                "type": "string",
                "description": "Service unit name (e.g., nginx.service)"
            },
            "priority": {
                "type": "string",
                "enum": ["err", "warning", "info", "debug"],
                "description": "Log priority level"
            },
            "since": {
                "type": "string",
                "description": "Time specification (e.g., '1h', '2d')"
            },
            "follow": {
                "type": "boolean",
                "default": false,
                "description": "Stream new entries"
            }
        }
    }
}
```

#### Docker Engine
```python
# docker.version
{
    "name": "docker.version",
    "description": "Get Docker version information",
    "inputSchema": {"type": "object", "properties": {}},
    "outputSchema": {
        "type": "object",
        "properties": {
            "client": {"type": "string"},
            "server": {"type": "string"}
        }
    }
}

# docker.cli (passthrough)
{
    "name": "docker.cli",
    "description": "Execute docker command (allowlist enforced)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "subcommand": {
                "type": "string",
                "enum": ["container", "image", "volume", "network", "system"],
                "description": "Docker subcommand"
            },
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Command arguments"
            }
        },
        "required": ["subcommand", "args"]
    }
}
```

#### Docker Compose
```python
# compose.up
{
    "name": "compose.up",
    "description": "Create and start compose services",
    "inputSchema": {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Compose files"
            },
            "project": {
                "type": "string",
                "description": "Project name"
            },
            "services": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific services to start"
            },
            "detach": {
                "type": "boolean",
                "default": true,
                "description": "Detached mode"
            },
            "profiles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Compose profiles to activate"
            }
        }
    }
}

# compose.cli (passthrough)
{
    "name": "compose.cli",
    "description": "Execute docker compose command (allowlist enforced)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Compose command arguments"
            }
        },
        "required": ["args"]
    }
}
```

#### Kubernetes
```python
# k8s.get
{
    "name": "k8s.get",
    "description": "Get Kubernetes resources",
    "inputSchema": {
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["pods", "deployments", "services", "nodes", "ingresses", 
                         "configmaps", "secrets", "pv", "pvc"],
                "description": "Resource kind"
            },
            "namespace": {
                "type": "string",
                "description": "Namespace (omit for cluster-scoped)"
            },
            "namespaces": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Multiple namespaces"
            },
            "selector": {
                "type": "string",
                "description": "Label selector (e.g., app=web)"
            },
            "output": {
                "type": "string",
                "enum": ["table", "yaml", "json"],
                "default": "table",
                "description": "Output format"
            }
        },
        "required": ["kind"]
    }
}

# k8s.kubectl (passthrough)
{
    "name": "k8s.kubectl",
    "description": "Execute kubectl command (allowlist enforced)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "kubectl arguments (e.g., ['get', 'pods', '-n', 'prod'])"
            }
        },
        "required": ["args"]
    }
}

# k8s.logs (multi-pod support)
{
    "name": "k8s.logs",
    "description": "Get pod logs (supports multiple pods like stern)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "pod": {
                "type": "string",
                "description": "Pod name"
            },
            "pods": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Multiple pod names"
            },
            "namespace": {
                "type": "string",
                "description": "Namespace"
            },
            "container": {
                "type": "string",
                "description": "Container name"
            },
            "since": {
                "type": "string",
                "description": "Time duration (e.g., '5m', '1h')"
            },
            "tail": {
                "type": "integer",
                "default": 100,
                "description": "Number of lines"
            },
            "follow": {
                "type": "boolean",
                "default": false,
                "description": "Stream logs"
            }
        }
    }
}
```

#### Helm
```python
# helm.version
{
    "name": "helm.version",
    "description": "Get Helm version",
    "inputSchema": {"type": "object", "properties": {}}
}

# helm.releases
{
    "name": "helm.releases",
    "description": "List Helm releases",
    "inputSchema": {
        "type": "object",
        "properties": {
            "namespace": {
                "type": "string",
                "description": "Namespace filter"
            },
            "all_namespaces": {
                "type": "boolean",
                "default": false,
                "description": "List releases across all namespaces"
            }
        }
    }
}

# helm.upgrade
{
    "name": "helm.upgrade",
    "description": "Upgrade a Helm release",
    "inputSchema": {
        "type": "object",
        "properties": {
            "release": {
                "type": "string",
                "description": "Release name"
            },
            "chart": {
                "type": "string",
                "description": "Chart name or path"
            },
            "namespace": {
                "type": "string",
                "description": "Namespace"
            },
            "values": {
                "type": "object",
                "description": "Values to set"
            },
            "install": {
                "type": "boolean",
                "default": false,
                "description": "Install if not exists"
            }
        },
        "required": ["release", "chart"]
    }
}
```

---

## ?? Configuration Template

### `~/.orbit/config.yaml`

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
    compose_files:
      - docker-compose.yml
      - docker-compose.prod.yml
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
      compose:
        - ps
        - logs
      dangerous_allowed: false
    
  staging:
    ssh_bastion: staging-bastion
    kube_context: staging-cluster
    kube_namespace: staging
    docker_host: unix:///var/run/docker.sock
    compose_files:
      - docker-compose.yml
      - docker-compose.staging.yml
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
        - inspect
        - exec
      compose:
        - up
        - down
        - ps
        - logs
        - pull
        - build
      dangerous_allowed: true
  
  development:
    ssh_bastion: dev-bastion
    kube_context: minikube
    kube_namespace: default
    docker_host: unix:///var/run/docker.sock
    compose_files:
      - docker-compose.yml
      - docker-compose.dev.yml
    allowlist:
      kubectl:
        - "*"  # All commands allowed in dev
      docker:
        - "*"
      compose:
        - "*"
      dangerous_allowed: true

# SSH Hosts
ssh_hosts:
  - name: prod-bastion
    host: bastion.prod.example.com
    user: ops
    key_path: ~/.ssh/prod_key
  
  - name: staging-bastion
    host: bastion.staging.example.com
    user: ops
    key_path: ~/.ssh/staging_key
  
  - name: dev-bastion
    host: localhost
    user: developer
    key_path: ~/.ssh/id_rsa

# Kubernetes Clusters
kubernetes_clusters:
  - name: prod-cluster
    kubeconfig_path: ~/.kube/config
    context: prod-cluster
  
  - name: staging-cluster
    kubeconfig_path: ~/.kube/config
    context: staging-cluster
  
  - name: minikube
    kubeconfig_path: ~/.kube/config
    context: minikube

# Docker Hosts
docker_hosts:
  - name: local
    type: local
    socket: unix:///var/run/docker.sock
  
  - name: remote-prod
    type: ssh
    ssh_host: docker.prod.example.com
    ssh_user: docker
    ssh_key: ~/.ssh/docker_key

# Redaction Patterns (case-insensitive)
redaction:
  patterns:
    - token
    - password
    - secret
    - apikey
    - bearer
    - authorization
    - x-api-key
    - aws_access_key
    - aws_secret_key

# Audit Settings
audit:
  enabled: true
  log_path: ~/.orbit/audit.log
  log_level: info
  redact_args: true

# Version Requirements (optional)
version_requirements:
  kubectl: ">=1.24"
  docker: ">=20.10"
  compose: ">=2.0"
  helm: ">=3.0"
```

---

## ?? Implementation Steps

### Step 1: Create New Directory Structure

```bash
mkdir -p ~/.orbit
mkdir -p src/orbit/{core,protocol,tools,managers}
```

### Step 2: Implement Core Systems

Priority order:
1. Profile Manager
2. Allowlist Engine  
3. Audit Logger
4. Redaction Engine
5. Version Detection

### Step 3: Implement Tools

By category:
1. Session Management (profile.set, context.show)
2. SSH tools
3. Docker tools + passthrough
4. Compose tools + passthrough
5. Kubernetes tools + passthrough
6. Helm tools
7. Log tools
8. Ticket tools

### Step 4: Update MCP Server

Integrate new tools with MCP protocol:
- Update tools/list to return 40+ tools
- Implement tool handlers with allowlist checks
- Add audit logging to all operations
- Apply redaction to all outputs

### Step 5: Testing

Test each category:
- Profile switching
- Allowlist enforcement
- Version detection
- Audit logging
- Redaction
- Multi-namespace operations
- Passthrough commands

### Step 6: Documentation

Update all docs for orbit-mcp:
- README
- Tool reference
- Profile guide
- Cursor integration
- Security guide

---

## ?? Success Criteria

- [ ] All 40+ tools defined with schemas
- [ ] Profile management working
- [ ] Allowlist engine enforcing rules
- [ ] Audit log capturing all operations
- [ ] Redaction working on sensitive data
- [ ] Version detection for all tools
- [ ] Multi-namespace K8s operations
- [ ] Passthrough commands safe and functional
- [ ] Cursor integration seamless
- [ ] All documentation updated

---

## ?? References

- kubectl: https://kubernetes.io/docs/reference/kubectl/
- Docker CLI: https://docs.docker.com/engine/reference/commandline/cli/
- Docker Compose: https://docs.docker.com/compose/reference/
- Helm: https://helm.sh/docs/helm/
- MCP Spec: https://modelcontextprotocol.io/
- CNCF Landscape: https://landscape.cncf.io/

---

**This guide provides the complete blueprint for orbit-mcp. Implementation can proceed in phases, starting with core systems and gradually adding tools.**
