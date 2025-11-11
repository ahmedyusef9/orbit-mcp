# ?? orbit-mcp: Next Steps & Roadmap

## Current Status

? **Phase 1 Complete**: MCP Server with 14 DevOps tools  
?? **Phase 2 In Progress**: Transformation to orbit-mcp with 40+ tools

---

## What You Have Now

### Working System (Phase 1)
- ? MCP protocol implementation (JSON-RPC 2.0)
- ? 14 DevOps tools (SSH, Docker, Kubernetes)
- ? STDIO and HTTP+SSE transports
- ? Cursor integration
- ? Comprehensive documentation
- ? Configuration system

### Documentation Created
- ? ORBIT_TRANSFORMATION.md - Overview of changes
- ? ORBIT_IMPLEMENTATION_GUIDE.md - Complete technical spec
- ? This file (ORBIT_NEXT_STEPS.md) - Action plan

---

## What Needs to Be Built

### Core Systems (Priority 1)

#### 1. Profile Management System
**File**: `src/orbit/core/profile.py`

**Key Features:**
- Load profiles from `~/.orbit/config.yaml`
- Switch between profiles (prod, staging, dev)
- Profile-specific configuration (SSH, K8s, Docker, allowlists)
- Context awareness

**Estimated Time**: 1-2 days

#### 2. Allowlist/Safety Engine
**File**: `src/orbit/core/allowlist.py`

**Key Features:**
- Validate passthrough commands against allowlists
- Per-profile safety rules
- Block dangerous operations by default
- Clear error messages for blocked commands

**Estimated Time**: 1-2 days

#### 3. Audit Logging System
**File**: `src/orbit/core/audit.py`

**Key Features:**
- Log all operations to `~/.orbit/audit.log`
- Include: timestamp, tool, profile, args hash, context, result
- Configurable log levels
- Log rotation

**Estimated Time**: 1 day

#### 4. Redaction Engine
**File**: `src/orbit/core/redaction.py`

**Key Features:**
- Redact sensitive data from outputs
- Pattern-based matching (token, password, secret, etc.)
- Configurable patterns
- Apply to both text and structured data

**Estimated Time**: 1 day

#### 5. Version Detection
**File**: `src/orbit/core/versions.py`

**Key Features:**
- Detect kubectl, docker, compose, helm versions
- Version comparison utilities
- Feature gating based on versions
- Clear error messages for missing tools

**Estimated Time**: 1 day

### Enhanced Managers (Priority 2)

#### 6. Enhanced Docker Manager
**File**: `src/orbit/managers/docker_manager.py`

**Additions:**
- Docker Compose support (v2)
- Passthrough command execution
- Multi-file compose support
- Enhanced error handling

**Estimated Time**: 2-3 days

#### 7. Enhanced Kubernetes Manager
**File**: `src/orbit/managers/k8s_manager.py`

**Additions:**
- Multi-namespace operations
- kubectl passthrough
- Multi-pod log streaming (stern-like)
- Helm integration
- Enhanced resource management

**Estimated Time**: 3-4 days

### Tool Implementations (Priority 3)

#### 8. Session Tools
**File**: `src/orbit/tools/session.py`

**Tools**: (3 tools)
- profile.set
- context.show
- allowlist.show / allowlist.test

**Estimated Time**: 1 day

#### 9. SSH & Linux Tools
**File**: `src/orbit/tools/ssh.py`

**Tools**: (6 tools)
- ssh.run
- sys.top / sys.df / sys.free
- sys.journal
- ssh.script

**Estimated Time**: 2 days

#### 10. Docker Tools
**File**: `src/orbit/tools/docker.py`

**Tools**: (15 tools)
- docker.version, docker.ps, docker.inspect
- docker.logs, docker.start/stop/restart
- docker.kill, docker.rm, docker.exec
- docker.cp, docker.pull/push/build
- docker.images, docker.rmi
- docker.cli (passthrough)

**Estimated Time**: 3-4 days

#### 11. Compose Tools
**File**: `src/orbit/tools/compose.py`

**Tools**: (8 tools)
- compose.version
- compose.up/down, compose.ps/logs
- compose.pull/build
- compose.config/restart
- compose.cli (passthrough)

**Estimated Time**: 2-3 days

#### 12. Kubernetes Tools
**File**: `src/orbit/tools/kubernetes.py`

**Tools**: (12 tools)
- k8s.contexts / k8s.useContext
- k8s.namespaces / k8s.useNamespace
- k8s.get, k8s.describe
- k8s.logs (multi-pod), k8s.exec
- k8s.apply/delete
- k8s.kubectl (passthrough)

**Estimated Time**: 4-5 days

#### 13. Helm Tools
**File**: `src/orbit/tools/helm.py`

**Tools**: (5 tools)
- helm.version
- helm.releases, helm.get
- helm.upgrade/uninstall

**Estimated Time**: 2 days

#### 14. Log Tools
**File**: `src/orbit/tools/logs.py`

**Tools**: (2 tools)
- logs.tail
- logs.search

**Estimated Time**: 1 day

#### 15. Ticket Tools
**File**: `src/orbit/tools/tickets.py`

**Tools**: (4 tools)
- ticket.create/update/list/get

**Estimated Time**: 1-2 days

### Integration & Testing (Priority 4)

#### 16. MCP Server Integration
**File**: `src/orbit/server.py`

**Updates:**
- Register all 40+ tools
- Integrate with profile system
- Add allowlist checks
- Apply audit logging
- Add redaction
- Update error handling

**Estimated Time**: 2-3 days

#### 17. CLI Updates
**File**: `src/orbit/cli.py`

**Updates:**
- Rename mcp ? orbit
- Add profile commands
- Add context commands
- Update help text
- Add version command

**Estimated Time**: 1-2 days

#### 18. Comprehensive Testing

**Test Coverage:**
- Unit tests for core systems
- Integration tests for tools
- End-to-end tests with Cursor
- Profile switching tests
- Allowlist enforcement tests
- Audit log verification
- Redaction tests

**Estimated Time**: 3-4 days

### Documentation (Priority 5)

#### 19. Complete Documentation

**Files to Create/Update:**
- ORBIT_README.md (main docs)
- TOOLS.md (all 40+ tools reference)
- PROFILES.md (profile configuration guide)
- ALLOWLIST.md (safety configuration)
- CURSOR.md (Cursor integration)
- SECURITY.md (updated for orbit)
- MIGRATION.md (from mcp-server to orbit-mcp)

**Estimated Time**: 2-3 days

---

## Estimated Timeline

### Phase 1: Core Systems (1 week)
- Profile management
- Allowlist engine
- Audit logging
- Redaction
- Version detection

### Phase 2: Enhanced Managers (1 week)
- Enhanced Docker manager with Compose
- Enhanced K8s manager with multi-namespace

### Phase 3: Tool Implementation (2-3 weeks)
- Session tools
- SSH tools
- Docker tools
- Compose tools
- Kubernetes tools
- Helm tools
- Log tools
- Ticket tools

### Phase 4: Integration & Testing (1 week)
- MCP server integration
- CLI updates
- Comprehensive testing

### Phase 5: Documentation (1 week)
- All documentation updates
- Migration guide
- Examples and tutorials

**Total Estimated Time**: 6-7 weeks for complete implementation

---

## Recommended Approach

### Option 1: Incremental (Recommended)

**Week 1-2: Foundation**
- Implement core systems
- Update existing tools to use profiles

**Week 3-4: Docker & Compose**
- Enhanced Docker manager
- Docker tools
- Compose tools

**Week 5-6: Kubernetes & Helm**
- Enhanced K8s manager
- Kubernetes tools
- Helm tools

**Week 7: Polish**
- Testing
- Documentation
- Cursor integration refinement

### Option 2: Parallel Tracks

**Track A (Core):** Profile system, allowlist, audit
**Track B (Docker):** Docker & Compose tools
**Track C (K8s):** Kubernetes & Helm tools

Run tracks in parallel with 2-3 developers

---

## Quick Wins (Ship Fast)

If you want to ship something quickly, prioritize:

1. **Profile System** (1-2 days)
   - Basic profile switching
   - Context display

2. **5 Most Requested Tools** (2-3 days)
   - docker.cli (passthrough)
   - compose.up/down
   - k8s.kubectl (passthrough)
   - k8s.logs (multi-pod)
   - helm.releases

3. **Basic Allowlist** (1 day)
   - Simple verb checking
   - Block dangerous operations

4. **Documentation** (1 day)
   - Quick start guide
   - Tool reference for new tools

**Total: 1 week for "orbit-mcp lite"**

---

## Implementation Resources

### Templates Provided

1. **ORBIT_TRANSFORMATION.md** - Overview
2. **ORBIT_IMPLEMENTATION_GUIDE.md** - Complete technical spec with:
   - Architecture details
   - Code examples for core systems
   - All tool schemas
   - Configuration template

### What You Need

**Python Libraries:**
```txt
# Existing
paramiko>=3.0.0
docker>=6.0.0
kubernetes>=25.0.0
click>=8.0.0
pyyaml>=6.0
cryptography>=41.0.0
rich>=13.0.0
aiohttp>=3.9.0

# New
docker-compose>=2.0.0  # If using Python API
```

**External Tools:**
- kubectl (for Kubernetes)
- docker (for Docker)
- docker compose (for Compose)
- helm (for Helm)
- journalctl (for Linux logs)

---

## Testing Strategy

### Unit Tests
```python
# test_profiles.py
def test_profile_switching()
def test_profile_not_found()
def test_get_context()

# test_allowlist.py
def test_kubectl_allowlist()
def test_docker_allowlist()
def test_dangerous_command_blocked()

# test_audit.py
def test_audit_log_created()
def test_audit_entry_format()
```

### Integration Tests
```python
# test_docker_integration.py
def test_docker_ps_with_profile()
def test_compose_up_with_allowlist()

# test_k8s_integration.py
def test_kubectl_passthrough()
def test_multi_namespace_logs()
```

### E2E Tests with Cursor
1. Configure Cursor with orbit-mcp
2. Test natural language commands
3. Verify user approval workflow
4. Check output formatting
5. Verify audit logs

---

## Migration Path

### For Existing Users

**Step 1: Backup**
```bash
cp ~/.mcp/config.yaml ~/.mcp/config.yaml.backup
```

**Step 2: Install orbit-mcp**
```bash
cd /workspace
git checkout -b orbit-enhancement
pip install -e .
```

**Step 3: Migrate Configuration**
```bash
orbit init --migrate-from ~/.mcp/config.yaml
```

**Step 4: Test**
```bash
orbit --help
orbit context show
```

**Step 5: Update Cursor**
Edit `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "orbit-mcp": {
      "command": "orbit",
      "args": [],
      "env": {
        "ORBIT_CONFIG": "~/.orbit/config.yaml",
        "ORBIT_PROFILE": "staging"
      }
    }
  }
}
```

---

## Decision Points

### Critical Decisions Needed

1. **Renaming Now vs Later**
   - Option A: Rename everything now (breaking change)
   - Option B: Keep mcp-server, add orbit as alias
   - **Recommendation**: Rename now (cleaner)

2. **Profile Storage**
   - Option A: Single config.yaml with all profiles
   - Option B: Separate files per profile
   - **Recommendation**: Single file (easier management)

3. **Allowlist Strictness**
   - Option A: Default deny (safest)
   - Option B: Default allow (most flexible)
   - **Recommendation**: Default deny with easy override

4. **Audit Log Format**
   - Option A: JSON lines (machine readable)
   - Option B: Structured text (human readable)
   - **Recommendation**: JSON lines (parseable)

---

## Getting Help

### Resources

1. **Implementation Guide**: ORBIT_IMPLEMENTATION_GUIDE.md
2. **Transformation Doc**: ORBIT_TRANSFORMATION.md
3. **Existing Code**: Current MCP implementation
4. **References**: kubectl, docker, compose, helm docs

### Questions to Resolve

- [ ] Confirm profile structure
- [ ] Review allowlist rules
- [ ] Approve tool list
- [ ] Confirm audit log format
- [ ] Review redaction patterns

---

## Success Metrics

### v0.1 (Lite) Success
- ? Profile system working
- ? 5 most-used tools implemented
- ? Basic allowlist enforced
- ? Works with Cursor
- ? Documentation complete

### v1.0 (Complete) Success
- ? All 40+ tools implemented
- ? Full allowlist engine
- ? Comprehensive audit logging
- ? All passthroughs working
- ? Multi-namespace K8s
- ? Helm integration
- ? Production ready

---

## Conclusion

The transformation to **orbit-mcp** is well-defined and achievable. The implementation guide provides all technical details needed. The recommended approach is:

1. **Start with core systems** (1-2 weeks)
2. **Implement tools incrementally** (2-3 weeks)
3. **Test thoroughly** (1 week)
4. **Document everything** (1 week)

**Total: 5-7 weeks for complete implementation**

Or ship "orbit-mcp lite" in **1 week** with core features.

---

**Next Action**: Review this document and ORBIT_IMPLEMENTATION_GUIDE.md, then decide on timeline and approach. Let me know which path you want to take!
