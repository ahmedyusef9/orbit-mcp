# Orbit-MCP Documentation & Installation Refresh PRD

## 1. Context

Orbit-MCP’s public surface (README, install guidance, ancillary Markdown) is fragmented across the repository. Users jump between Python-focused instructions, legacy implementation notes, and scattered README variants before they can launch the MCP server. This PRD consolidates documentation into a single hub, clarifies the Python-first distribution story, and standardises configuration flows so new teams can adopt Orbit-MCP without reverse-engineering internal history.

## 2. Goals

- **G1 – Unified entry point:** Deliver a single, GitHub-visible landing page that explains what Orbit-MCP is, why it ships as a Python package, and how to install/configure it in under 10 minutes.
- **G2 – Organised knowledge base:** Relocate every Markdown asset into `docs/`, grouped by purpose (guides, archival notes, meta docs) so maintainers can reason about scope and update paths quickly.
- **G3 – Config clarity:** Provide step-by-step install + config recipes (pipx, virtualenv, MCP client wiring) that map directly to the CLI and MCP options shipped in `src/mcp`.
- **G4 – Packaging compatibility:** Ensure `setup.py` and any automation continue to read the canonical README for PyPI metadata after files move.

## 3. Non-Goals

- Changing the underlying CLI or MCP server behaviour.
- Rewriting deep technical content in the archival documents beyond path/heading normalisation.
- Publishing documentation to an external site (Mintlify, Docusaurus) as part of this release.

## 4. Users & Personas

- **First-time Platform Engineers:** evaluating Orbit-MCP against other DevOps copilots; need a polished README and clear install path.
- **Internal SREs / Maintainers:** keep docs in sync, know where to add change notes, confirm packaging still works after moves.
- **AI Tool Integrators (Cursor, Windsurf, Claude Code):** require specific MCP config snippets and explanation of tool scopes.

## 5. Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR1 | Move every `.md` file outside `docs/` into the `docs/` hierarchy. | `git ls-files '*.md'` returns paths rooted in `docs/`. Tests and automation reference new locations. |
| FR2 | Promote the updated README content to the canonical landing page inside `docs/README.md`. | README covers value prop, Python rationale, install, config, quick start, tool scopes, troubleshooting, contributing, licensing. |
| FR3 | Preserve legacy implementation notes in a discoverable archive. | All historical implementation markdown files live under `docs/archive/` with unchanged filenames. |
| FR4 | Surface contributor- and change-log material alongside primary docs. | `docs/CONTRIBUTING.md` and `docs/CHANGELOG.md` available and referenced from the landing page. |
| FR5 | Provide a structured installation section for pipx, virtualenv, and editable clone workflows. | Steps include command snippets, entry-point verification, and PATH guidance. |
| FR6 | Document configuration bootstrapping. | README links to configuration guide and shows `mcp config init` / `config.example.yaml` flow. |
| FR7 | Update packaging metadata. | `setup.py` resolves the relocated README without breaking `pip install mcp-server`. |

## 6. Technical Notes

- Use git moves (`mv`) to retain file history.
- Update relative links inside README and any cross-document references to match new paths (`./quick-start.md` vs `docs/quick-start.md`).
- Adjust import paths in tests or tooling scripts if they read Markdown directly.
- Ensure CI or release scripts that read `README.md` are redirected to the new location.

## 7. Milestones & Deliverables

| Milestone | Deliverable | Owner | ETA |
|-----------|-------------|-------|-----|
| M1 | New README (Python rationale, install, config) merged | Docs maintainer | Day 1 |
| M2 | All Markdown centralised under `docs/`, archive and contributor docs linked | Docs maintainer | Day 2 |
| M3 | Packaging + links verified, PR merged to `main` | Release engineer | Day 2 |
| M4 | Optional follow-up: publish docs structure to external site (out of scope) | TBD | Later |

## 8. Risks & Mitigations

- **Broken Links:** Relative links may 404 after moves. Mitigation: run a link checker (optional) and manual spot-check key paths before merge.
- **Packaging Regression:** `setup.py` failing to find README. Mitigation: update the file path and run `pip install .` locally.
- **Team Confusion:** Contributors expect old paths. Mitigation: highlight the new `docs/` structure in the changelog and README contributing section.

## 9. Success Metrics

- Root directory contains zero `.md` files; `docs/` holds the entire documentation tree.
- README explains Python-first strategy and install/config steps with zero open issues requesting clarification.
- Packaging succeeds in CI (or local `pip install .`) after relocation.
