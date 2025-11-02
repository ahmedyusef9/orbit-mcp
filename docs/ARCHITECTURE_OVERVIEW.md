# Orbit-MCP Architecture Overview

## System Architecture

Orbit-MCP is a **hybrid system** with three operational modes:

```
???????????????????????????????????????????????????????????????
?                       ORBIT-MCP                              ?
?                                                              ?
?  ??????????????????  ??????????????????  ????????????????  ?
?  ?   MCP Server   ?  ?   AI Agent     ?  ?  CLI Mode    ?  ?
?  ?                ?  ?                ?  ?              ?  ?
?  ?  For Cursor    ?  ?  Autonomous    ?  ?  Direct      ?  ?
?  ?  Integration   ?  ?  LLM-powered   ?  ?  Commands    ?  ?
?  ??????????????????  ??????????????????  ????????????????  ?
?          ?                   ?                   ?          ?
???????????????????????????????????????????????????????????????
           ?                   ?                   ?
           ?                   ?                   ?
    ???????????????    ????????????????    ??????????????
    ?   Cursor    ?    ?  Terminal    ?    ?  Scripts   ?
    ?   (IDE)     ?    ?  (Human)     ?    ?  (Auto)    ?
    ???????????????    ????????????????    ??????????????
                               ?
                               ?
                     ????????????????????????
                     ?    Tool Registry     ?
                     ?  (Infrastructure)    ?
                     ????????????????????????
                               ?
           ?????????????????????????????????????????
           ?                   ?                   ?
           ?                   ?                   ?
      ??????????         ???????????        ????????????
      ?  SSH   ?         ? Docker  ?        ?   K8s    ?
      ??????????         ???????????        ????????????
```

## Mode 1: MCP Server (Cursor Integration)

### Purpose
Expose DevOps tools to AI assistants via Model Context Protocol.

### Flow
```
Cursor (IDE)
    ? STDIO/HTTP
MCP Protocol Layer
    ? JSON-RPC 2.0
Tool Handlers
    ?
Infrastructure (SSH, Docker, K8s)
```

### Key Components
- **Protocol Handler** (`src/mcp/protocol.py`)
  - Implements MCP JSON-RPC 2.0
  - Methods: `initialize`, `tools/list`, `tools/call`, `ping`
  
- **Transport Layer** (`src/mcp/transports.py`)
  - STDIO transport (local)
  - HTTP+SSE transport (remote)
  
- **Tool Registry**
  - Defines 40+ tools
  - SSH, Docker, Compose, K8s, Helm, Logs, etc.

### Usage
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
User: "Check status of prod-web-01"
Cursor AI ? orbit-mcp ? SSH ? result ? Cursor AI ? User
```

## Mode 2: AI Agent (Autonomous)

### Purpose
Standalone AI assistant with embedded LLM for natural language DevOps.

### Flow
```
User Prompt
    ?
Intent Parser
    ?
Planner (LLM)
    ?
Executor (Tools)
    ?
Reflector (LLM)
    ?
Response
```

### Plan-Execute-Reflect Loop

#### 1. Parse Intent
```python
User: "Why did OpenSearch fail on ilgss1111?"
    ?
Intent Parser (LLM):
{
  "intent_type": "diagnose_failure",
  "entities": ["ilgss1111", "OpenSearch"],
  "urgency": "high",
  "requires_confirmation": false
}
```

#### 2. Create Plan
```python
Planner (LLM):
Plan:
  1. SSH to ilgss1111, check service status
  2. If failed, retrieve OpenSearch logs
  3. Analyze logs for error patterns
  4. Identify root cause
  5. Suggest remediation
```

#### 3. Execute Plan
```python
Executor:
  Step 1: ssh.execute(host="ilgss1111", cmd="systemctl status opensearch")
          ? Result: "failed (exit code 137)"
  
  Step 2: ssh.execute(host="ilgss1111", cmd="tail -1000 /var/log/opensearch/...")
          ? Result: [10000 lines of logs]
          ? Optimized: [extract error lines] ? [50 lines]
  
  Step 3: llm.summarize_logs(logs=[50 lines])
          ? Result: "OutOfMemoryError at startup"
  
  Step 4: llm.reason(data=[status, logs, summary])
          ? Result: "Root cause identified: insufficient heap memory"
```

#### 4. Reflect & Synthesize
```python
Reflector (LLM):
  - Review: All steps completed successfully
  - Analysis: Root cause clear (OOM)
  - Completeness: Sufficient to answer question
  
  Final Response:
  "The OpenSearch cluster on ilgss1111 failed to start because it 
   ran out of memory during initialization. The service status shows
   exit code 137 (OOM kill), and logs contain OutOfMemoryError at 
   startup. 
   
   Recommendation: Increase heap memory allocation in 
   /etc/opensearch/jvm.options or add more RAM to the server."
```

### LLM Integration

#### Multiple Providers
```python
class LLMClient:
    providers = {
        'openai': OpenAIProvider(model='gpt-3.5-turbo'),
        'anthropic': AnthropicProvider(model='claude-3-sonnet'),
        'ollama': OllamaProvider(model='llama2')
    }
    
    def generate(prompt, provider=None):
        # Auto-select based on task complexity, context size, budget
        provider = provider or self._select_optimal_provider()
        return providers[provider].generate(prompt)
```

#### Cost Manager
```python
class CostManager:
    budgets = {
        'daily': 10.0,
        'monthly': 200.0
    }
    
    def can_make_request(estimated_cost):
        if daily_cost + estimated_cost > daily_budget:
            return False
        return True
    
    def record_usage(tokens, cost):
        # Track and persist
        usage['daily']['cost'] += cost
        usage['daily']['tokens'] += tokens
```

#### Token Optimizer
```python
class TokenOptimizer:
    def optimize_log_content(log, max_lines=500):
        # Extract error lines
        errors = [line for line in log if 'ERROR' in line]
        
        # Extract warnings
        warnings = [line for line in log if 'WARN' in line]
        
        # Recent context
        recent = log[-100:]
        
        # Combine, deduplicate, limit
        optimized = unique(errors + warnings + recent)[:max_lines]
        
        # 95% token reduction achieved
        return '\n'.join(optimized)
```

### Usage Modes

#### CLI One-Shot
```bash
$ mcp ai ask "Check server prod-web-01 status"

[Processing...]

? Server prod-web-01 is healthy
- Uptime: 23 days
- Load: 0.8, 1.2, 1.5
- Memory: 62% used
- Disk: 45% used (/)

Cost: $0.0023 today
```

#### Interactive REPL
```bash
$ mcp ai chat

Welcome to Orbit AI ??

You: What pods are failing?

Orbit AI: Checking production cluster...
Found 3 pods in CrashLoopBackOff:
- api-server-7d9f8 (15 restarts)
- worker-4k2p1 (8 restarts)
- redis-9x7m4 (23 restarts)

You: Show redis logs

Orbit AI: [shows logs with error highlighted]
OOM command not allowed

You: How do I fix it?

Orbit AI: Increase Redis memory limit:
kubectl edit deployment redis-cache
# Set resources.limits.memory to 2Gi

You: /exit

Goodbye! ??
```

## Mode 3: Traditional CLI

### Purpose
Direct command-line operations without AI.

### Usage
```bash
# SSH operations
mcp ssh list
mcp ssh exec prod-web-01 "systemctl status nginx"

# Docker operations
mcp docker list
mcp docker logs my-container

# Kubernetes operations
mcp k8s pods
mcp k8s logs my-pod

# Configuration
mcp config show
mcp config set ssh.servers.prod.host 192.168.1.100
```

## Core Components

### 1. Configuration Manager
```python
class ConfigManager:
    config_file = "~/.mcp/config.yaml"
    
    config = {
        'ssh': {...},
        'docker': {...},
        'kubernetes': {...},
        'llm': {...}
    }
    
    def load_config()
    def save_config()
    def get(key)
    def set(key, value)
```

### 2. Tool Registry
```python
tools = {
    'ssh.execute': {
        'description': 'Execute command on remote server',
        'handler': ssh_manager.execute_command,
        'schema': {...}
    },
    'docker.list': {
        'description': 'List Docker containers',
        'handler': docker_manager.list_containers,
        'schema': {...}
    },
    # ... 40+ more tools
}
```

### 3. Infrastructure Managers

#### SSHManager
```python
class SSHManager:
    def connect(server_name)
    def execute_command(host, command)
    def upload_file(host, local, remote)
    def download_file(host, remote, local)
    def tail_logs(host, file, lines)
```

#### DockerManager
```python
class DockerManager:
    def list_containers(host)
    def start_container(host, container_id)
    def stop_container(host, container_id)
    def get_logs(host, container_id, lines)
    def get_stats(host, container_id)
```

#### KubernetesManager
```python
class KubernetesManager:
    def list_pods(context, namespace)
    def get_pod_logs(context, namespace, pod, lines)
    def scale_deployment(context, namespace, deployment, replicas)
    def restart_deployment(context, namespace, deployment)
```

## Data Flow Examples

### Example 1: MCP Server Mode (Cursor)

```
1. User in Cursor: "Check prod-web-01 status"

2. Cursor AI decides to use orbit-mcp tools

3. Cursor ? MCP JSON-RPC:
   {
     "method": "tools/call",
     "params": {
       "name": "ssh.execute",
       "arguments": {
         "host": "prod-web-01",
         "command": "uptime && free -m && df -h"
       }
     }
   }

4. Orbit MCP Server:
   - Validates request
   - Calls ssh_manager.execute_command()
   - Returns result

5. Cursor ? Response:
   {
     "result": {
       "stdout": "...uptime, memory, disk output...",
       "exit_code": 0
     }
   }

6. Cursor AI interprets result ? User:
   "The server is healthy with 23 days uptime..."
```

### Example 2: AI Agent Mode (Autonomous)

```
1. User in terminal: mcp ai ask "Why nginx down on prod?"

2. AI Agent:
   - Parse: intent="diagnose_failure", entity="nginx", host="prod"
   
   - Plan:
     Step 1: Check nginx service status
     Step 2: Get nginx error logs
     Step 3: Analyze logs for root cause
   
   - Execute:
     Step 1: ssh.execute("prod", "systemctl status nginx")
             ? "inactive (failed)"
     
     Step 2: ssh.execute("prod", "tail -500 /var/log/nginx/error.log")
             ? [500 lines]
             ? optimize_logs() ? [15 error lines]
     
     Step 3: llm.reason(status + error_lines)
             ? "Config syntax error on line 42"
   
   - Reflect:
     ? Sufficient data gathered
     ? Root cause identified
     ? Can provide solution
   
   - Synthesize:
     "Nginx failed due to configuration syntax error on line 42.
      Error: 'invalid number of arguments in "server_name"'
      Fix: Check /etc/nginx/nginx.conf line 42"

3. User receives full diagnosis in terminal
```

### Example 3: Traditional CLI Mode

```
1. User: mcp ssh exec prod-web-01 "systemctl status nginx"

2. CLI:
   - Parse command
   - Load config (get prod-web-01 credentials)
   - Call ssh_manager.execute_command()
   - Print result to stdout

3. User sees raw output (no AI interpretation)
```

## Security Architecture

### 1. Credential Management
```python
# Stored encrypted in ~/.mcp/config.yaml
ssh:
  servers:
    prod:
      host: 192.168.1.100
      key_file: ~/.ssh/id_rsa  # Never exposed

# LLM keys in environment
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Command Allowlists
```python
allowed_commands = [
    'systemctl',
    'journalctl',
    'docker',
    'kubectl',
    'tail',
    'cat',
    'grep',
    'ls'
]

blocked_patterns = [
    'rm -rf',
    'mkfs',
    'dd if=',
    '> /dev'
]

def validate_command(cmd):
    if any(pattern in cmd for pattern in blocked_patterns):
        raise SecurityError("Command blocked")
    
    if not any(cmd.startswith(allowed) for allowed in allowed_commands):
        raise SecurityError("Command not in allowlist")
```

### 3. Confirmation for Destructive Actions
```python
def execute_tool(tool_name, args):
    if tools[tool_name]['destructive']:
        if not confirm(f"About to {tool_name} - proceed?"):
            raise Cancelled("User cancelled")
    
    return tools[tool_name]['handler'](**args)
```

### 4. Data Redaction
```python
def redact_sensitive(text):
    # Remove common secrets before sending to LLM
    patterns = [
        r'sk-[A-Za-z0-9]+',  # API keys
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IPs
        r'password["\s:=]+\S+',  # Passwords
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '[REDACTED]', text)
    
    return text
```

## Performance Optimization

### 1. Caching
```python
@cache(ttl=300)  # 5 minutes
def list_pods(context, namespace):
    # Expensive K8s API call
    return k8s_api.list_pods()
```

### 2. Parallel Execution
```python
async def execute_plan(steps):
    # Identify independent steps
    parallel_groups = analyze_dependencies(steps)
    
    for group in parallel_groups:
        # Execute independent steps in parallel
        results = await asyncio.gather(*[
            execute_step(step) for step in group
        ])
```

### 3. Token Optimization
```python
# Before: 10,000 log lines = 40,000 tokens = $1.20
raw_logs = ssh.execute("tail -10000 /var/log/app.log")

# After: Extract relevant = 200 lines = 800 tokens = $0.024
optimized = token_optimizer.optimize_log_content(raw_logs)

# 98% cost reduction
```

### 4. LLM Provider Selection
```python
def select_provider(task_complexity, context_size, budget_remaining):
    if budget_remaining < 0.10:
        return 'ollama'  # Local, free
    
    if context_size > 30000:
        return 'anthropic'  # 100K context window
    
    if task_complexity <= 5:
        return 'ollama'  # Simple task
    
    if task_complexity <= 8:
        return 'openai'  # gpt-3.5-turbo, cheap
    
    return 'anthropic'  # claude-3-sonnet, premium
```

## Deployment Patterns

### Pattern 1: Local Development
```bash
# Install locally
pip install -e .

# Use directly
mcp ai chat
```

### Pattern 2: Cursor Integration
```json
{
  "mcpServers": {
    "orbit-mcp": {
      "command": "mcp-server",
      "transport": "stdio"
    }
  }
}
```

### Pattern 3: Remote MCP Server
```bash
# Run as service
mcp-server --transport http --host 0.0.0.0 --port 8080

# Clients connect via HTTP+SSE
```

### Pattern 4: Team Deployment
```bash
# Deploy on bastion host
# Team members SSH and use
ssh bastion
mcp ai ask "check production status"
```

## Future Architecture Enhancements

### 1. Multi-Agent Collaboration
```python
# Multiple specialized agents
agents = {
    'diagnostics': DiagnosticAgent(tools=['ssh', 'logs']),
    'remediation': RemediationAgent(tools=['docker', 'k8s']),
    'security': SecurityAgent(tools=['audit', 'compliance'])
}

# Coordinator delegates to specialists
coordinator.handle_incident(agents)
```

### 2. Learning & Adaptation
```python
# Learn from past incidents
incident_db.record({
    'symptoms': [...],
    'root_cause': '...',
    'resolution': '...'
})

# Suggest solutions based on history
similar_incidents = incident_db.search(current_symptoms)
suggest_resolution(similar_incidents)
```

### 3. Proactive Monitoring
```python
# Agent continuously monitors
while True:
    metrics = collect_metrics()
    
    if agent.detect_anomaly(metrics):
        agent.investigate()
        agent.alert_human()
    
    sleep(60)
```

### 4. Integration Hub
```python
# Connect to external systems
integrations = {
    'pagerduty': PagerDutyIntegration(),
    'slack': SlackIntegration(),
    'jira': JiraIntegration(),
    'datadog': DatadogIntegration()
}

# Auto-create tickets, send alerts, etc.
```

## Summary

Orbit-MCP provides three complementary modes:

| Mode | Use Case | User | LLM Location |
|------|----------|------|--------------|
| **MCP Server** | IDE integration | Developer in Cursor | Cursor (Claude/GPT) |
| **AI Agent** | Autonomous ops | DevOps in terminal | Built-in (OpenAI/Anthropic/Ollama) |
| **Traditional CLI** | Direct commands | Automation scripts | None |

**Key Innovation:** Hybrid architecture allows using the right tool for the job:
- Coding? Use Cursor + MCP Server
- On-call? Use AI Agent in terminal
- Scripts? Use Traditional CLI

All three modes share the same underlying tool registry and infrastructure managers, ensuring consistency and reducing duplication.
