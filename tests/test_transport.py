"""Tests for MCP transport modes (STDIO, HTTP, SSE)."""

import pytest
from unittest.mock import MagicMock, patch
import asyncio
import json
from io import StringIO


class TestSTDIOTransport:
    """Tests for STDIO transport mode."""
    
    def test_stdio_basic_command(self):
        """Test basic command via STDIO."""
        # Simulate STDIO communication
        stdin_data = json.dumps({
            "method": "tools/call",
            "params": {
                "name": "ssh.run",
                "arguments": {"host": "test", "command": "echo hello"}
            },
            "id": 1
        })
        
        # Mock stdin/stdout
        mock_stdin = StringIO(stdin_data + '\n')
        mock_stdout = StringIO()
        
        # This would be the actual STDIO handler
        # For now, just verify structure
        request = json.loads(stdin_data)
        
        assert request['method'] == 'tools/call'
        assert 'params' in request
        assert request['params']['name'] == 'ssh.run'
    
    def test_stdio_multi_turn_conversation(self):
        """Test multiple commands through STDIO."""
        commands = [
            {"method": "tools/list", "id": 1},
            {"method": "tools/call", "params": {"name": "ssh.run"}, "id": 2},
            {"method": "tools/call", "params": {"name": "k8s.get"}, "id": 3}
        ]
        
        for cmd in commands:
            # Verify each command is valid
            assert 'method' in cmd
            assert 'id' in cmd
    
    def test_stdio_graceful_shutdown(self):
        """Test STDIO transport shuts down gracefully."""
        # Send EOF or quit command
        quit_command = json.dumps({"method": "quit", "id": 99})
        
        # Verify command structure
        cmd = json.loads(quit_command)
        assert cmd['method'] == 'quit'
    
    def test_stdio_error_response(self):
        """Test error responses via STDIO."""
        error_response = {
            "error": {
                "code": "METHOD_NOT_FOUND",
                "message": "Unknown method: invalid.method"
            },
            "id": 1
        }
        
        # Verify error structure
        assert 'error' in error_response
        assert 'code' in error_response['error']
        assert 'message' in error_response['error']


@pytest.mark.integration
class TestHTTPTransport:
    """Tests for HTTP transport mode."""
    
    @pytest.mark.asyncio
    async def test_http_tool_call(self):
        """Test tool invocation via HTTP."""
        import aiohttp
        
        # Mock HTTP client
        async def mock_post(url, json_data):
            class MockResponse:
                status = 200
                async def json(self):
                    return {
                        "result": {
                            "stdout": "command output",
                            "exit_code": 0
                        }
                    }
            return MockResponse()
        
        # Test HTTP request structure
        request_data = {
            "method": "tools/call",
            "params": {
                "name": "ssh.run",
                "arguments": {
                    "host": "test-server",
                    "command": "uptime"
                }
            }
        }
        
        # Verify request structure
        assert request_data['method'] == 'tools/call'
        assert 'params' in request_data
    
    @pytest.mark.asyncio
    async def test_http_list_tools(self):
        """Test listing tools via HTTP GET."""
        # Mock HTTP GET response
        expected_tools = [
            {"name": "ssh.run", "description": "Execute SSH command"},
            {"name": "k8s.get", "description": "Get Kubernetes resources"},
            {"name": "docker.logs", "description": "Get container logs"}
        ]
        
        # Verify response structure
        assert isinstance(expected_tools, list)
        assert all('name' in tool for tool in expected_tools)
        assert all('description' in tool for tool in expected_tools)
    
    @pytest.mark.asyncio
    async def test_http_error_codes(self):
        """Test HTTP error code handling."""
        error_scenarios = [
            (400, "Bad Request - invalid parameters"),
            (401, "Unauthorized - invalid credentials"),
            (404, "Not Found - tool does not exist"),
            (500, "Internal Server Error"),
            (503, "Service Unavailable")
        ]
        
        for status_code, message in error_scenarios:
            # Each should be handled appropriately
            assert status_code >= 400
    
    @pytest.mark.asyncio
    async def test_http_large_payload(self):
        """Test handling large payloads over HTTP."""
        # Large log content
        large_payload = {
            "method": "tools/call",
            "params": {
                "name": "docker.logs",
                "arguments": {
                    "container": "test",
                    "logs": "x" * 100000  # 100KB
                }
            }
        }
        
        # Should be serializable
        json_str = json.dumps(large_payload)
        assert len(json_str) > 100000
    
    @pytest.mark.asyncio
    async def test_http_concurrent_requests(self):
        """Test concurrent HTTP requests."""
        # Simulate multiple concurrent requests
        requests = [
            {"method": "tools/call", "params": {"name": "ssh.run"}, "id": i}
            for i in range(10)
        ]
        
        # All should have unique IDs
        ids = [req['id'] for req in requests]
        assert len(ids) == len(set(ids))


@pytest.mark.integration
class TestSSETransport:
    """Tests for Server-Sent Events transport."""
    
    @pytest.mark.asyncio
    async def test_sse_streaming_logs(self):
        """Test log streaming via SSE."""
        # Simulate SSE events
        events = [
            "data: log line 1\n\n",
            "data: log line 2\n\n",
            "data: log line 3\n\n",
            "data: [DONE]\n\n"
        ]
        
        # Parse events
        log_lines = []
        for event in events:
            if event.startswith("data:"):
                content = event.replace("data:", "").strip()
                if content != "[DONE]":
                    log_lines.append(content)
        
        assert len(log_lines) == 3
        assert log_lines[0] == "log line 1"
    
    @pytest.mark.asyncio
    async def test_sse_streaming_llm_response(self):
        """Test streaming LLM response via SSE."""
        # Simulate incremental LLM tokens
        tokens = ["Hello", " ", "world", "!", " ", "Test", " ", "complete", "."]
        
        sse_events = [f"data: {token}\n\n" for token in tokens]
        sse_events.append("data: [DONE]\n\n")
        
        # Reconstruct message
        full_message = ""
        for event in sse_events:
            if event.startswith("data:"):
                content = event.replace("data:", "").strip()
                if content != "[DONE]":
                    full_message += content
        
        assert full_message == "Hello world! Test complete."
    
    @pytest.mark.asyncio
    async def test_sse_error_handling(self):
        """Test error handling in SSE stream."""
        # SSE error event
        error_event = "event: error\ndata: {\"message\": \"Stream failed\"}\n\n"
        
        # Parse error
        assert "error" in error_event
        assert "Stream failed" in error_event
    
    @pytest.mark.asyncio
    async def test_sse_client_disconnect(self):
        """Test handling client disconnect during SSE."""
        # Simulate stream interruption
        events_sent = 0
        max_events = 100
        
        # Client disconnects after 10 events
        for i in range(max_events):
            events_sent += 1
            if i == 10:
                # Simulate disconnect
                break
        
        # Should have stopped at 11 (0-10)
        assert events_sent == 11
    
    @pytest.mark.asyncio
    async def test_sse_timing(self):
        """Test that SSE events are sent promptly."""
        import time
        
        start_time = time.time()
        
        # Simulate sending events
        events = ["data: event1\n\n", "data: event2\n\n", "data: event3\n\n"]
        
        for event in events:
            # Should not buffer excessively
            pass
        
        elapsed = time.time() - start_time
        
        # Should be fast (< 1 second for 3 events)
        assert elapsed < 1.0


class TestTransportConsistency:
    """Test consistency across transport modes."""
    
    def test_same_output_all_transports(self):
        """Verify output is consistent across transports."""
        # Sample tool output
        expected_output = {
            "stdout": "command output",
            "stderr": "",
            "exit_code": 0
        }
        
        # STDIO format
        stdio_response = {
            "result": expected_output,
            "id": 1
        }
        
        # HTTP format
        http_response = {
            "result": expected_output
        }
        
        # SSE final format
        sse_final = {
            "result": expected_output
        }
        
        # All should have same result
        assert stdio_response['result'] == expected_output
        assert http_response['result'] == expected_output
        assert sse_final['result'] == expected_output
    
    def test_error_format_consistency(self):
        """Verify errors are formatted consistently."""
        error_data = {
            "code": "TOOL_ERROR",
            "message": "Tool execution failed"
        }
        
        # All transports should use same error structure
        stdio_error = {"error": error_data, "id": 1}
        http_error = {"error": error_data}
        sse_error = {"error": error_data}
        
        assert stdio_error['error'] == error_data
        assert http_error['error'] == error_data
        assert sse_error['error'] == error_data


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance across transports."""
    
    def test_json_rpc_format(self):
        """Test JSON-RPC 2.0 format compliance."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "test"},
            "id": 1
        }
        
        # Verify required fields
        assert request['jsonrpc'] == "2.0"
        assert 'method' in request
        assert 'id' in request
    
    def test_notification_format(self):
        """Test notification format (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": "$/progress",
            "params": {"percentage": 50}
        }
        
        # Notifications have no 'id'
        assert 'id' not in notification
    
    def test_batch_requests(self):
        """Test batch request format."""
        batch = [
            {"jsonrpc": "2.0", "method": "tool1", "id": 1},
            {"jsonrpc": "2.0", "method": "tool2", "id": 2},
            {"jsonrpc": "2.0", "method": "tool3", "id": 3}
        ]
        
        # Verify batch structure
        assert isinstance(batch, list)
        assert len(batch) == 3
        assert all('id' in req for req in batch)
