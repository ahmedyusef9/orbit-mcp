# Orbit-MCP Quick Start

Spin up Orbit-MCP in minutes. This guide sticks to a **single install path** (the bundled script) and then shows how to wire Orbit into Cursor so you can start calling tools immediately.

---

## 1. Requirements

- Python 3.10+ (3.11 recommended)
- `pip` and `virtualenv` access
- Optional: Docker CLI, `kubectl`, and `ssh` for local validation
- At least one LLM provider key (or Ollama for local inference)

> **Ask AI**  
> “Verify I have Python 3.11, Docker, and kubectl installed before setting up Orbit-MCP.”

---

## 2. Single-command installation

```bash
git clone https://github.com/<org>/orbit-mcp.git
cd orbit-mcp
chmod +x install.sh
./install.sh
```

What the script does:

- Verifies Python 3.10+ and offers to create a virtual environment.
- Installs all dependencies and Orbit-MCP (`pip install -e .`).
- Optionally runs `mcp config init` so you start with a config file.
- Confirms the `mcp` CLI is on your `PATH`.

> **Ask AI**  
> “Run the Orbit installer and confirm the `mcp` command is available.”

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

## 4. Add Orbit-MCP to Cursor

1. Ensure `mcp-server` is available (`which mcp-server`).  
2. Edit `~/.cursor/mcp.json` (create it if it doesn’t exist) and add:

```json
{
  "mcpServers": {
    "orbit-mcp": {
      "command": "mcp-server",
      "args": ["--transport", "stdio"],
      "env": {
        "ORBIT_TOOLS": "standard",
        "ORBIT_CONFIG": "/Users/<you>/.mcp/config.yaml",
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

3. Restart Cursor (or use the MCP reload command) and approve the Orbit-MCP connection when prompted.
4. In the editor chat, try:  
   > “Use Orbit-MCP to tail the last 50 lines of nginx error logs on `prod-web`.”

> **Ask AI**  
> “Define Orbit-MCP in Cursor using `~/.cursor/mcp.json` and enable the `standard` tool scope.”

---

## 5. First run checklist

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

Whether you’re in the terminal or Cursor, the following commands verify everything end-to-end:

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
