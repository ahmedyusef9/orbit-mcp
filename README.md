# Orbit-MCP - AI-Powered DevOps Platform

![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**Orbit-MCP** is a hybrid DevOps platform that combines traditional command-line tools, MCP server capabilities for IDE integration, and an intelligent AI agent powered by LLMs. It empowers developers and DevOps teams to manage infrastructure through **natural language**, direct commands, or AI-assisted workflows.

## ?? What's New: AI Agent Integration

Orbit-MCP now includes a **built-in AI agent** that can:

- ?? **Understand natural language** - "Check why OpenSearch failed on server ilgss1111"
- ?? **Plan and execute autonomously** - Break complex tasks into steps
- ?? **Optimize costs** - Intelligently choose between OpenAI, Claude, or local Ollama models
- ?? **Use DevOps tools** - SSH, Docker, Kubernetes, logs, and more
- ?? **Reason and diagnose** - Analyze logs and explain root causes
- ?? **Safe by default** - Confirm destructive operations

## ?? Three Modes of Operation

### 1. **AI Agent Mode** (NEW!)

Ask questions in natural language:

```bash
# One-shot queries
$ mcp ai ask "Check status of server prod-web-01"

? Server prod-web-01 is healthy
- Uptime: 23 days
- Load: 0.8, 1.2, 1.5
- Memory: 62% used
- Disk: 45% used

# Interactive chat
$ mcp ai chat

You: Why did nginx fail?
Orbit AI: [analyzes logs] Nginx failed due to SSL certificate expiration...

You: Show me the OpenSearch cluster status
Orbit AI: [checks cluster] Status: RED. Root cause: Disk full on node 1...
```

**Use when:**
- Investigating incidents
- Diagnosing complex issues
- Need intelligent analysis
- Want conversational interaction

### 2. **MCP Server Mode**

Integrate with Cursor or other AI IDEs:

```json
// Cursor config
{
  "mcpServers": {
    "orbit-mcp": {
      "command": "mcp-server",
      "transport": "stdio"
    }
  }
}
```

In Cursor:
```
You: "Check production server status"
Cursor AI ? orbit-mcp ? infrastructure ? results ? Cursor AI ? You
```

**Use when:**
- Working in your IDE (Cursor, VS Code)
- Want AI assistance during coding
- Need infrastructure context while developing

### 3. **Traditional CLI Mode**

Direct commands (no AI):

```bash
mcp ssh exec prod-web-01 "systemctl status nginx"
mcp docker ps
mcp k8s pods -n production
```

**Use when:**
- Scripting and automation
- Known exact commands
- Speed is critical
- No AI needed

## ?? What It Manages

- **SSH Access** - Execute remote commands, tail logs, transfer files
- **Docker** - Containers, images, logs, stats
- **Kubernetes** - Pods, services, deployments, scaling
- **Docker Compose** - Multi-container applications
- **Helm** - Kubernetes package management
- **System Logs** - Journalctl, syslog, application logs
- **Command Aliases** - Custom shortcuts

## ?? Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd orbit-mcp

# Install dependencies
pip install -r requirements.txt

# Install Orbit
pip install -e .
```

### AI Agent Setup

```bash
# Option 1: Use Ollama (local, free)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2

# Option 2: Use OpenAI
export OPENAI_API_KEY=sk-...

# Option 3: Use Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-...
```

### Configuration

```bash
# Copy example config
cp config.example.yaml ~/.mcp/config.yaml

# Edit config
vim ~/.mcp/config.yaml
```

### First AI Query

```bash
mcp ai ask "Hello, introduce yourself"
```

## ?? AI Agent Examples

### Server Health Check

```bash
$ mcp ai ask "Is server prod-web-01 healthy?"

Checking prod-web-01...

? Server is healthy
- Uptime: 23 days, 14:32
- Load average: 0.8, 1.2, 1.5 (normal)
- Memory: 8.2 GB / 16 GB (62% used)
- Disk: 145 GB / 500 GB (45% used)
- No critical errors in logs

Status: All systems operational
```

### Log Analysis

```bash
$ mcp ai ask "Why did the OpenSearch cluster fail on ilgss1111?"

Investigating OpenSearch failure on ilgss1111...

Step 1: Checking service status...
? Service: inactive (failed)
? Exit code: 137 (OOM kill)

Step 2: Analyzing logs...
? Found OutOfMemoryError at 14:57:23
? Heap size: 2GB configured, attempted to allocate 3.2GB

ROOT CAUSE:
The OpenSearch cluster failed due to insufficient heap memory.
The JVM tried to allocate 3.2GB but only 2GB was configured,
triggering an out-of-memory kill by the system.

RECOMMENDATION:
Increase heap size in /etc/opensearch/jvm.options:
-Xms4g
-Xmx4g

Cost: $0.0342 today
```

### Interactive Investigation

```bash
$ mcp ai chat

Welcome to Orbit AI ??

You: What pods are failing in production?

Orbit AI: Checking production Kubernetes cluster...

Found 3 pods in CrashLoopBackOff:
- api-server-7d9f8 (15 restarts)
- worker-queue-4k2p1 (8 restarts)  
- redis-cache-9x7m4 (23 restarts)

You: Show logs for api-server

Orbit AI: Retrieving logs...

Key error found: "ECONNREFUSED redis:6379"
The API server can't connect to Redis.

You: Why is Redis failing?

Orbit AI: Checking Redis logs...

Redis error: "OOM command not allowed when used memory > 'maxmemory'"

ROOT CAUSE: Redis has run out of memory (maxmemory limit hit)

SOLUTION:
1. Increase Redis memory limit:
   kubectl edit deployment redis-cache
   # Set resources.limits.memory to 2Gi

2. Or clear Redis cache:
   kubectl exec redis-cache-9x7m4 -- redis-cli FLUSHALL

Would you like me to help execute this?
```

## ?? LLM Providers & Cost Management

### Supported Providers

| Provider | Best For | Cost | Setup |
|----------|----------|------|-------|
| **Ollama** | Privacy, unlimited usage | $0 (local) | `ollama pull llama2` |
| **OpenAI** | General reasoning | $0.0015-0.06/1K tokens | `export OPENAI_API_KEY=...` |
| **Anthropic** | Large context (100K tokens) | $0.00025-0.075/1K tokens | `export ANTHROPIC_API_KEY=...` |

### Cost Control

Automatic budget management:

```yaml
# ~/.mcp/config.yaml
llm:
  cost_control:
    daily_budget: 10.0      # Max $10/day
    monthly_budget: 200.0   # Max $200/month
    alert_at: 0.8           # Alert at 80%
    prefer_local: true      # Use Ollama for simple tasks
    auto_optimize: true     # Switch to cheaper models when needed
```

### Usage Tracking

```bash
$ mcp ai usage

Today:
  Cost:      $0.2450 / $10.00
  Tokens:    15,230
  Remaining: $9.76

This Month:
  Cost:      $12.45 / $200.00
  Tokens:    782,100
  Remaining: $187.55
```

### Cost Optimization

The agent automatically:
1. Uses **local models** (Ollama) for simple tasks
2. Uses **GPT-3.5** for moderate complexity
3. Uses **Claude** for large context (logs, configs)
4. Reserves **GPT-4/Claude-Opus** for complex reasoning

Example:
```
Simple query: "List pods"
? Uses: Ollama (free)

Complex analysis: "Diagnose cluster failure"
? Uses: Claude-3-Sonnet ($0.08)

Huge logs (50K tokens): "Analyze these logs"
? Uses: Claude (100K context) after optimization
? Optimizes: 50K tokens ? 3K tokens (95% reduction)
? Cost: $0.09 instead of $1.50
```

## ?? Usage Modes

### AI Ask (One-Shot)

```bash
# Basic queries
mcp ai ask "Check server prod-web-01"
mcp ai ask "List all running containers"
mcp ai ask "Show Kubernetes pod status"

# Complex diagnostics
mcp ai ask "Why is nginx down on prod-web-02?"
mcp ai ask "Analyze error logs from last hour"

# Specify provider
mcp ai ask "Complex query" --provider anthropic

# Output formats
mcp ai ask "List pods" --format json
```

### AI Chat (Interactive)

```bash
# Start session
mcp ai chat

# Commands inside chat
/help          # Show help
/status        # Usage stats
/model <name>  # Switch LLM
/reset         # Clear history
/exit          # Quit

# Just talk naturally
You: Check production status
You: Show me the logs
You: What's causing the errors?
```

### Traditional CLI

```bash
# SSH
mcp ssh list
mcp ssh exec prod-web-01 "systemctl status nginx"
mcp ssh logs prod-web-01 /var/log/nginx/error.log

# Docker
mcp docker list
mcp docker logs my-container
mcp docker stats my-container

# Kubernetes
mcp k8s pods -n production
mcp k8s logs my-pod -n default
mcp k8s scale my-deployment 5 -n production
```

## ?? Configuration Example

`~/.mcp/config.yaml`:

```yaml
# SSH Servers
ssh:
  servers:
    prod-web-01:
      host: 192.168.1.100
      username: admin
      key_file: ~/.ssh/id_rsa

# Docker Hosts
docker:
  hosts:
    local:
      type: local
      socket: unix:///var/run/docker.sock

# Kubernetes Clusters
kubernetes:
  clusters:
    prod-k8s:
      kubeconfig: ~/.kube/config
      context: prod-cluster

# LLM Configuration
llm:
  default_provider: ollama
  
  providers:
    openai:
      enabled: true
      model: gpt-3.5-turbo
      api_key: ${OPENAI_API_KEY}
    
    anthropic:
      enabled: true
      model: claude-3-sonnet
      api_key: ${ANTHROPIC_API_KEY}
    
    ollama:
      enabled: true
      model: llama2
      base_url: http://localhost:11434
  
  cost_control:
    daily_budget: 10.0
    monthly_budget: 200.0
    prefer_local: true

# Security
security:
  confirm_destructive: true
  allowed_commands:
    - systemctl
    - docker
    - kubectl
  blocked_patterns:
    - rm -rf
    - mkfs
```

## ??? Architecture

Orbit-MCP uses a hybrid architecture:

```
????????????????????????????????????????????????
?              ORBIT-MCP                       ?
?                                              ?
?  ??????????????  ????????????  ??????????? ?
?  ? MCP Server ?  ? AI Agent ?  ?   CLI   ? ?
?  ? (Cursor)   ?  ? (LLM)    ?  ? (Direct)? ?
?  ??????????????  ????????????  ??????????? ?
?         ?             ?             ?        ?
????????????????????????????????????????????????
          ?             ?             ?
          ???????????????             ?
                     ?                ?
            ???????????????????
            ? Tool Registry   ?
            ? (Infrastructure)?
            ???????????????????
                     ?
         ?????????????????????????
         ?           ?           ?
         ?           ?           ?
    ??????????  ??????????  ????????
    ?  SSH   ?  ? Docker ?  ? K8s  ?
    ??????????  ??????????  ????????
```

**AI Agent Loop:**
```
User Prompt
    ?
1. PARSE INTENT
    ?
2. CREATE PLAN (LLM)
    ?
3. EXECUTE STEPS (Tools)
    ?
4. REFLECT & ANALYZE (LLM)
    ?
Final Response
```

## ?? Security

### Credentials
- Stored in `~/.mcp/config.yaml` (0600 permissions)
- LLM API keys in environment variables
- SSH key-based auth recommended
- Never committed to version control

### Safety Features
- **Confirmation required** for destructive operations
- **Command allowlists** - Only permitted commands
- **Blocked patterns** - Dangerous commands blocked
- **Data redaction** - Secrets removed before LLM
- **Read-only default** - Most operations are diagnostic

### Best Practices
```bash
# ? Good - use SSH keys
mcp config add-ssh server host user --key ~/.ssh/id_rsa

# ? Avoid - plain text passwords
mcp config add-ssh server host user --password secret

# ? Good - environment variables for LLM keys
export OPENAI_API_KEY=sk-...

# ? Avoid - hardcoded in config
```

## ?? Documentation

- **[AI Agent Guide](docs/AI_AGENT_GUIDE.md)** - Complete AI agent documentation
- **[Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md)** - System design and data flow
- **[MCP Integration](docs/MCP_INTEGRATION.md)** - Cursor/IDE integration
- **[Configuration](config.example.yaml)** - Full config reference

## ??? Roadmap

### ? Phase 1: Core Platform (DONE)
- [x] SSH, Docker, Kubernetes management
- [x] Traditional CLI interface
- [x] MCP protocol server
- [x] Configuration management

### ? Phase 2: AI Integration (DONE)
- [x] Multi-LLM support (OpenAI, Anthropic, Ollama)
- [x] Plan-execute-reflect agent loop
- [x] Cost management and optimization
- [x] Interactive REPL mode
- [x] Token optimization

### ?? Phase 3: Enhanced AI (IN PROGRESS)
- [ ] Multi-turn self-correction
- [ ] Learning from incidents
- [ ] Automated runbook execution
- [ ] Voice interface
- [ ] Visual dashboards

### ?? Phase 4: Team & Enterprise
- [ ] Multi-user support
- [ ] RBAC and permissions
- [ ] PagerDuty/Slack integration
- [ ] Incident management
- [ ] Team collaboration
- [ ] Web UI dashboard

## ?? Use Cases

### DevOps On-Call
```bash
# Incident investigation
mcp ai chat
You: PagerDuty alert - API latency high
AI: [checks metrics, logs, pods] 
AI: Database connection pool exhausted...
```

### Infrastructure Audits
```bash
mcp ai ask "Check all production servers for security updates"
mcp ai ask "What containers are running outdated images?"
```

### Capacity Planning
```bash
mcp ai ask "Show resource usage trends for last week"
mcp ai ask "Which servers need more disk space?"
```

### Developer Productivity
```bash
# In Cursor while coding
You: "Check if staging deployment succeeded"
Cursor AI ? orbit-mcp ? K8s ? "Deployment successful, 3/3 pods ready"
```

## ?? Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## ?? License

MIT License - see [LICENSE](LICENSE) file

## ?? Support

- ?? [Open an issue](https://github.com/yourorg/orbit-mcp/issues)
- ?? Contact DevOps team
- ?? Check [documentation](docs/)

## ?? Acknowledgments

- Built with Python, Paramiko, Docker SDK, Kubernetes Client
- LLM integration: OpenAI, Anthropic, Ollama
- MCP protocol for AI tool integration
- Inspired by best practices in AI agents and DevOps automation

---

## ? Quick Command Reference

```bash
# AI Agent
mcp ai ask "<prompt>"              # One-shot query
mcp ai chat                        # Interactive mode
mcp ai models                      # List LLM models
mcp ai usage                       # Show costs

# Traditional CLI
mcp ssh exec <server> "<command>"  # Execute command
mcp docker ps                      # List containers
mcp k8s pods -n <namespace>        # List pods

# Configuration
mcp config list                    # Show config
mcp config show                    # Display full config
```

**Start using Orbit AI today! ??**

```bash
pip install -e .
mcp ai ask "Hello, introduce yourself"
```
