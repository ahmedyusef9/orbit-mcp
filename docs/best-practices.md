# Orbit-MCP Best Practices

This guide distills what worked well in Task Master’s production rollout—reframed for Orbit-MCP’s Python stack. Use it when onboarding teams, writing Mintlify pages, or double-checking an environment before you hand the keys to an AI assistant.

---

## 1. Authentication & secrets

- **Prefer SSH keys over passwords**  
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/orbit_prod
  mcp config add-ssh prod-web prod-web.internal deploy --key ~/.ssh/orbit_prod
  chmod 600 ~/.ssh/orbit_prod
  ```

- **Separate credentials by environment** (`~/.ssh/orbit_dev`, `orbit_stage`, `orbit_prod`) and map them to distinct config files (`~/.mcp/config.dev.yaml` etc.).

- **Keep secrets in env vars** (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `ORBIT_CONFIG`) and reference them in YAML as `${VAR}`. Never hard-code keys.

- **Audit regularly**  
  ```bash
  find ~/.mcp -maxdepth 1 -type f -name "config*.yaml" -exec ls -l {} \;
  ```

---

## 2. Tool scope hygiene

- Default to `ORBIT_TOOLS=core` in production and elevate to `standard`/`all` only when necessary.
- Limit high-impact tools (e.g., scaling deployments) to custom scopes and pair them with homegrown confirmation prompts (`prompt: "Type SCALE to continue"` stored in your docs).
- Before adding a destructuve tool, create a matching runbook & “Ask AI” snippet so human operators understand the blast radius.

---

## 3. Safety rails

- **Alias destructive commands** so they are single-purpose and auditable:

  ```bash
  mcp config add-alias restart-nginx "sudo systemctl restart nginx && journalctl -u nginx -n 50"
  ```

- **Log everything**: run Orbit from a tmux session with `mcp-server 2>&1 | tee -a ~/.mcp/orbit.log`.
- **Confirm before mutating**: Orbit already prompts inside the MCP flow; mirror that in the CLI by using shell `read -p` wrappers if you automate things further.

---

## 4. Cost control & provider strategy

- Start with `ollama` + `gpt-4o-mini` (cheap, fast) and set `daily_budget` low (e.g., `$5`) while you learn usage patterns.
- Encourage engineers to run `mcp ai usage` at the end of a session; surface the numbers in Slack if you run Orbit on a shared bastion.
- Document when to reach for premium models (e.g., long Kubernetes events) and when to stay with local inference.

---

## 5. Observability patterns

- Pipe Orbit outputs into your incident timeline (Slack thread, Ticket comments) so decisions are traceable.
- Collect baseline metrics with a nightly job: `mcp ssh exec ... "uptime && df -h && free -h"` and store in object storage for comparisons.
- Use `query_logs` with tailored filters to avoid dumping entire files to the LLM; it keeps token usage (and costs) predictable.

---

## 6. Testing & staging

- Maintain a staging configuration (`~/.mcp/config.staging.yaml`) that mirrors production infrastructure names with a suffix. Use it to rehearse playbooks.
- Run unit tests (`pytest tests/`) after adding new tools or config logic to ensure schema/handler drift is caught early.
- For new tool scopes, create a quick contract test in `tests/test_transport.py` so `tools/list` stays in sync with docs.

---

## 7. Documentation workflow

- When you add or modify tools, update:
  1. `configuration.md` scope table  
  2. `mcp-tools.md` schema section  
  3. `cli-reference.md` (if there’s a matching CLI command)  
  4. Any playbooks that rely on the tool  

- Each doc includes “Ask AI” prompts—use them liberally to keep the human + AI hand-off smooth.

- Track doc changes in the changelog so operators know what moved between releases.

---

## 8. Incident-ready checklist

| Item | Status |
|------|--------|
| `ORBIT_TOOLS` set to the correct scope | ☐ |
| SSH keys rotated within last 90 days | ☐ |
| `mcp ai usage` budgets configured | ☐ |
| Autopilot playbooks tested in staging | ☐ |
| Docs published to Mintlify / handbook | ☐ |

Export this table into your on-call runbook so engineers can do a 60-second readiness check.

---

## 9. Advanced ideas

- Integrate with Vault or AWS Secrets Manager for dynamic credential retrieval (planned in Orbit’s roadmap—watch `docs/configuration.md` for updates).
- Build a `diagnostic_report` composite tool that stitches results from `ssh_execute`, `k8s_logs`, and cost metrics into one JSON payload. Document it alongside scope changes.
- Stream Orbit transcripts into an observability system to build searchable incident retrospectives.

---

Adopting these patterns keeps Orbit approachable for newcomers, safe in production, and aligned with the high-quality documentation cadence established by Task Master.
