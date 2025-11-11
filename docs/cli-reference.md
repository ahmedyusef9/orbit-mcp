# Orbit-MCP CLI Reference

Orbit’s CLI mirrors the same capabilities exposed through the MCP server. Use this guide as a command cheat sheet—every block is runnable and safe to paste into Mintlify or a README.

> **Ask AI**  
> “Generate the CLI commands to check disk usage on `prod-web-01`, tail Redis logs, and scale the `api` deployment to 4 replicas.”

---

## 1. Global commands

```bash
mcp --help                # show top-level help
mcp --version             # confirm binary version
mcp --config ./orbit.yaml # target an alternate config file

mcp config list           # audit current SSH, Docker, K8s, and aliases
mcp config init           # generate ~/.mcp/config.yaml
```

---

## 2. Managing configuration from the CLI

```bash
# add infrastructure
mcp config add-ssh prod-web prod-web.internal deploy --key ~/.ssh/prod_ed25519
mcp config add-docker remote-docker docker.internal --ssh-server prod-web
mcp config add-k8s prod-k8s ~/.kube/config --context prod

# tweak defaults
mcp config set tooling.default_scope standard
mcp config set llm.default_provider anthropic

# create convenient aliases
mcp config add-alias health-check "uptime && free -h && df -h"
mcp config add-alias restart-api "systemctl restart api && journalctl -u api -n 50"
```

Use `mcp config remove-ssh`, `remove-docker`, or `remove-k8s` to clean things up.

---

## 3. SSH toolkit

```bash
# execute commands
mcp ssh exec prod-web "uptime && free -h && df -h"
mcp ssh exec prod-web health-check         # alias example
mcp ssh exec prod-web "journalctl -u nginx -n 100"

# list available SSH profiles
mcp ssh list

# tail and follow logs
mcp ssh logs prod-web /var/log/nginx/error.log -n 100
mcp ssh logs prod-web /var/log/nginx/access.log -f

# transfer files (if enabled in config)
mcp ssh download prod-web /var/log/nginx/error.log ./downloads/error.log
mcp ssh upload prod-web ./manifests/app.yaml /tmp/app.yaml
```

> **Ask AI**  
> “Use Orbit CLI commands to capture system health stats from `prod-web` and save them in `/tmp/orbit-health.txt`.”

---

## 4. Docker commands

```bash
# inspect running containers
mcp docker ps
mcp docker ps --all

# view logs
mcp docker logs api-container -n 200
mcp docker logs api-container -f

# lifecycle controls (requires ORBIT_TOOLS=all)
mcp docker start api-container
mcp docker stop api-container
mcp docker restart api-container
```

Combine with SSH to run native Docker CLI commands when you need unusual options:

```bash
mcp ssh exec prod-web "docker stats --no-stream api-container"
```

---

## 5. Kubernetes commands

```bash
# contexts and namespaces
mcp k8s contexts
mcp k8s use prod-k8s

# pod diagnostics
mcp k8s pods -n production
mcp k8s pods -n production --selector app=api
mcp k8s logs api-7d9f8 -n production
mcp k8s logs api-7d9f8 -c sidecar -n production -n 200

# deep dive
mcp k8s describe api-7d9f8 -n production
mcp k8s events -n production --tail 20

# mutating commands (ORBIT_TOOLS=all)
mcp k8s scale api-deployment 4 -n production
mcp k8s restart api-deployment -n production
mcp k8s exec api-7d9f8 -n production -- "printenv"
```

If you prefer direct kubectl commands, route through SSH:

```bash
mcp ssh exec prod-web "kubectl rollout status deployment/api -n production"
```

---

## 6. AI agent & autopilot

```bash
# one-shot questions
mcp ai ask "List pods restarting in production"
mcp ai ask "Why is nginx showing 502 errors?" --provider anthropic
mcp ai ask "Summarise /var/log/nginx/error.log" --format json

# interactive REPL
mcp ai chat
# inside chat:
#   /help, /status, /model claude-3-sonnet, /reset, /exit

# cost and provider visibility
mcp ai usage
mcp ai models
```

Pair CLI commands with “Ask AI” prompts to create repeatable runbooks:

> “Tail the last 300 lines of `api-container` logs and summarise the top errors.”

---

## 7. Long-running or repeatable tasks

```bash
# example bash loop to monitor disk usage
#!/usr/bin/env bash
while true; do
  ts=$(date +"%Y-%m-%d %H:%M:%S")
  usage=$(mcp ssh exec prod-web "df -h / | awk 'NR==2 {print \$5}'")
  echo "$ts $usage" | tee -a /tmp/orbit-disk.log
  sleep 300
done
```

Use cron, CI pipelines, or GitHub Actions to schedule CLI runs—for example, scaling a deployment after a release or gathering diagnostics before opening an incident.

---

## 8. Troubleshooting CLI issues

| Problem | Resolution |
|---------|------------|
| `mcp: command not found` | Ensure the virtualenv is active or reinstall with `pip install -e .`. |
| SSH commands hang | Check firewall rules, confirm host and username in config, or increase `timeout`. |
| Docker/K8s commands fail | Verify the host has Docker/kubectl installed; test with raw SSH commands. |
| AI commands say “provider not configured” | Export the relevant API key and confirm `llm.providers.<name>.enabled` is `true`. |

For a higher-level narrative, continue to the [Autopilot Playbooks](./autopilot.md); for editorial integration and scopes, revisit the [Tool Catalog](./mcp-tools.md).
