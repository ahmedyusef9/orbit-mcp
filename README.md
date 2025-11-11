<a name="readme-top"></a>

<div align="center">
  <a href="https://modelcontextprotocol.io/" target="_blank"><img src="https://img.shields.io/badge/MCP-Compatible-0A84FF.svg?style=for-the-badge" alt="MCP Compatible"></a>
  <img src="https://img.shields.io/badge/version-0.1.0-blue.svg?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="docs/quick-start.md"><img src="https://img.shields.io/badge/docs-quick%20start-6C63FF.svg?style=for-the-badge" alt="Quick start docs"></a>
</div>

<p align="center">
  <strong>Orbit-MCP</strong>: AI-assisted DevOps control plane that brings SSH, Kubernetes, Docker, and observability tooling to any AI chat or terminal workflow.
</p>

<p align="center">
  <a href="docs/quick-start.md">Quick Start</a> ·
  <a href="docs/mcp-tools.md">Tool Catalog</a> ·
  <a href="docs/cli-reference.md">CLI Reference</a> ·
  <a href="docs/best-practices.md">Best Practices</a>
</p>

---

## Built by the Orbit-MCP Team

Orbit-MCP unifies the CLI, an interactive AI agent, and the Model Context Protocol (MCP) server into a single DevOps platform. You can issue natural-language requests inside Cursor, Windsurf, VS Code, Claude Code, or the terminal and Orbit will execute the correct SSH, Kubernetes, Docker, or log commands—while respecting guardrails and confirmation prompts.

---

## Why Python?

Orbit-MCP ships as a Python package because the platform leans heavily on battle-tested Python SDKs for SSH (Paramiko), Docker, Kubernetes, and structured CLI tooling. The reference project you linked (`claude-task-master`) focuses on distributing an npm package for JavaScript runtimes; Orbit-MCP, by contrast, embeds privileged infrastructure integrations and long-running services that are easier to harden, test, and package in Python.

---

## Documentation

📚 **[Read the full docs](docs/README.md)** for architecture, walkthroughs, and playbooks.

### Quick Reference

- [Quick Start](docs/quick-start.md) – cloned install + first run checklist
- [Configuration Guide](docs/configuration.md) – infrastructure profiles, authentication, LLM routing
- [CLI Reference](docs/cli-reference.md) – every `mcp` subcommand
- [Tool Catalog](docs/mcp-tools.md) – MCP scopes, schemas, and safety tips
- [Autopilot Playbooks](docs/autopilot.md) – incident and runbook examples
- [Best Practices](docs/best-practices.md) – budgeting, safety rails, audit patterns
- [Product Requirements](docs/product-requirements.md) – roadmap and north-star features

#### Quick Install for Cursor 1.0+ (One-Click)

[![Add Orbit-MCP MCP server to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=orbit-mcp&config=eyJjb21tYW5kIjogIm1jcC1zZXJ2ZXIiLCAiYXJncyI6IFsiLS10cmFuc3BvcnQiLCAic3RkaW8iXSwgImVudiI6IHsiT1JCSVRfVE9PTFMiOiAic3RhbmRhcmQiLCAiT1JCSVRfQ09ORklHIjogIn4vLm1jcC9jb25maWcueWFtbCIsICJPUEVOQUlfQVBJX0tFWSI6ICJZT1VSX09QRU5BSV9BUElfS0VZX0hFUkUiLCAiQU5USFJPUElDX0FQSV9LRVkiOiAiWU9VUl9BTlRIUk9QSUNfQVBJX0tFWV9IRVJFIiwgIkdPT0dMRV9BUElfS0VZIjogIllPVVJfR09PR0xFX0FQSV9LRVlfSEVSRSIsICJNSVNUUkFMX0FQSV9LRVkiOiAiWU9VUl9NSVNUUkFMX0FQSV9LRVlfSEVSRSIsICJHUk9RX0FQSV9LRVkiOiAiWU9VUl9HUk9RX0FQSV9LRVlfSEVSRSIsICJQRVJQTEVYSVRZX0FQSV9LRVkiOiAiWU9VUl9QRVJQTEVYSVRZX0FQSV9LRVlfSEVSRSJ9fQ==)

> After installing, edit `~/.cursor/mcp.json` (or the project-scoped config) to replace placeholder API keys. Restart the editor if Orbit appears with zero tools enabled.

#### Claude Code Quick Install

```bash
claude mcp add orbit-mcp --scope user \
  --env ORBIT_TOOLS="standard" \
  -- mcp-server --transport stdio
```

Add any provider keys you plan to use:

- in your shell profile or `.env`
- in the `env` section of the Claude MCP record (`ORBIT_TOOLS`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)

---

## Requirements

- Python 3.10+ (3.11 recommended)
- `pip` or `pipx`, plus optional dependencies you want Orbit to manage (`ssh`, Docker CLI, `kubectl`)
- At least one LLM provider credential (Anthropic, OpenAI, Google, Mistral, Groq, Perplexity, etc.) **or** a local provider such as Ollama

Orbit can route prompts through different models for planning, research, and fallback. Define credentials in `~/.mcp/config.yaml`, environment variables, or editor-specific MCP config.

---

## Installation

Orbit-MCP is published as the `mcp-server` Python package.

```bash
# Recommended: isolated install with pipx
pipx install mcp-server

# or install into an activated virtual environment
pip install mcp-server
```

Working from a clone? The editable install keeps source and runtime in sync:

```bash
git clone https://github.com/<your-org>/orbit-mcp.git
cd orbit-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

After installing, confirm the entry points:

```bash
mcp --help
mcp-server --help
```

If those commands are not on your `PATH`, make sure `~/.local/bin` (or your pipx bin directory) is exported.

---

## Configuration

Orbit looks for a config file at `~/.mcp/config.yaml` by default. Generate or copy one of the following:

```bash
# Guided setup
mcp config init

# Or start from the example bundled with the repo
cp config.example.yaml ~/.mcp/config.yaml
```

Populate the file with the SSH servers, Kubernetes clusters, and Docker hosts you want Orbit to manage, then add any LLM credentials (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) as environment variables or directly under the `llm.providers` section. See [docs/configuration.md](docs/configuration.md) for every field.

---

## Quick Start

### Option 1: MCP (Recommended)

1. **Add the MCP config**  
   Choose the scope path for your editor:

   | Editor       | Scope   | Linux/macOS Path                      | Windows Path                                      | Key          |
   | ------------ | ------- | ------------------------------------- | ------------------------------------------------- | ------------ |
   | **Cursor**   | Global  | `~/.cursor/mcp.json`                  | `%USERPROFILE%\.cursor\mcp.json`                  | `mcpServers` |
   |              | Project | `<project>/.cursor/mcp.json`          | `<project>\.cursor\mcp.json`                      | `mcpServers` |
   | **Windsurf** | Global  | `~/.codeium/windsurf/mcp_config.json` | `%USERPROFILE%\.codeium\windsurf\mcp_config.json` | `mcpServers` |
   | **VS Code**  | Project | `<project>/.vscode/mcp.json`          | `<project>\.vscode\mcp.json`                      | `servers`    |
   | **Claude CLI** | User | `~/.anthropic/claude/mcp.json`         | –                                                 | `mcpServers` |

2. **Manual configuration**  
   Start with the snippet below (also available in `examples/cursor-mcp-config.json`):

   ```json
   {
     "mcpServers": {
       "orbit-mcp": {
         "command": "mcp-server",
         "args": ["--transport", "stdio"],
         "env": {
           "ORBIT_TOOLS": "standard",
           "ORBIT_CONFIG": "~/.mcp/config.yaml",
           "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY_HERE",
           "ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY_HERE",
           "GOOGLE_API_KEY": "YOUR_GOOGLE_API_KEY_HERE",
           "MISTRAL_API_KEY": "YOUR_MISTRAL_API_KEY_HERE",
           "GROQ_API_KEY": "YOUR_GROQ_API_KEY_HERE",
           "PERPLEXITY_API_KEY": "YOUR_PERPLEXITY_API_KEY_HERE"
         }
       }
     }
   }
   ```

   For VS Code MCP (JSON-RPC transport), add `"type": "stdio"` within the server definition.

3. **Enable Orbit in your editor**  
   - Cursor: open Settings → MCP → toggle on `orbit-mcp` and approve the tool list.  
   - Windsurf/Claude: follow the prompt to grant trust.  
   - VS Code: reload the window after saving `mcp.json`.

4. **Pick models (optional)**  
   In your AI chat pane you can ask, for example:  
   `Change the main and fallback models to claude-3-5-sonnet and gpt-4o-mini.`  
   Orbit respects whatever `default_provider` and overrides you configure.

5. **Initialize your infrastructure profiles**  
   - Copy `config.example.yaml` to `~/.mcp/config.yaml`.  
   - Run `mcp config init` for a guided setup.  
   - Add SSH, Kubernetes, and Docker entries as needed.

6. **First-run checklist**  
   ```bash
   mcp config list
   ORBIT_TOOLS=standard mcp-server --transport stdio   # optional manual launch
   mcp ai ask "Summarize production pod health"
   mcp ssh exec prod-web "uptime && df -h"
   mcp docker ps
   ```

### Option 2: Command Line

```bash
# Clone the repo
git clone https://github.com/<your-org>/orbit-mcp.git
cd orbit-mcp

# Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Install Orbit locally (editable)
pip install -e .

# Configure
mcp config init
```

Common CLI patterns:

```bash
mcp ssh exec prod-web "systemctl status nginx"
mcp docker logs api --tail 100
mcp k8s pods -n production
mcp ai ask "Diagnose 500 errors in staging"
```

---

## Tool Loading Configuration

Orbit ships with 3 curated scopes for the MCP tool registry. Adjust `ORBIT_TOOLS` to balance context size and permissions.

| Mode        | Tools (summary)                                                                                          | Context (~tokens) | Typical use case                    |
|-------------|-----------------------------------------------------------------------------------------------------------|-------------------|-------------------------------------|
| `core`      | `ssh_execute`, `query_logs`, `system_info`, `disk_usage`                                                  | ~5K               | Read-only triage and health checks |
| `standard`  | `core` + Docker/Kubernetes read operations (`docker_list_containers`, `docker_logs`, `k8s_list_pods`, …)  | ~10K              | Daily SRE workflows                |
| `all`       | `standard` + mutating tools (`docker_start/stop/restart`, `k8s_scale_deployment`, `k8s_restart_deployment`) | ~21K              | Runbooks and trusted operators     |
| custom list | Comma-separated subset (`ssh_execute,k8s_logs,docker_logs`)                                               | Variable          | Fine-grained project configs       |

Set globally (`export ORBIT_TOOLS=standard`) or per invocation (`ORBIT_TOOLS=core mcp-server --transport stdio`).

---

## Claude Code Support

- Works with `claude-code/sonnet` and `claude-code/opus`
- Requires the Claude Code CLI; no API key needed if you stay inside the local Claude sandbox
- Combine with other providers by defining `default_provider` in `~/.mcp/config.yaml`

A hands-on flow for Claude Code lives in the MCP section of [docs/quick-start.md](docs/quick-start.md).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `mcp-server: command not found` | Activate the virtual environment or install with `pipx install mcp-server`. |
| Cursor lists `orbit-mcp` with 0 tools | Ensure `ORBIT_TOOLS` is set and restart the editor after editing `mcp.json`. |
| SSH tool fails | Verify `ssh <host>` works manually and your key has `chmod 600`. |
| Kubernetes tool errors | Confirm `kubectl get pods` works with the same kubeconfig/context. |
| Editor disconnects mid-session | Relaunch `mcp-server --transport stdio` or reload the MCP integration panel. |

More scenarios and fixes live in [docs/best-practices.md](docs/best-practices.md) and [docs/autopilot.md](docs/autopilot.md).

---

## Orbit-MCP Highlights

- **Unified control plane** – call the same secure tooling from MCP-aware editors or the terminal.
- **AI-first workflow** – plan/execute/reflect loop that explains diagnostics in plain language.
- **Multi-provider routing** – Anthropic, OpenAI, Google, Groq, Mistral, Perplexity, Ollama, and more.
- **Safety guardrails** – confirmation prompts, tool scopes, command allowlists, redact-before-send pipeline.
- **Cost management** – daily/monthly budgets, provider fallbacks, usage tracking via `mcp ai usage`.
- **Runbook ready** – use Autopilot playbooks or craft your own PRDs for repeatable incident response.

---

## Contributing

We welcome issues, ideas, and pull requests! Start with [CONTRIBUTING.md](CONTRIBUTING.md) and open a discussion if you plan a large feature or integration.

---

## Licensing

Orbit-MCP is distributed under the [MIT License](LICENSE). Use it in personal, commercial, or academic environments—just keep attribution and stay within the guardrails of your infrastructure policies.

---

Looking for the fastest way back to the top? [Back to top ⬆️](#readme-top)
