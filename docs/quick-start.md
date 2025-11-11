# Orbit-MCP Quick Start

Spin up Orbit-MCP in minutes—the flow mirrors Task Master’s “Requirements → Installation → Configuration → First Command” cadence so you can paste it into Mintlify or share as-is.

---

## 1. Requirements

- Python 3.10+ (3.11 recommended)
- `pip` and `virtualenv` access
- Optional: Docker CLI, `kubectl`, and `ssh` for local validation
- At least one LLM provider key (or Ollama for local inference)

> **Ask AI**  
> “Verify I have Python 3.11, Docker, and kubectl installed before setting up Orbit-MCP.”

---

## 2. Installation paths

### Option A — One-click Cursor deeplink

Use the same pattern as Task Master: ship a Cursor URL that installs the MCP server with placeholder keys. Adjust the repo URL and environment before sharing.

```
cursor://mcp/install?name=orbit-mcp&command=mcp-server&transport=stdio&env[ORBIT_TOOLS]=standard
```

After the deeplink, open `~/.cursor/mcp.json` to replace placeholder API keys.

### Option B — Manual MCP registration

Update `~/.cursor/mcp.json` (Cursor), `~/.claude/mcp.json` (Claude Code), or `~/.windsurf/mcp.json` (Windsurf):

```json
{
  "mcpServers": {
    "orbit-mcp": {
      "command": "mcp-server",
      "args": ["--transport", "stdio"],
      "env": {
        "ORBIT_TOOLS": "core",
        "ORBIT_CONFIG": "/Users/<you>/.mcp/config.yaml"
      }
    }
  }
}
```

Restart the editor and approve the connection when prompted.

### Option C — CLI install

```bash
# clone & enter
git clone https://github.com/<org>/orbit-mcp.git
cd orbit-mcp

# create virtualenv (recommended)
python3 -m venv .venv
source .venv/bin/activate

# install dependencies + console scripts
pip install -r requirements.txt
pip install -e .

# smoke test
mcp --help
mcp-server --help
```

---

## 3. Configure Orbit

1. Generate the base file:
   ```bash
   mcp config init
   ```
2. Add infrastructure:
   ```bash
   mcp config add-ssh prod-web prod-web.internal deploy --key ~/.ssh/prod_ed25519
   mcp config add-k8s prod-k8s ~/.kube/config --context prod
   ```
3. Export provider keys (choose whichever apply):
   ```bash
   export OPENAI_API_KEY=sk-...
   export ANTHROPIC_API_KEY=sk-ant-...
   export ORBIT_TOOLS=standard   # core | standard | all | custom list
   ```
4. Review the schema and scope options in [configuration.md](./configuration.md).

> **Ask AI**  
> “Fill in my Orbit configuration with prod + staging SSH hosts and enable Ollama as the default provider.”

---

## 4. First run checklist

```bash
# 1. Validate configuration
mcp config list

# 2. Start MCP server for your editor
ORBIT_TOOLS=standard mcp-server --transport stdio

# 3. Or kick the tires via CLI
mcp ssh exec prod-web "uptime && free -h"
mcp docker ps
mcp k8s pods -n production
```

Now open Cursor/Claude Code and try:

> “Use Orbit-MCP to tail the last 50 lines of nginx error logs on `prod-web`.”

Approve the tool call and review the result in the chat.

---

## 5. Common next steps

- `mcp ai ask "List pods in production"` — exercise the AI agent loop.
- `mcp ai chat` — start an interactive REPL with plan/execute/reflect.
- `mcp docker logs <container> -n 100` — validate Docker connectivity.
- `mcp k8s scale my-deployment 5 -n production` — test mutating ops (only if `ORBIT_TOOLS=all`).

Wrap up by reading:

- [MCP Tools catalog](./mcp-tools.md) — know exactly what the LLM can call.
- [CLI Reference](./cli-reference.md) — command-by-command cheat sheet.
- [Best Practices](./best-practices.md) — safety rails, budgeting, and audit tips.

---

## 6. Troubleshooting quick hits

| Issue | Fix |
|-------|-----|
| `mcp-server: command not found` | Make sure the virtualenv is activated or add `~/.local/bin` to `PATH`. |
| Cursor can’t connect | Restart Cursor, ensure `mcp-server` is running, confirm `ORBIT_TOOLS` scope. |
| SSH authentication fails | Run `ssh prod-web` manually; check key permissions (`chmod 600 ~/.ssh/<key>`). |
| Kubernetes tool errors | Verify `kubectl get pods` works with the same kubeconfig/context. |

If the basics work, head to the [Autopilot Playbooks](./autopilot.md) to see Orbit handle full incident runs.
