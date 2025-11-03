# MCP Server Debugging Guide

## Common Issues: Cursor Connects But No Responses

If Cursor can connect to your MCP server but you're not seeing responses, follow this troubleshooting guide.

## Quick Diagnostic Checklist

### 1. ? Verify Transport Type

**For Cursor (local):** Use STDIO transport
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

**For remote/network:** Use HTTP+SSE transport
```json
{
  "mcpServers": {
    "task-master": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### 2. ? Check Method Names Match MCP Spec

**Correct method names:**
- `initialize` ?
- `initialized` ? (notification)
- `tools/list` ?
- `tools/call` ?
- `resources/list` ?
- `prompts/list` ?

**Wrong (common mistakes):**
- `list/tools` ?
- `listTools` ?
- `tools-list` ?

Our implementation uses the correct names: `tools/list` and `tools/call`.

### 3. ? Ensure Proper stdout/stderr Separation

**Critical:** All JSON-RPC responses must go to **stdout only**. Logs go to **stderr**.

? **Correct:**
```python
# Response to stdout
sys.stdout.write(json_response)
sys.stdout.write('\n')
sys.stdout.flush()

# Logs to stderr
logger.info("Processing request")  # Goes to stderr
```

? **Wrong:**
```python
print(json_response)  # Might go to wrong stream
print("Debug info")   # Mixed with JSON responses
```

Our implementation correctly uses:
- `sys.stdout.write()` for JSON-RPC responses
- `logging` (configured to `sys.stderr`) for logs

### 4. ? Verify Initialize Response Format

The `initialize` response must include:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "mcp-devops-server",
      "version": "0.2.0"
    },
    "capabilities": {
      "tools": {
        "listChanged": false
      }
    }
  }
}
```

Our implementation returns this format correctly.

### 5. ? Test with MCP Inspector

Install and run the MCP Inspector:

```bash
npm i -g @modelcontextprotocol/inspector
mcp-inspector "python3 -m src.mcp.mcp_main --transport stdio"
```

This will show you:
- All available tools
- Response/request logging
- Any JSON parsing errors

### 6. ? Test with Manual JSON-RPC

Send JSON-RPC messages directly:

```bash
# Initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python3 -m src.mcp.mcp_main --transport stdio

# List tools (after initialized)
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 -m src.mcp.mcp_main --transport stdio
```

### 7. ? Use Our Test Script

Run the test script to verify basic functionality:

```bash
python3 scripts/test_mcp_stdio.py
```

This will:
1. Start the server
2. Send initialize request
3. Send initialized notification
4. Request tools/list
5. Verify responses

## Common Pitfalls

### Pitfall 1: Process Exits Too Early

? **Wrong:**
```python
def main():
    server = MCPDevOpsServer()
    server.process_message(json.dumps(init_request))
    # Process exits here!
```

? **Correct:**
```python
async def main():
    server = MCPDevOpsServer()
    transport = StdioTransport(server)
    await transport.start()  # Keeps running
```

Our implementation uses `asyncio.run(run_stdio_server(server))` which keeps the server alive.

### Pitfall 2: Buffering Issues

? **Wrong:**
```python
# Python's stdout might be buffered
print(json_response)
```

? **Correct:**
```python
sys.stdout.write(json_response)
sys.stdout.write('\n')
sys.stdout.flush()  # Force immediate output
```

Our implementation uses `flush()` after every write.

### Pitfall 3: Extra Output on stdout

? **Wrong:**
```python
print("Server starting...")  # Goes to stdout, corrupts JSON!
sys.stdout.write(json_response)
```

? **Correct:**
```python
logger.info("Server starting...")  # Goes to stderr
sys.stdout.write(json_response)    # Only JSON on stdout
```

Our implementation uses `logging` configured to `sys.stderr`.

### Pitfall 4: Wrong JSON Format

? **Wrong:**
```json
{
  "jsonrpc": "2.0",
  "result": {...}  // Missing "id" field
}
```

? **Correct:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {...}
}
```

Our implementation includes the `id` field in all responses.

## Debugging Steps

### Step 1: Enable Verbose Logging

```bash
python3 -m src.mcp.mcp_main --transport stdio --verbose
```

This logs all requests/responses to stderr.

### Step 2: Check Cursor MCP Settings

1. Open Cursor Settings
2. Go to MCP section
3. Verify server is enabled
4. Check server status (should show "connected")

### Step 3: Inspect Cursor Logs

Cursor logs MCP activity. Check:
- `~/.cursor/logs/` (or `%APPDATA%\Cursor\logs` on Windows)
- Look for MCP-related errors

### Step 4: Verify Environment Variables

If your server needs API keys:

```json
{
  "mcpServers": {
    "task-master": {
      "command": "python3",
      "args": ["-m", "src.mcp.mcp_main", "--transport", "stdio"],
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

### Step 5: Test Outside Cursor

Use the test script or manual JSON-RPC to verify the server works independently of Cursor:

```bash
# Should return JSON response
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python3 -m src.mcp.mcp_main --transport stdio 2>/dev/null
```

## Expected Behavior

When working correctly:

1. **Initialize:** Server responds with capabilities
2. **Initialized:** Server marks itself as initialized (no response needed)
3. **tools/list:** Server responds with list of tools (23+ tools in our case)
4. **tools/call:** Server executes tool and returns result

## Getting Help

If issues persist:

1. Run test script: `python3 scripts/test_mcp_stdio.py`
2. Run with verbose logging: `--verbose`
3. Check server stderr output for errors
4. Verify method names match MCP spec
5. Ensure stdout only contains JSON-RPC responses

## Reference

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [Cursor MCP Docs](https://cursor.sh/docs)