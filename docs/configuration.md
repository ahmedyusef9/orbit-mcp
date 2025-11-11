# Orbit-MCP Configuration

Orbit-MCP keeps all user credentials, tool preferences, and LLM settings in a single YAML file. This guide shows how to bootstrap the config in minutes, mirror the Task Master tool-scoping pattern, and wire the same core to both the MCP server and CLI.

> **Ask AI**  
> “Draft an `~/.mcp/config.yaml` that includes prod and staging SSH hosts, enables OpenAI + Ollama, and scopes tools to the `standard` preset.”

---

## 1. Where configuration lives

- Default path: `~/.mcp/config.yaml`
- Create with `mcp config init`
- Override per command with `mcp --config /path/to/config.yaml …`
- Cursor/Claude Code will also pick up `ORBIT_CONFIG` if you prefer an environment variable.

```bash
# create a fresh config
mcp config init

# inspect what got generated
mcp config list
```

You can safely keep multiple configs side by side:

```bash
~/.mcp/config.dev.yaml
~/.mcp/config.staging.yaml
~/.mcp/config.prod.yaml
```

Switch in one command:

```bash
mcp --config ~/.mcp/config.prod.yaml ssh exec prod-web-01 "uptime"
```

---

## 2. Minimal working example

```yaml
version: "1.1"

ssh:
  servers:
    prod-web-01:
      host: prod-web-01.internal
      username: deploy
      key_file: ~/.ssh/prod_ed25519

docker:
  hosts:
    local:
      type: local
      socket: unix:///var/run/docker.sock

kubernetes:
  clusters:
    prod-k8s:
      kubeconfig: ~/.kube/config
      context: prod

llm:
  default_provider: ollama
  providers:
    ollama:
      enabled: true
      model: llama3
      base_url: http://localhost:11434
    openai:
      enabled: true
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
  cost_control:
    daily_budget: 10.0
    monthly_budget: 200.0
    alert_at: 0.8
    prefer_local: true

tooling:
  default_scope: standard   # core | standard | all | custom list
```

Paste it, run `mcp config list`, and you have a workable starting point.

---

## 3. Provider keys & environment

Orbit follows the Task Master pattern: keep secrets in the environment, reference them from YAML.

| Provider     | Environment variable          | Notes                                |
|--------------|-------------------------------|--------------------------------------|
| OpenAI       | `OPENAI_API_KEY`              | Required for GPT models              |
| Anthropic    | `ANTHROPIC_API_KEY`           | 100K context, Claude family          |
| Perplexity   | `PERPLEXITY_API_KEY`          | Optional search-augmented answers    |
| Google (Gemini)| `GOOGLE_API_KEY`            | Optional multimodal support          |
| Mistral      | `MISTRAL_API_KEY`             | Lightweight reasoning                |
| OpenRouter   | `OPENROUTER_API_KEY`          | Unified access to multiple providers |
| Azure OpenAI | `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT` | Same schema as Task Master |
| Local Ollama | none                          | Use `ollama serve` + `ollama pull`   |

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export ORBIT_TOOLS=standard
```

Tip: keep these exports in `~/.orbit-mcp.env` and `source` the file from your shell profile.

---

## 4. Tool scopes (`ORBIT_TOOLS`)

Copying the best idea from Task Master, Orbit ships three curated groupings plus a custom mode. The environment variable works for both the MCP server and CLI.

| Value      | Included tools                                                                                                  | Use when…                                  |
|------------|------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `core`     | `ssh_execute`, `system_info`, `disk_usage`, `query_logs`                                                         | First-time setup, safest footprint         |
| `standard` | `core` + Docker (`docker_*`) + Kubernetes read-only (`k8s_list_pods`, `k8s_get_pod`, `k8s_logs`)                 | Day-to-day diagnostics                     |
| `all`      | `standard` + Kubernetes mutating ops (`k8s_scale_deployment`, `k8s_restart_deployment`) + future advanced tools | Power users, trusted operators             |
| `ssh,k8s_logs` | Explicit comma list                                                                                          | Tailor exactly what the LLM can call       |

Set the scope once in your shell or Cursor configuration:

```bash
export ORBIT_TOOLS=core
```

Override per run:

```bash
ORBIT_TOOLS=ssh_execute,docker_logs mcp-server --transport stdio
```

---

## 5. Editor integrations

### Cursor / Claude Code / Windsurf

```json
{
  "mcpServers": {
    "orbit-mcp": {
      "command": "mcp-server",
      "args": ["--transport", "stdio"],
      "env": {
        "ORBIT_TOOLS": "standard",
        "ORBIT_CONFIG": "/Users/<you>/.mcp/config.yaml"
      }
    }
  }
}
```

Copy the block, update the config path, and paste it into:

- Cursor: `~/.cursor/mcp.json`
- Claude Code: `~/.claude/mcp.json`
- Windsurf: `~/.windsurf/mcp.json`

> **Ask AI**  
> “Register Orbit-MCP in my Cursor settings with the `core` tool scope and Anthropic API key set.”

### VS Code (Model Context Protocol extension)

```json
{
  "modelcontext.registeredServers": [
    {
      "id": "orbit-mcp",
      "type": "stdio",
      "command": "mcp-server",
      "args": [],
      "env": {
        "ORBIT_TOOLS": "all",
        "ORBIT_CONFIG": "C:\\Users\\you\\.mcp\\config.yaml"
      }
    }
  ]
}
```

---

## 6. CLI parity

Every value in `~/.mcp/config.yaml` is shared by the CLI (`mcp …`) and MCP server. A few handy commands:

```bash
# add infrastructure
mcp config add-ssh prod-web prod-web.internal deploy --key ~/.ssh/prod_ed25519
mcp config add-k8s prod-k8s ~/.kube/config --context prod

# inspect what you have
mcp config list

# change defaults on the fly
mcp config set tooling.default_scope core
mcp config set llm.default_provider anthropic
```

For automation, wrap commands with aliases:

```bash
mcp config add-alias health-check "uptime && free -h && df -h"
mcp ssh exec prod-web-01 health-check
```

---

## 7. Safety guardrails

- Config directory is auto-created with `0700` permissions, file with `0600`
- Orbit never writes API keys directly; use `${ENV_VAR}` placeholders
- Add destructive tools only to custom scopes and pair them with `confirm: true` inside the tool definition (see `src/mcp/mcp_server.py`)
- Rotate SSH keys regularly; keep per-environment keys in `~/.ssh`

---

## 8. Troubleshooting checklist

| Symptom | Fix |
|---------|-----|
| `Server not found` | Run `mcp config list`—is the SSH host spelled correctly? |
| `permission denied (publickey)` | `chmod 600 ~/.ssh/<key>` and verify `username` in config |
| `ConfigParseError` | Validate YAML: `python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('~/.mcp/config.yaml').expanduser().read_text())"` |
| Cursor cannot connect | Ensure `mcp-server` is on `PATH` (`pip install -e .`), restart the editor, confirm `ORBIT_TOOLS` scope |
| Wrong tool scope | Echo `ORBIT_TOOLS` before launching (`echo $ORBIT_TOOLS`) |

---

## 9. Next steps

- Continue to the [Quick Start guide](./quick-start.md) for installation flows
- Explore the [MCP tool catalog](./mcp-tools.md) to decide which scope fits your team
- Review [Best Practices](./best-practices.md) for auth layouts, dry-run patterns, and audit logging

Once your configuration is in place, you can bounce seamlessly between the CLI, the MCP server inside Cursor, and the autonomous AI agent—backed by a single source of truth.
