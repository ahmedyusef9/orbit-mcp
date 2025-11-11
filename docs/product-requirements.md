# Orbit-MCP — Product Requirements & Roadmap

This document captures the current PRD and six-week launch roadmap for Orbit-MCP. It aligns with the Task Master-inspired architecture and documentation structure already present in this repo.

---

## 1. Core Features & Use Cases

### CF1. Multi-provider LLM routing
- **Use case:** Operator selects Anthropic, OpenAI, Gemini, Perplexity, or local Ollama; Orbit routes prompts and tool calls accordingly.
- **Why:** Works seamlessly in Cursor, Windsurf, VS Code (MCP) and the terminal CLI.

### CF2. Thin MCP adapter, fat core
- **Use case:** SSH/K8s/Docker/Grafana/OpenSearch operations remain identical from MCP chat and CLI.
- **Why:** Guarantees a single source of truth and unit-testable core modules.

### CF3. DevOps tool catalog (initial set)
- **SSH:** `ssh_run`, `ssh_tail`, `ssh_upload`
- **Kubernetes:** `k8s_get_pods`, `k8s_describe`, `k8s_logs`, `k8s_exec`
- **Docker:** `docker_ps`, `docker_logs`, `docker_exec`
- **Observability:** `grafana_check`, `opensearch_health`, `opensearch_shards`, `opensearch_logs_query`
- **Composite:** `diagnostic_report` (pods + events + logs, summarized)

### CF4. Tool modes
- `ORBIT_TOOLS=core | standard | all | <custom list>` to control context bloat and permissions.

### CF5. Long-running jobs & streaming
- SSE for live output (`stdout`, `progress`, `partial_result`)
- `start_job` / `get_job_status` / `get_job_output` pattern for heavy diagnostics.

### CF6. Safety rails
- Dry-run flags, confirmation fields for destructive actions, max duration/timeouts, secret redaction.

### CF7. Auth matrix & profiles
- SSH (key/password/agent), K8s (kubeconfig/context), Docker (local socket/remote), Grafana/OpenSearch (API tokens)
- Named profiles such as `dev2`, `prod-cluster-a`.

### CF8. Audit & RBAC (phase 2)
- Local audit log with request/response metadata.
- Optional role policies per tool.

### CF9. Docs & “Ask-AI” prompts
- Mintlify-ready docs with copyable MCP snippets, CLI examples, and curated prompts.

---

## 2. Problem / Goals / Non-Goals

- **Problem:** SREs and developers need a reproducible, editor- or terminal-based way to diagnose and fix infrastructure across SSH/K8s/Docker and observability stacks without bespoke glue scripts.
- **Goals:**  
  G1. Fast setup in editors via MCP (`npx -y orbit-mcp`) and simple env config.  
  G2. CLI with 1:1 parity to core functions for CI/local automation.  
  G3. Secure-by-default posture: least privilege, timeouts, redaction, audit log.  
  G4. Extensible tool catalog with validated inputs.  
  G5. Streaming outputs for long-running operations.
- **Non-goals:** Full ITSM/CMDB, secrets-manager replacement, custom dashboard UI.

---

## 3. Personas

| Persona | Needs |
|---------|-------|
| **Infra Engineer (primary)** | Diagnose failing pods, tail logs, restart services safely. |
| **Developer (secondary)** | Pull logs, check metrics during feature rollout. |
| **On-call SRE** | Run composite diagnostics to triage incidents quickly. |

---

## 4. Functional Requirements

1. MCP server (stdio) exposes tools with zod schemas.  
2. CLI commands wrap the same core functions.  
3. Model routing via environment keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.).  
4. Profiles stored in `~/.orbit/config.json` (per-cluster/server credentials).  
5. SSE streaming for long jobs; chunked log tail with back-pressure.  
6. Tool modes via `ORBIT_TOOLS`.  
7. `diagnostic_report` returns structured JSON plus short summary.  
8. Safe defaults: dry-run, confirm, timeouts, truncation.

---

## 5. Non-Functional Requirements

- **Security:** No secret echo; redact tokens; restrict upload paths; optional allowlists.  
- **Reliability:** Graceful cancel/timeout; retry transient network errors.  
- **Performance:** First tool call < 2s warm; stream begins < 1s.  
- **DX:** Clear errors; copy-ready snippets; versioned changelog.

---

## 6. Tool Catalog — Illustrative Schemas

```ts
const SshRunParams = z.object({
  profile: z.string().describe("Name of SSH profile"),
  cmd: z.string().min(1),
  cwd: z.string().optional(),
  timeoutSec: z.number().int().min(1).max(600).default(120),
  dryRun: z.boolean().default(false)
});

const K8sLogsParams = z.object({
  context: z.string(),
  namespace: z.string(),
  pod: z.string(),
  container: z.string().optional(),
  since: z.string().default("1h"),
  tail: z.number().int().max(5000).default(500),
  follow: z.boolean().default(false)
});

const OpenSearchHealthParams = z.object({
  profile: z.string(),
  detail: z.enum(["cluster", "indices"]).default("cluster")
});
```

**Registration pattern:** each tool exports `{ name, description, parameters, execute }`; server registers tools per mode (`core`, `standard`, `all`) during startup.

---

## 7. Configuration

- **Environment variables:** `ORBIT_TOOLS`, `ORBIT_CONFIG_PATH`, provider keys, optional `HTTP_PROXY`.
- **Profiles file** (`~/.orbit/config.json`):

```json
{
  "ssh": {
    "dev2": { "host": "ilgss1111", "user": "ops", "key": "~/.ssh/id_rsa" }
  },
  "k8s": {
    "dev2": { "kubeconfig": "~/.kube/config", "context": "dev2" }
  },
  "opensearch": {
    "dev2": { "baseUrl": "https://os-dev2:9200", "token": "..." }
  }
}
```

- **MCP snippet (Cursor/Windsurf):**

```json
{
  "mcpServers": {
    "orbit-mcp": {
      "command": "npx",
      "args": ["-y", "orbit-mcp"],
      "env": {
        "ANTHROPIC_API_KEY": "...",
        "OPENAI_API_KEY": "...",
        "ORBIT_TOOLS": "standard"
      },
      "disabled": false
    }
  }
}
```

---

## 8. Documentation Plan (Mintlify Structure)

1. **Getting Started:** Requirements → Installation (deeplink + manual) → Configuration (env + profiles) → First run.  
2. **Tool Catalog:** Core/Standard/All groupings with short examples and Ask-AI prompts.  
3. **CLI Reference:** Mirrors tool catalog with recipe-style usage.  
4. **Best Practices:** Auth, timeouts, safety, streaming, profiles.  
5. **Guides:** e.g., “Diagnose failing OpenSearch cluster”.  
6. **Changelog & Contributing:** changesets + versioning.

---

## 9. KPIs / Acceptance Criteria

- Time-to-first-interaction < 2 seconds; streaming starts < 1 second.  
- ≥ 95% success on valid tool calls.  
- New user reaches first `k8s_logs` call in < 10 minutes via docs.  
- ≥ 80% test coverage on core modules; end-to-end coverage for at least three scenarios.

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Secrets leakage | Central redactor; snapshot tests on logs. |
| Destructive ops | Dry-run, confirm, allowlists, RBAC policies. |
| Provider limits | Tool-first design, minimal prompts, scoped tool sets. |

---

# Delivery Roadmap (6-week Baseline)

## Phase 0 — Project Skeleton (2–3 days)
- **Deliverables:** Monorepo (pnpm/turbo), packages `mcp-server/`, `core/`, `cli/`, `docs/`; tsconfig, eslint, vitest, changesets; minimal MCP + CLI hello world.
- **DoD:** `npx -y orbit-mcp` runs and lists tools in Cursor.

## Phase 1 — Core + SSH/K8s (Week 1–2)
- **Build:** SSH & K8s adapters; tools (`ssh_run`, `ssh_tail`, `k8s_get_pods`, `k8s_describe`, `k8s_logs`, `k8s_exec`); profiles loader; `ORBIT_TOOLS` modes; SSE streaming for tails/logs.
- **Tests:** Param validation, timeouts, redaction; E2E with local kind/minikube + SSH localhost.
- **Docs:** Getting Started, installation variants, profiles.
- **DoD:** From editor, run `k8s_logs --follow` with live stream; CLI parity.

## Phase 2 — Docker + Observability (Week 3)
- **Build:** `docker_ps`, `docker_logs`, `docker_exec`; `grafana_check`, `opensearch_health`, `opensearch_shards`, `opensearch_logs_query`; `diagnostic_report`.
- **Tests:** Docker E2E; mock OpenSearch/Grafana responses.
- **Docs:** Tool catalog updates; recipes.
- **DoD:** Command returns concise OpenSearch health summary with streamable logs.

## Phase 3 — Safety, RBAC, Audit (Week 4)
- **Build:** Dry-run + confirm, allowlists, per-tool max duration; optional local RBAC policy; JSON audit log with trace IDs.
- **Tests:** Negative tests (blocked tools, timeouts); redaction snapshot tests.
- **Docs:** Best Practices, policy examples.
- **DoD:** Destructive calls require confirm; audit log records metadata.

## Phase 4 — CLI Polish & DX (Week 5)
- **Build:** CLI UX (rich help, profile switch, `--json` output), error taxonomy, friendly messages, changesets-based releases.
- **Docs:** CLI reference with copy-paste commands, Ask-AI prompts.
- **DoD:** New user completes first diagnostic in < 10 minutes following docs.

## Phase 5 — Hardening & Launch (Week 6)
- **Build:** Load tests for streaming; flaky network handling; telemetry toggles; opt-in crash reporting.
- **Docs:** End-to-end guide “Fix failing OpenSearch cluster”; changelog `v1.0.0`; contribution guide.
- **DoD:** 95% pass rate across E2E matrix; release tag `v1.0.0`.

---

## Post-Launch Backlog

- Kubernetes port-forward tool; Helm status commands.  
- Cloud vendor add-ons (EKS, GKE, AKS helpers).  
- Secrets backend integrations (Vault, Cloud KMS).  
- Shareable session transcripts / diagnostic reports.  
- VS Code MCP packaging + Windsurf snippets.

---

## Example “Ask-AI” Prompts

- “Initialize Orbit-MCP with **standard** tools and profile `dev2`.”  
- “Use `k8s_logs` to tail `opensearch-master-0` in `search` namespace for 10 minutes; summarize errors every minute.”  
- “Run `diagnostic_report` for `dev2` and propose next remediation steps.”

---

### Build Offers

If capacity allows, the next steps include:
1. Monorepo skeleton (tsconfig/turbo/changesets).  
2. MCP server with `ssh_run` / `k8s_logs` and SSE streaming.  
3. Mintlify docs starter using the structure above.

