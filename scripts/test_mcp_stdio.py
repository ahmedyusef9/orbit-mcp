#!/usr/bin/env python3
"""
Test script to verify MCP server STDIO communication.
This mimics what Cursor does when connecting to the MCP server.
"""

import json
import sys
import subprocess
import time

def test_mcp_server():
    """Test MCP server with STDIO transport."""
    
    # Start the server process
    print("Starting MCP server...", file=sys.stderr)
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.mcp.mcp_main", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0  # Unbuffered
    )
    
    try:
        # Test 1: Initialize
        print("\n=== Test 1: Initialize ===", file=sys.stderr)
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        request_str = json.dumps(init_request) + "\n"
        print(f"Sending: {request_str.strip()[:100]}...", file=sys.stderr)
        server_process.stdin.write(request_str)
        server_process.stdin.flush()
        
        # Read response
        response_line = server_process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)
            
            if "result" in response and "capabilities" in response["result"]:
                print("? Initialize successful", file=sys.stderr)
            else:
                print("? Initialize failed - invalid response", file=sys.stderr)
                return False
        else:
            print("? No response to initialize", file=sys.stderr)
            return False
        
        # Test 2: Send initialized notification
        print("\n=== Test 2: Initialized Notification ===", file=sys.stderr)
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        request_str = json.dumps(initialized_notification) + "\n"
        server_process.stdin.write(request_str)
        server_process.stdin.flush()
        # Notifications don't get responses
        
        time.sleep(0.1)  # Small delay
        
        # Test 3: List tools
        print("\n=== Test 3: List Tools ===", file=sys.stderr)
        tools_list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        request_str = json.dumps(tools_list_request) + "\n"
        print(f"Sending: {request_str.strip()[:100]}...", file=sys.stderr)
        server_process.stdin.write(request_str)
        server_process.stdin.flush()
        
        # Read response
        response_line = server_process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print(f"Response keys: {list(response.keys())}", file=sys.stderr)
            
            if "result" in response and "tools" in response["result"]:
                tools_count = len(response["result"]["tools"])
                print(f"? Tools list successful - {tools_count} tools found", file=sys.stderr)
                
                # Show first few tool names
                tool_names = [tool["name"] for tool in response["result"]["tools"][:5]]
                print(f"   Sample tools: {', '.join(tool_names)}", file=sys.stderr)
                return True
            else:
                print(f"? Tools list failed - invalid response: {response}", file=sys.stderr)
                return False
        else:
            print("? No response to tools/list", file=sys.stderr)
            return False
    
    except Exception as e:
        print(f"? Test failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False
    
    finally:
        # Cleanup
        server_process.terminate()
        try:
            server_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server_process.kill()
        
        # Print stderr output (logs)
        stderr_output = server_process.stderr.read()
        if stderr_output:
            print("\n=== Server Logs ===", file=sys.stderr)
            print(stderr_output, file=sys.stderr)

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)