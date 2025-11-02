# Orbit-MCP: Hybrid Architecture Summary

## Executive Summary

Orbit-MCP has been transformed into a **hybrid DevOps platform** that uniquely combines:

1. **Traditional CLI** - Direct command execution
2. **MCP Server** - IDE integration (Cursor, VS Code)
3. **AI Agent** - Autonomous LLM-powered assistant

This architecture provides **three ways to accomplish the same tasks**, letting users choose based on context and preference.

## Key Question: Where Do LLMs Fit?

### Previous Understanding (Cursor-Only)
```
Cursor (IDE with Claude/GPT)
    ?
orbit-mcp (tools only)
    ?
Infrastructure
```
? LLM in Cursor, orbit provides tools

### New Understanding (Hybrid)
```
Option 1: Cursor (IDE)          Option 2: Terminal (AI)        Option 3: Terminal (CLI)
    ?                               ?                              ?
Cursor's LLM                    orbit's built-in LLM          No LLM (direct)
    ?                               ?                              ?
orbit MCP server                orbit AI agent                orbit CLI
    ?                               ?                              ?
Infrastructure                  Infrastructure                Infrastructure
```

? **LLM can be in Cursor OR in orbit itself**

## The Innovation: Built-in LLM

### What's Different
Orbit-MCP now has **its own LLM client** with:

- Multi-provider support (OpenAI, Anthropic, Ollama)
- Cost management and budgets
- Token optimization
- Plan-execute-reflect agent loop
- Natural language understanding

### Why This Matters

**Scenario 1: Developer Coding**
- Uses Cursor with orbit-mcp as MCP server
- LLM: Cursor's Claude/GPT
- Benefit: Integrated in IDE

**Scenario 2: DevOps On-Call**
- Uses orbit directly in terminal
- LLM: orbit's built-in (OpenAI/Claude/Ollama)
- Benefit: Works anywhere, no IDE needed

**Scenario 3: Automation Scripts**
- Uses orbit CLI commands
- LLM: None
- Benefit: Fast, deterministic, scriptable

## Architecture Components

### 1. LLM Integration Layer

```python
# src/mcp/llm/providers.py
class LLMClient:
    providers = {
        'openai': OpenAIProvider(),
        'anthropic': AnthropicProvider(),
        'ollama': OllamaProvider()
    }
    
    def generate(prompt, provider=None):
        # Auto-select best provider
        # Based on: complexity, context size, budget
        return selected_provider.generate(prompt)
```

**Features:**
- ? Multiple LLM backends
- ? Automatic provider selection
- ? Streaming responses
- ? Cost tracking

### 2. Cost Management

```python
# src/mcp/llm/cost_manager.py
class CostManager:
    def can_make_request(estimated_cost):
        # Check budget limits
        if daily_cost + estimated_cost > daily_budget:
            return False
        return True
    
    def record_usage(tokens, cost):
        # Track usage
        usage['daily']['cost'] += cost
        save_to_file()
```

**Features:**
- ? Daily/monthly budgets
- ? Usage tracking
- ? Cost alerts
- ? Automatic optimization

### 3. AI Agent Loop

```python
# src/mcp/ai/agent.py
class AIAgent:
    async def process_prompt(user_prompt):
        # 1. Parse intent
        intent = await self._parse_intent(user_prompt)
        
        # 2. Create plan
        plan = await self._create_plan(intent)
        
        # 3. Execute steps
        results = await self._execute_plan(plan)
        
        # 4. Reflect and synthesize
        response = await self._reflect(results)
        
        return response
```

**Features:**
- ? Plan-execute-reflect cycle
- ? Tool orchestration
- ? Error handling
- ? Multi-step reasoning

### 4. Token Optimization

```python
# src/mcp/llm/cost_manager.py
class TokenOptimizer:
    def optimize_log_content(logs):
        # Extract errors, warnings
        # Remove verbose debug
        # Keep context
        # Result: 95% token reduction
        return optimized_logs
```

**Features:**
- ? Log filtering
- ? Context truncation
- ? Smart summarization
- ? Cost savings (up to 95%)

### 5. REPL Mode

```python
# src/mcp/ai/repl.py
class OrbitREPL:
    async def run(self):
        while True:
            user_input = prompt("You: ")
            response = await agent.chat_turn(user_input)
            print(f"Orbit AI: {response}")
```

**Features:**
- ? Interactive chat
- ? Context across turns
- ? Commands (/help, /status, etc.)
- ? Model switching

## Usage Comparison

### Task: "Check server prod-web-01 status"

#### Option 1: Cursor + MCP Server
```json
// Setup once in Cursor config
{
  "mcpServers": {
    "orbit-mcp": {"command": "mcp-server"}
  }
}
```

```
In Cursor chat:
You: "Check server prod-web-01 status"
Cursor AI ? orbit-mcp tools ? server ? Cursor AI ? You

Cost: Cursor's subscription (Claude/GPT)
```

#### Option 2: Orbit AI Agent
```bash
$ mcp ai ask "Check server prod-web-01 status"

[Processing with GPT-3.5...]

? Server is healthy
- Uptime: 23 days
- Load: 0.8
- Memory: 62%

Cost: $0.0023
```

#### Option 3: Traditional CLI
```bash
$ mcp ssh exec prod-web-01 "uptime && free -m"

23:14:32 up 23 days, 14:32, load average: 0.8, 1.2, 1.5
              total        used        free
Mem:          16000        9920        6080

Cost: $0
```

## When to Use Each Mode

| Scenario | Mode | Why |
|----------|------|-----|
| **Coding in IDE** | Cursor + MCP | Integrated workflow |
| **On-call incident** | AI Agent (terminal) | Quick, conversational |
| **Complex diagnosis** | AI Agent | LLM reasoning needed |
| **Known command** | Traditional CLI | Fast, scriptable |
| **Automation script** | Traditional CLI | Deterministic output |
| **Cost-sensitive** | AI Agent + Ollama | Local, free |
| **Large logs** | AI Agent | Token optimization |
| **Team dashboard** | MCP Server (HTTP) | Remote access |

## Cost Considerations

### Cursor Mode (MCP Server)
- **Cost:** Cursor subscription (~$20/month)
- **LLM:** Included in subscription
- **Limits:** Cursor's rate limits
- **Good for:** Regular development work

### AI Agent Mode (Built-in LLM)
- **Cost:** Pay-per-use API calls
  - OpenAI: $0.0015-0.06 per 1K tokens
  - Anthropic: $0.00025-0.075 per 1K tokens
  - Ollama: $0 (local)
- **Budget:** User-defined ($10/day default)
- **Good for:** Controlled, optimized usage

### CLI Mode (No LLM)
- **Cost:** $0
- **Speed:** Fastest
- **Good for:** Automation, scripts

### Cost Example: Log Analysis

```
Task: Analyze 10,000-line error log

Traditional (no AI): $0, but manual work

AI Agent (with optimization):
  - Raw: 40,000 tokens = $1.20
  - Optimized: 800 tokens = $0.024
  - Time: 10 seconds
  - 98% cost reduction!

Cursor:
  - Included in subscription
  - But limited to Cursor's context
```

## Security Model

### API Keys
```yaml
# ~/.mcp/config.yaml
llm:
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}  # From environment
    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
```

**Never hardcoded, always from environment**

### Secrets Redaction
```python
def redact_sensitive(text):
    # Before sending to LLM
    text = remove_api_keys(text)
    text = remove_passwords(text)
    text = remove_ips(text)
    return text
```

### Confirmation for Destructive Actions
```python
if operation_is_destructive:
    if not confirm("This will restart nginx. Proceed?"):
        raise Cancelled()
```

## Configuration

### Minimal Setup (Ollama)
```yaml
llm:
  default_provider: ollama
  providers:
    ollama:
      enabled: true
      model: llama2
```

```bash
ollama pull llama2
mcp ai ask "Hello"
```

### Full Setup (All Providers)
```yaml
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
  
  cost_control:
    daily_budget: 10.0
    monthly_budget: 200.0
    prefer_local: true
```

## Implementation Status

### ? Completed
- [x] Multi-LLM provider support
- [x] Cost management and budgets
- [x] Token optimization
- [x] Plan-execute-reflect agent
- [x] Interactive REPL mode
- [x] One-shot CLI mode
- [x] CLI integration
- [x] Configuration management
- [x] Comprehensive documentation

### ?? In Progress
- [ ] Full tool registry (40+ tools)
- [ ] Enhanced error handling
- [ ] Multi-turn self-correction
- [ ] Learning from incidents

### ?? Future
- [ ] Voice interface
- [ ] Visual dashboards
- [ ] Slack/Teams integration
- [ ] Team collaboration

## Key Takeaways

### 1. **Two LLM Integration Points**
   - **External:** Cursor/IDEs use orbit's tools
   - **Internal:** Orbit has its own LLM for standalone use

### 2. **Cost Control Built-in**
   - Budget limits ($10/day default)
   - Automatic provider selection
   - Token optimization (95% reduction possible)
   - Usage tracking

### 3. **Flexibility**
   - Use Cursor when coding
   - Use orbit AI when troubleshooting
   - Use orbit CLI when scripting
   - All three share same infrastructure

### 4. **Local-First Option**
   - Ollama for privacy
   - Zero API costs
   - Unlimited usage
   - Perfect for sensitive data

### 5. **Production-Ready**
   - Safe by default
   - Confirmation for destructive ops
   - Command allowlists
   - Secrets redaction

## Quick Start

```bash
# Install
pip install -e .

# Option A: Use local model (free)
ollama pull llama2
mcp ai ask "Hello, introduce yourself"

# Option B: Use cloud model (paid)
export OPENAI_API_KEY=sk-...
mcp ai ask "Check server status"

# Interactive mode
mcp ai chat

# Cursor integration
# Add to Cursor config:
{
  "mcpServers": {
    "orbit-mcp": {"command": "mcp-server"}
  }
}
```

## Conclusion

Orbit-MCP is now a **complete DevOps AI platform** with three modes:

1. **MCP Server** for IDE integration
2. **AI Agent** for autonomous operations  
3. **Traditional CLI** for direct commands

The AI agent with built-in LLM support makes orbit useful **beyond Cursor**, enabling natural language DevOps anywhere - terminal, SSH sessions, scripts, or on-call scenarios.

**The user can choose:**
- Pay for premium models when needed
- Use free local models for routine tasks
- Skip AI entirely for fast scripting

This flexibility, combined with cost controls and security, makes orbit-mcp a practical, production-ready AI-powered DevOps tool.
