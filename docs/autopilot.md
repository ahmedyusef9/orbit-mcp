# Orbit-MCP Autopilot Playbooks

These playbooks show how Orbit’s plan → execute → reflect loop behaves in real incidents. Adapt them into Mintlify “Guides” or provide them as ready-to-run prompts alongside your runbooks. Each story calls out the expected tool usage, safety checks, and cost considerations.

---

## 1. Diagnose a crashing Kubernetes pod

**Prompt**

> “Diagnose why the `checkout` service is stuck in CrashLoopBackOff in production.”

**Expected plan**

1. `k8s_list_pods` (scope: `standard`) to confirm CrashLoopBackOff status.  
2. `k8s_logs` for the failing pod (tail 200 lines).  
3. `query_logs` or `ssh_execute` to check upstream dependencies if needed.  
4. Summarise root cause, propose remediation, ask for confirmation before any mutating step.

**Sample execution transcript**

```
?  Step 1: Listing pods in namespace production…
   checkout-7d9f8      CrashLoopBackOff (13 restarts)  node ip-10-0-2-14

?  Step 2: Fetching last 200 log lines from checkout-7d9f8…
   - Fatal error: cannot connect to redis://redis.internal:6379 (ECONNREFUSED)
   - Retried 5 times with exponential backoff

?  Analysis:
   Root cause: checkout cannot connect to Redis.
   Likely cascading failure: Redis exhausted memory.

?  Recommendation:
   1. Inspect Redis pod logs.
   2. Increase memory limit or flush cache.
   3. Restart checkout after Redis recovers.

?  Next options:
   - “Check Redis pod logs”
   - “Increase Redis memory to 2Gi” (requires confirmation)
```

**Safety**

- Because scope is `standard`, Orbit proposes but does not execute mutations.  
- If the user replies “Scale checkout to 3 replicas”, Orbit asks for confirmation and reminds the user `ORBIT_TOOLS` must be `all`.

**Cost note**

- 200 log lines typically stay under 3K tokens; the agent will stick with `ollama` or `gpt-4o-mini` unless the context balloons.

---

## 2. Restore capacity after disk pressure

**Prompt**

> “Fix disk pressure on `prod-web-01` and show me how much space we reclaimed.”

**Expected plan**

1. `system_info` to confirm disk pressure event.  
2. `disk_usage` to list largest partitions.  
3. `query_logs` against `/var/log` to find heavy offenders.  
4. If asked, `ssh_execute` to run clean-up commands (always with confirmation).  
5. Re-run `disk_usage` to compare before vs after.

**Suggested tool call sequence**

```
1. system_info(server="prod-web-01")
2. disk_usage(server="prod-web-01")
3. query_logs(server="prod-web-01", log_path="/var/log", tail=200, filter="WARN|ERROR")
4. ssh_execute(server="prod-web-01", command="sudo journalctl --vacuum-time=7days")  # confirmation required
5. disk_usage(server="prod-web-01")
```

**Narrative snippet**

```
Before cleanup:
  /var/log -> 82% (42G / 50G)

Cleanup action pending:
  sudo journalctl --vacuum-time=7days
  This will remove logs older than 7 days.
  Proceed? (yes/no)

After cleanup:
  /var/log -> 37% (18G / 50G)
  Reclaimed ~24G.
```

**Automation tip**

Turn the flow into a reusable “Ask AI” snippet inside your docs:

> “Diagnose disk pressure on `prod-web-01`, propose a safe cleanup command, execute it after I confirm, and report the space recovered.”

---

## 3. Expand a PRD into executable tasks

Even without the full Task Master project, Orbit can ingest PRD text (via copy/paste or file prompt) and generate actionable tasks using MCP tools for validation.

**Prompt**

> “Here’s the Payment Service PRD (paste). Break it into tasks, run `mcp ai ask` to validate prerequisite infrastructure, and output a checklist grouped by milestone.”

**Plan outline**

1. Parse PRD using the LLM.  
2. Identify infrastructure dependencies (e.g., new Kubernetes namespace, Redis cluster).  
3. Call `mcp ai ask` or CLI commands to confirm current state (e.g., `k8s_list_pods`, `ssh_execute`).  
4. Emit structured markdown with tasks, owners, and validation steps.

**Deliverable structure**

```markdown
## Milestone 1 — Provision staging primitives
- [ ] Confirm Kubernetes namespace `payments-staging` exists (`mcp k8s pods -n payments-staging`)
- [ ] Create Redis cache via Terraform (owner: SRE)
- [ ] Configure Orbit alias `payments-health-check`

## Milestone 2 — Deploy payment workers
- [ ] Build container image (`mcp docker ps` to verify rollout host)
- [ ] Apply deployment manifest
- [ ] Run smoke test (`mcp ai ask "Run payments health check"`)

## Milestone 3 — Observability & alerts
- [ ] Add dashboards (Grafana)
- [ ] Create PagerDuty service
- [ ] Document runbook (link)
```

**Why it works**

- Orbit keeps the MCP layer thin; all validation commands come from the existing toolset.  
- The agent can re-run tasks and mark them off interactively in chat or the CLI.

---

## 4. Designing your own autopilot stories

1. **Start from outcomes**: “Diagnose”, “Recover”, “Deploy”, “Audit”.  
2. **List the tools** Orbit should reach for (keep them within your `ORBIT_TOOLS` scope).  
3. **Add safety gates**: confirmation prompts, dry-run flags, or alias checks.  
4. **Document the expected transcript** so operators know what “good” looks like.  
5. **Include Ask AI prompts** users can paste in the editor to kick off the flow.

Keeping a living library of playbooks ensures new team members (or future you) can hand complicated incidents to Orbit with confidence—and it mirrors the “TDD workflow / Autopilot” section from the Task Master docs the team loved.
