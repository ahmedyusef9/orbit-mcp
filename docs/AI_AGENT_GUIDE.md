# Orbit-MCP AI Agent Guide

## Overview

Orbit-MCP is a **hybrid system** that combines:
1. **MCP Server** - Exposes DevOps tools to AI assistants like Cursor
2. **AI Agent** - Built-in LLM-powered autonomous assistant
3. **Traditional CLI** - Direct command-line operations

This guide focuses on the **AI Agent** capabilities.

## What is the AI Agent?

The Orbit AI Agent is an intelligent DevOps assistant that can:

- ?? **Understand natural language** - Ask questions in plain English
- ?? **Plan and execute** - Break down complex tasks into steps
- ?? **Use DevOps tools** - SSH, Docker, Kubernetes, logs, etc.
- ?? **Reason and analyze** - Diagnose issues and explain root causes
- ?? **Optimize costs** - Intelligently choose LLMs based on task complexity
- ?? **Safe by default** - Confirms destructive operations

## Architecture: Plan-Execute-Reflect

The AI agent uses a sophisticated loop:

```
User Prompt
    ?
1. PARSE INTENT
   - What does the user want?
   - Which systems are involved?
   - How urgent is it?
    ?
2. CREATE PLAN
   - Break into steps
   - Identify required tools
   - Assess complexity
    ?
3. EXECUTE PLAN
   - Run each step
   - Gather results
   - Handle errors
    ?
4. REFLECT & SYNTHESIZE
   - Analyze results
   - Answer the question
   - Suggest next steps
    ?
User Response
```

## Usage Modes

### 1. One-Shot Mode (CLI)

Ask a single question and get an answer:

```bash
# Basic query
mcp ai ask "Check status of server prod-web-01"

# Complex diagnostic
mcp ai ask "Why did the OpenSearch cluster fail on ilgss1111?"

# Multi-step operation
mcp ai ask "Show me all running containers on staging and their resource usage"

# Specify LLM provider
mcp ai ask "Analyze nginx logs for errors" --provider anthropic

# Different output formats
mcp ai ask "List Kubernetes pods" --format json
```

### 2. Interactive Chat Mode (REPL)

Have a conversation with the AI:

```bash
# Start interactive session
mcp ai chat

# With specific provider
mcp ai chat --provider openai
```

Inside the REPL:
```
You: Check server prod-web-01 status
Orbit AI: [executes and shows results]

You: Show me the nginx logs
Orbit AI: [retrieves logs]

You: Summarize the errors
Orbit AI: [analyzes and summarizes]

You: /help
[shows commands]

You: /exit
```

## LLM Providers

### OpenAI (ChatGPT)

**Best for:** General reasoning, balanced performance

**Models:**
- `gpt-3.5-turbo` - Fast, cheap, good for simple tasks
- `gpt-4` - High quality reasoning
- `gpt-4-turbo` - Best balance of speed and quality

**Cost:** $0.0015-0.06 per 1K tokens (depending on model)

**Setup:**
```yaml
llm:
  providers:
    openai:
      enabled: true
      model: gpt-3.5-turbo
      api_key: ${OPENAI_API_KEY}
```

```bash
export OPENAI_API_KEY=sk-...
```

### Anthropic (Claude)

**Best for:** Large context (100K+ tokens), detailed analysis

**Models:**
- `claude-3-haiku` - Fast and cheap
- `claude-3-sonnet` - Balanced (recommended)
- `claude-3-opus` - Highest quality

**Cost:** $0.00025-0.075 per 1K tokens

**Setup:**
```yaml
llm:
  providers:
    anthropic:
      enabled: true
      model: claude-3-sonnet
      api_key: ${ANTHROPIC_API_KEY}
```

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Ollama (Local Models)

**Best for:** Privacy, no API costs, unlimited usage

**Models:**
- `llama2` - General purpose (7B, 13B, 70B)
- `mistral` - Fast and capable
- `codellama` - Code-focused
- `mixtral` - High quality

**Cost:** $0 (uses local compute)

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama2

# Configure orbit
llm:
  providers:
    ollama:
      enabled: true
      model: llama2
      base_url: http://localhost:11434
```

## Cost Management

### Budget Limits

Set daily and monthly budgets:

```yaml
llm:
  cost_control:
    daily_budget: 10.0     # $10 per day max
    monthly_budget: 200.0  # $200 per month max
    alert_at: 0.8          # Alert at 80%
```

### Automatic Cost Optimization

The agent automatically:

1. **Uses local models for simple tasks** (if `prefer_local: true`)
2. **Switches to cheaper models** when approaching budget
3. **Chooses Claude for large context** (long logs, configs)
4. **Selects premium models only for complex reasoning**

### Usage Tracking

```bash
# View usage and costs
mcp ai usage
```

Output:
```
Today:
  Cost:      $0.2450 / $10.00
  Tokens:    15,230
  Remaining: $9.76

This Month:
  Cost:      $12.45 / $200.00
  Tokens:    782,100
  Remaining: $187.55

All Time:
  Total Cost:   $127.89
  Total Tokens: 6,392,450
```

## Token Optimization

The agent minimizes token usage (and costs) by:

### 1. Log Filtering
Instead of sending 10,000 log lines, it extracts:
- Error lines
- Warnings
- Recent context around failures
- Relevant patterns

### 2. Context Truncation
For large inputs:
- Keeps critical parts (errors, recent data)
- Truncates middle sections
- Maintains semantic meaning

### 3. Smart Summarization
- Iterative log summarization
- Progressive detail reduction
- Preserves key information

Example:
```
Raw logs: 250KB (62,500 tokens ? $1.88)
Optimized: 12KB (3,000 tokens ? $0.09)
Savings: 95% reduction
```

## AI Agent Tools

The agent can use these tools internally:

### LLM-Powered Tools
- `llm.chat` - Conversational responses
- `llm.plan` - Create execution plans
- `llm.reason` - Analyze data and reason
- `llm.summarize_logs` - Condense log files

### Infrastructure Tools
- `ssh.execute` - Run commands on servers
- `docker.list` - List containers
- `docker.logs` - Get container logs
- `k8s.get_pods` - List Kubernetes pods
- `k8s.get_logs` - Get pod logs
- `logs.tail` - Tail system logs
- *(More tools coming in full orbit-mcp implementation)*

## Example Workflows

### 1. Server Health Check

```bash
mcp ai ask "Check if server prod-web-01 is healthy"
```

**What the agent does:**
1. Plans: "Need to check system status, load, disk, memory"
2. Executes: SSH to server, runs `uptime`, `df -h`, `free -m`
3. Analyzes: Reviews metrics for anomalies
4. Responds: "Server is healthy. Load: 0.8, Disk: 45% used, Memory: 62% used"

### 2. Log Analysis

```bash
mcp ai ask "Why did nginx fail on prod-web-01 at 3pm?"
```

**What the agent does:**
1. Plans: "Get nginx logs around 3pm, filter for errors"
2. Executes: SSH to server, gets logs from 2:45-3:15pm
3. Optimizes: Extracts error lines only
4. Analyzes: Uses LLM to identify root cause
5. Responds: "Nginx failed due to SSL certificate expiration at 14:57. The error log shows: 'SSL_CTX_use_certificate_file failed'"

### 3. Cluster Diagnostics

```bash
mcp ai ask "Diagnose why OpenSearch cluster is red"
```

**What the agent does:**
1. Plans: Multi-step diagnostic
   - Check cluster health
   - Get shard status
   - Review recent logs
   - Check disk space
2. Executes: Each step, gathering data
3. Correlates: Finds connection between logs and disk
4. Responds: "Cluster is RED because of unassigned shards. Root cause: Node 1 has 98% disk usage, triggering shard allocation failure. Recommendation: Clear disk space or add storage"

### 4. Multi-Step Investigation

```bash
# Start chat session
mcp ai chat
```

```
You: What pods are failing in production?

Orbit AI: Checking production Kubernetes cluster...
Found 3 pods in CrashLoopBackOff:
- api-server-7d9f8 (restarting 15 times)
- worker-queue-4k2p1 (restarting 8 times)
- redis-cache-9x7m4 (restarting 23 times)

You: Show logs for api-server

Orbit AI: Retrieving logs for api-server-7d9f8...
[shows last 50 lines with errors highlighted]

Key error: "ECONNREFUSED redis:6379"

You: So it can't connect to redis?

Orbit AI: Correct! The api-server can't reach Redis. 
This explains the cascade: api-server crashes ? workers can't process ? system degraded.

The redis pod is also crashing (23 restarts). Let me check why...
[retrieves redis logs]

Redis is out of memory: "OOM command not allowed"

Root cause: Redis memory limit too low for current load.

You: How do I fix it?

Orbit AI: To resolve:

1. **Immediate:** Increase Redis memory limit
   ```bash
   kubectl edit deployment redis-cache
   # Increase resources.limits.memory to 2Gi
   ```

2. **Monitor:** Watch pods recover
   ```bash
   kubectl get pods -w
   ```

3. **Verify:** Check if errors stop

Would you like me to help with any of these steps?
```

## Safety & Confirmation

The agent is **safe by default**:

### Read-Only by Default
- Most operations are diagnostic (read-only)
- No accidental changes to production

### Confirmation Required
For destructive actions (restart, delete, modify):

```bash
You: Restart the nginx service on prod-web-01

Orbit AI: ??  This operation will restart nginx, causing brief downtime.

Command: systemctl restart nginx
Server: prod-web-01

Proceed? (yes/no): yes

[executes]

? Nginx restarted successfully
```

### Command Allowlists
Only permitted commands can be executed (configured in `config.yaml`):

```yaml
security:
  allowed_commands:
    - systemctl
    - journalctl
    - docker
    - kubectl
    - tail
    - cat
  
  blocked_patterns:
    - rm -rf
    - mkfs
    - dd if=
```

## Configuration

Full LLM configuration in `~/.mcp/config.yaml`:

```yaml
llm:
  # Which provider to use by default
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
    alert_at: 0.8
    auto_optimize: true
    prefer_local: true
  
  token_optimization:
    max_context_tokens: 4000
    aggressive_truncation: true
    log_summarization: true
```

## Model Selection Strategy

The agent automatically chooses models based on:

| Task Complexity | Context Size | Budget | Selected Model |
|----------------|--------------|---------|----------------|
| Simple (1-3)   | < 4K tokens  | Any     | Ollama (if available) |
| Moderate (4-7) | < 30K tokens | > $1    | GPT-3.5-turbo |
| Complex (8-9)  | < 100K tokens| > $5    | Claude-3-sonnet |
| Advanced (10)  | Any          | > $5    | Claude-3-opus or GPT-4 |

Override:
```bash
mcp ai ask "complex query" --provider anthropic
```

## Commands Reference

```bash
# One-shot queries
mcp ai ask "<prompt>"
mcp ai ask "<prompt>" --provider <name>
mcp ai ask "<prompt>" --format json

# Interactive chat
mcp ai chat
mcp ai chat --provider <name>

# Model management
mcp ai models           # List available models
mcp ai usage            # Show usage and costs

# REPL commands (inside chat)
/help                   # Show help
/status                 # Usage stats
/model [name]           # List or switch model
/reset                  # Reset conversation
/exit                   # Exit
```

## Best Practices

### 1. Use Local Models for Routine Tasks
```bash
# Set ollama as default
llm:
  default_provider: ollama
  cost_control:
    prefer_local: true
```

### 2. Reserve Premium Models for Complex Issues
```bash
# Use Claude only when needed
mcp ai ask "complex diagnostic issue requiring deep analysis" --provider anthropic
```

### 3. Monitor Costs Regularly
```bash
mcp ai usage
```

### 4. Set Conservative Budgets Initially
```yaml
cost_control:
  daily_budget: 5.0   # Start low, adjust up if needed
```

### 5. Use Interactive Mode for Investigations
```bash
# REPL maintains context across questions
mcp ai chat
```

## Integration with MCP (Cursor)

The AI agent can also be used **from within Cursor**:

1. Cursor connects to orbit-mcp as an MCP server
2. Cursor's AI (Claude/GPT) uses orbit's tools
3. The benefit: Cursor's UI + orbit's tools

vs.

1. Use orbit AI directly in terminal
2. The benefit: No Cursor needed, works anywhere

**When to use which:**
- **Cursor integration:** When coding and want AI in the IDE
- **Orbit AI direct:** When in terminal, SSH sessions, on-call incidents

## Troubleshooting

### "AI features not available"
```bash
# Install AI dependencies
pip install openai anthropic tiktoken
```

### "No LLM configuration found"
Create `~/.mcp/config.yaml` with LLM section (see config.example.yaml)

### "Provider not configured: openai"
```bash
export OPENAI_API_KEY=sk-...
# Or add to config.yaml
```

### Ollama not responding
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model if needed
ollama pull llama2
```

### High costs
```bash
# Check usage
mcp ai usage

# Lower budgets
vim ~/.mcp/config.yaml
# Set lower daily_budget

# Prefer local models
llm:
  cost_control:
    prefer_local: true
```

## Future Enhancements

Coming soon to orbit-mcp:

- [ ] Multi-turn planning with self-correction
- [ ] Learning from past incidents
- [ ] Automated runbook execution
- [ ] Integration with incident management (PagerDuty, etc.)
- [ ] Visual dashboards and charts
- [ ] Voice interface
- [ ] Slack/Teams bot integration

## Comparison: Orbit AI vs MCP Client

### Orbit AI Agent (Built-in)
**Pros:**
- ? Works standalone (no IDE needed)
- ? Terminal-friendly
- ? Direct cost control
- ? Choose your own LLM
- ? Perfect for on-call, SSH sessions

**Cons:**
- ? No IDE integration
- ? Separate from coding workflow

### MCP Client (Cursor Integration)
**Pros:**
- ? Integrated in IDE
- ? Part of coding workflow
- ? Beautiful UI
- ? Context from code

**Cons:**
- ? Requires Cursor/compatible IDE
- ? Less control over LLM choice
- ? Harder to use in pure ops scenarios

### Best of Both Worlds

**Use both!**
- Orbit AI for investigations, incidents, on-call
- Cursor+MCP for coding, reviewing, planning

---

## Getting Started

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure LLM
cp config.example.yaml ~/.mcp/config.yaml
vim ~/.mcp/config.yaml
# Add API keys or enable Ollama

# 3. Test it
mcp ai ask "Hello, can you introduce yourself?"

# 4. Start using
mcp ai chat
```

**Welcome to Orbit AI! ??**
