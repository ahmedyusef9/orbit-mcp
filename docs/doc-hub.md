# Orbit-MCP Documentation Hub

Orbit-MCP’s docs mirror the playbook used by Task Master: fast onboarding, a discoverable tool catalog, and repeatable workflows for AI-assisted operations. Use this file as the map—each link points to a focused guide you can drop into Mintlify, Docusaurus, or keep as Markdown.

---

## Getting started

- [Quick Start](./quick-start.md) — from requirements and installation to your first command in under ten minutes.
- [Configuration](./configuration.md) — single source of truth for SSH, Docker, Kubernetes, LLM providers, and tool scopes.
- [Product Requirements & Roadmap](./product-requirements.md) — PRD, six-week delivery plan, post-launch backlog.

> **Ask AI**  
> “Give me the TL;DR for Orbit-MCP setup and link me to the config schema.”

---

## Capabilities

- [MCP Tools](./mcp-tools.md) — grouped catalog (`core`/`standard`/`all`) with zod-style schema detail for each tool.
- [CLI Reference](./cli-reference.md) — command cheatsheet with runnable snippets for SSH, Docker, Kubernetes, and AI modes.
- [Autopilot Playbooks](./autopilot.md) — TDD-style stories showing how Orbit plans, executes, and reflects on multi-step incidents.

---

## Operations & practices

- [Best Practices](./best-practices.md) — authentication layouts, safety rails, budgeting, and observability patterns adapted from Task Master.

---

## Suggested reading flow

1. **Quick Start**: install + run the MCP server once.  
2. **Configuration**: wire in infrastructure and provider keys, pick a tool scope.  
3. **Product Requirements & Roadmap**: understand the end-to-end build targets and timeline.  
4. **MCP Tools / CLI Reference**: explore what the LLM can call versus what humans can script.  
5. **Autopilot Playbooks + Best Practices**: operationalize Orbit for on-call, SRE, and CI/CD scenarios.

---

## Keeping docs in sync

- Each guide leans on copyable code blocks and “Ask AI” prompts so users can paste directly into Cursor or Claude Code.
- Whenever you add a new tool or CLI command, update the relevant section plus the scope table in `configuration.md`.
- The structure is Mintlify-ready—drop the files into `mint.json` or another static site generator and you instantly get navigation pillars.

Have an idea or notice drift? Open an issue in the repo under “Docs” or drop a note in `README.md` so we can track improvements.
