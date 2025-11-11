# Orbit-MCP Tool Catalog

Orbit-MCP exposes the same DevOps toolkit to editors (via MCP) and the CLI. Inspired by Task Master, tools are grouped into curated scopes (`core`, `standard`, `all`) so you can balance safety with capability. Toggle the scope through the `ORBIT_TOOLS` environment variable or per-session overrides.

> **Ask AI**  
> “Which Orbit tool scope should I use for read-only production troubleshooting?”

---

## 1. Tool scopes at a glance

| Scope      | Included tools                                                                                                                  | Default | Recommended for |
|------------|----------------------------------------------------------------------------------------------------------------------------------|---------|------------------|
| `core`     | `ssh_execute`, `query_logs`, `system_info`, `disk_usage`                                                                         | ✅       | First install, low-risk operations |
| `standard` | All `core` tools + Docker read (`docker_list_containers`, `docker_logs`) + Kubernetes read (`k8s_list_pods`, `k8s_get_pod`, `k8s_logs`) |         | Daily diagnostics, SRE triage |
| `all`      | `standard` scope + mutating tools (`docker_start_container`, `docker_stop_container`, `docker_restart_container`, `k8s_scale_deployment`, `k8s_restart_deployment`) |         | Trusted operators, runbooks |
| Custom     | Comma-separated list (`ssh_execute,k8s_logs,docker_logs`)                                                                        |         | Fine-grained control per project |

```bash
# global scope (shell profile, CI job, etc.)
export ORBIT_TOOLS=standard

# single run override
ORBIT_TOOLS=core mcp-server --transport stdio
```

---

## 2. Tool reference (JSON Schema style)

Each table summarises the JSON schema registered with the MCP server (see `src/mcp/mcp_server.py`). All tools return rich text plus structured JSON so Cursor, Claude Code, or your automation can post-process responses.

### 2.1 Core scope

| Tool | Description | Input (type → description) | Output |
|------|-------------|----------------------------|--------|
| `ssh_execute` | Run shell commands on configured SSH hosts. Includes stdout, stderr, exit code. | `server:string` → SSH profile name<br>`command:string` → shell command<br>`timeout?:integer` (seconds, default `30`) | `{ stdout, stderr, exit_code }` |
| `query_logs` | Tail and optionally filter logs on remote hosts. | `server:string`<br>`log_path:string`<br>`filter?:string` (grep expression)<br>`tail?:integer` (default `100`)<br>`follow?:boolean` (streaming not yet supported) | Text block with last `N` lines matching filter |
| `system_info` | Collects uptime, load averages, CPU/memory, and basic health checks from a host. | `server:string` | Markdown summary + structured metrics |
| `disk_usage` | Runs disk usage diagnostics (`df -h`) on a host. | `server:string` | Markdown summary of mounted volumes |

### 2.2 Standard scope extensions

| Tool | Description | Input | Notes |
|------|-------------|-------|-------|
| `docker_list_containers` | Lists containers with status, image, and IDs. | `all?:boolean` (show stopped containers) | Great for context-aware prompts |
| `docker_logs` | Retrieves container logs (tail only). | `container:string`<br>`tail?:integer` (default `100`)<br>`follow?:boolean` (streaming not yet supported) | Combine with AI summarisation |
| `k8s_list_pods` | Lists pods within a namespace. | `namespace?:string` (default `default`)<br>`cluster?:string` (loads kubeconfig + optional context) | Requires kubeconfig entry |
| `k8s_get_pod` | Returns detailed pod status (conditions, containers). | `name:string`<br>`namespace?:string` | |
| `k8s_logs` | Fetches logs from a pod (optionally container-specific). | `pod:string`<br>`namespace?:string`<br>`container?:string`<br>`tail?:integer`<br>`follow?:boolean` | Use `tail` to cap token usage |

### 2.3 All scope additions (mutating + lifecycle)

| Tool | Description | Input | Safety tips |
|------|-------------|-------|-------------|
| `docker_start_container` | Start a container by name/ID. | `container:string` | Pair with a confirmation prompt in your editor |
| `docker_stop_container` | Stop a container, optional timeout. | `container:string`<br>`timeout?:integer` (default `10`) | Use `ORBIT_TOOLS=standard` in production unless necessary |
| `docker_restart_container` | Restart container (stop + start). | `container:string` | |
| `k8s_scale_deployment` | Adjust replica count for a deployment. | `deployment:string`<br>`replicas:integer`<br>`namespace?:string` | Commonly wrapped in runbooks |
| `k8s_restart_deployment` | Force a rollout restart. | `deployment:string`<br>`namespace?:string` | |

---

## 3. Example: scoped MCP config

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

Pair the scope with curated prompts inside your docs or Mintlify site:

> **Ask AI**  
> “Using Orbit-MCP (`standard` tools), list pods in the `production` namespace and summarise the restart counts.”

---

## 4. Adding new tools

1. Implement the tool in `src/mcp/mcp_server.py` (JSON schema + handler).  
2. Categorise it: add the tool name to the correct scope in `configuration.md`.  
3. Document schema, parameters, and safety notes here.  
4. Consider adding a CLI wrapper in `mcp/cli.py` for parity if applicable.  
5. Update tests in `tests/test_transport.py` or relevant suite.

Following this loop keeps docs, code, and scopes aligned—making it easy for editors like Cursor, Claude Code, and Windsurf to expose the right capabilities without overwhelming the language model.
