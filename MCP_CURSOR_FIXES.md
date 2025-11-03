# MCP Cursor Integration Fixes

## Summary of Fixes Applied

Based on the troubleshooting guide for "Cursor connects but no responses" issues, the following fixes have been applied:

### 1. ? STDIO Transport Improvements

**File:** `src/mcp/transports.py`

**Changes:**
- Improved error handling for JSON parsing failures
- Added proper error response generation when exceptions occur
- Ensured stdout is flushed immediately after each response
- Better handling of EOF and empty lines
- Logging limited to first 200 chars to avoid overwhelming logs

**Key improvements:**
- Unbuffered stdout writes with explicit flush
- Error responses sent even when exceptions occur (maintaining JSON-RPC compliance)
- More robust line reading with proper EOF detection

### 2. ? Verification of Method Names

**Verified:** All method names match MCP specification:
- ? `initialize` (not `init`)
- ? `tools/list` (not `list/tools` or `toolsList`)
- ? `tools/call` (not `tools/callTool` or `callTool`)
- ? `initialized` notification handled correctly

### 3. ? stdout/stderr Separation

**Verified:** 
- All JSON-RPC responses go to `stdout` only
- All logging goes to `stderr` (configured in `mcp_main.py`)
- No print statements that would corrupt JSON output

### 4. ? Initialize Response Format

**Verified:** Initialize response includes:
- `protocolVersion`: "2024-11-05"
- `serverInfo`: name and version
- `capabilities`: tools capability properly set

### 5. ? Server Lifecycle

**Verified:**
- Server stays alive after initialization (async event loop)
- Processes requests in a continuous loop
- Handles EOF gracefully (stops when stdin closes)

## Testing Tools Added

### Test Script: `scripts/test_mcp_stdio.py`

A comprehensive test script that:
1. Starts the MCP server as a subprocess
2. Sends initialize request
3. Sends initialized notification
4. Requests tools/list
5. Validates responses match expected format

**Usage:**
```bash
python3 scripts/test_mcp_stdio.py
```

### Debugging Guide: `docs/MCP_DEBUGGING.md`

Complete troubleshooting guide covering:
- Common pitfalls and fixes
- Method name verification
- stdout/stderr separation
- Testing outside Cursor
- Using MCP Inspector

## Cursor Configuration Examples

### Updated Configuration Files

**File:** `examples/task-master-cursor-config.json`

Updated to use explicit Python module path:
```json
{
  "mcpServers": {
    "task-master": {
      "command": "python3",
      "args": ["-m", "src.mcp.mcp_main", "--transport", "stdio"]
    }
  }
}
```

**Alternative** (if installed via setup.py):
```json
{
  "mcpServers": {
    "task-master": {
      "command": "mcp-server",
      "args": ["--transport", "stdio"]
    }
  }
}
```

## How to Test

### Step 1: Test Server Independently

```bash
# Test with our script
python3 scripts/test_mcp_stdio.py

# Or manually
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python3 -m src.mcp.mcp_main --transport stdio 2>/dev/null
```

### Step 2: Test with MCP Inspector

```bash
npm i -g @modelcontextprotocol/inspector
mcp-inspector "python3 -m src.mcp.mcp_main --transport stdio"
```

### Step 3: Configure Cursor

1. Copy `examples/task-master-cursor-config.json` to `~/.cursor/mcp.json`
2. Update paths if needed
3. Set environment variables (API keys)
4. Restart Cursor
5. Enable server in Settings ? MCP

### Step 4: Verify in Cursor

1. Open Cursor Settings
2. Go to MCP section
3. Verify server shows "Connected"
4. Try asking: "List all available tools"

## Common Issues and Solutions

### Issue: "No response from server"

**Check:**
1. ? Server process is running (check Cursor MCP status)
2. ? Method names are correct (`tools/list` not `list/tools`)
3. ? stdout only contains JSON (no print statements)
4. ? Server stays alive (check it's not exiting)

**Solution:** Run test script to verify basic functionality

### Issue: "Method not found" errors

**Check:**
1. ? Method names match MCP spec exactly
2. ? Server registered the method handler
3. ? Server is initialized (received `initialized` notification)

**Solution:** Check server logs for registration messages

### Issue: "Invalid JSON" errors

**Check:**
1. ? No extra output on stdout (only JSON-RPC)
2. ? Responses properly formatted with `jsonrpc: "2.0"`
3. ? All responses include `id` field (except notifications)

**Solution:** Enable verbose logging and check stderr output

## Next Steps

If issues persist after these fixes:

1. **Run test script** - Verify server works independently
2. **Check Cursor logs** - Look for MCP-related errors
3. **Enable verbose mode** - `--verbose` flag shows detailed logs
4. **Use MCP Inspector** - Visual debugging of requests/responses
5. **Verify configuration** - Double-check `~/.cursor/mcp.json` format

## Files Modified

- ? `src/mcp/transports.py` - Improved STDIO handling
- ? `scripts/test_mcp_stdio.py` - New test script
- ? `docs/MCP_DEBUGGING.md` - New debugging guide
- ? `examples/task-master-cursor-config.json` - Updated config
- ? `MCP_CURSOR_FIXES.md` - This document

## Verification Checklist

Before reporting issues, verify:

- [ ] Test script passes: `python3 scripts/test_mcp_stdio.py`
- [ ] Server responds to manual JSON-RPC calls
- [ ] stdout only contains JSON (check with `2>/dev/null`)
- [ ] Method names match MCP spec exactly
- [ ] Cursor config file syntax is valid JSON
- [ ] Server shows "Connected" in Cursor MCP settings
- [ ] Environment variables are set (if needed)

---

**All fixes have been applied and tested. The server should now work correctly with Cursor.**