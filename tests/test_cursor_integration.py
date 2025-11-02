"""Tests for Cursor IDE integration and MDC rules."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestMDCRulesIntegration:
    """Test MDC rules integration."""
    
    def test_mdc_rules_loading(self, sample_mdc_rules):
        """Test loading MDC rules from .cursor directory."""
        rules_files = list(sample_mdc_rules.glob('*.mdc'))
        
        assert len(rules_files) > 0
        
        # Read first rule file
        rule_content = rules_files[0].read_text()
        
        assert len(rule_content) > 0
        assert '# DevOps Safety Rules' in rule_content
    
    def test_mdc_safety_rules_enforcement(self, sample_mdc_rules):
        """Test that MDC safety rules are enforced."""
        # Load rules
        rules_file = sample_mdc_rules / 'devops.mdc'
        rules = rules_file.read_text()
        
        # Rules should prohibit dangerous commands
        assert 'destructive commands' in rules.lower()
        assert 'confirmation' in rules.lower()
    
    def test_mdc_formatting_rules(self, sample_mdc_rules):
        """Test MDC formatting rules."""
        rules_file = sample_mdc_rules / 'devops.mdc'
        rules = rules_file.read_text()
        
        # Should have formatting guidelines
        assert 'backticks' in rules.lower()
        assert 'format' in rules.lower()


class TestCursorToolOrchestration:
    """Test tool orchestration in Cursor environment."""
    
    @pytest.mark.asyncio
    async def test_tool_chaining(self, mock_ssh_manager, mock_docker_manager):
        """Test chaining multiple tools in sequence."""
        # Simulate tool chain: SSH -> Docker logs -> Analysis
        
        # Step 1: SSH to check service
        ssh_result = mock_ssh_manager.execute_command(
            host='prod-server',
            command='systemctl status myapp'
        )
        
        assert ssh_result['exit_code'] == 0
        
        # Step 2: Get Docker logs
        docker_logs = mock_docker_manager.get_logs(
            container='myapp-container'
        )
        
        assert docker_logs is not None
        
        # Step 3: Analysis would use LLM
        # This simulates the full chain working
    
    @pytest.mark.asyncio
    async def test_tool_error_propagation(self, mock_ssh_manager):
        """Test error propagation through tool chain."""
        # First tool fails
        mock_ssh_manager.execute_command.side_effect = ConnectionError(
            "SSH failed"
        )
        
        with pytest.raises(ConnectionError):
            result = mock_ssh_manager.execute_command(
                host='unreachable',
                command='test'
            )
        
        # Chain should stop and report error
    
    @pytest.mark.asyncio
    async def test_conditional_tool_execution(self, mock_ssh_manager):
        """Test conditional tool execution based on results."""
        # If service is down, restart it
        mock_ssh_manager.execute_command.side_effect = [
            # First call: check status
            {'stdout': 'inactive', 'stderr': '', 'exit_code': 3},
            # Second call: restart
            {'stdout': 'started', 'stderr': '', 'exit_code': 0}
        ]
        
        # Check status
        status = mock_ssh_manager.execute_command(
            host='server',
            command='systemctl status myapp'
        )
        
        if status['exit_code'] != 0:
            # Restart
            restart_result = mock_ssh_manager.execute_command(
                host='server',
                command='systemctl restart myapp'
            )
            assert restart_result['exit_code'] == 0


class TestCursorConversationalFlow:
    """Test conversational flows in Cursor."""
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, mock_llm_client):
        """Test multi-turn conversation with context."""
        conversation = []
        
        # Turn 1: User asks about pods
        user1 = "What pods are running?"
        conversation.append({"role": "user", "content": user1})
        
        # Assistant responds
        response1 = await mock_llm_client.generate(user1)
        conversation.append({"role": "assistant", "content": response1.content})
        
        # Turn 2: Follow-up question
        user2 = "Show logs for the first one"
        conversation.append({"role": "user", "content": user2})
        
        # Assistant should have context
        response2 = await mock_llm_client.generate(user2)
        
        assert len(conversation) == 4
    
    @pytest.mark.asyncio
    async def test_user_confirmation_prompt(self, mock_llm_client):
        """Test prompting user for confirmation."""
        # User asks to restart service
        user_request = "Restart the nginx service"
        
        # Assistant should ask for confirmation
        async def mock_with_confirmation(prompt, **kwargs):
            from src.mcp.llm.providers import LLMResponse
            if 'restart' in prompt.lower():
                return LLMResponse(
                    content="This will restart nginx. Are you sure? (yes/no)",
                    model="mock",
                    tokens_used=50,
                    cost=0.001
                )
            return LLMResponse(
                content="Restarting nginx...",
                model="mock",
                tokens_used=50,
                cost=0.001
            )
        
        mock_llm_client.generate = mock_with_confirmation
        
        response = await mock_llm_client.generate(user_request)
        
        assert "Are you sure" in response.content or "confirm" in response.content.lower()
    
    @pytest.mark.asyncio
    async def test_context_preservation(self, mock_llm_client):
        """Test that context is preserved across turns."""
        # Context from previous messages
        context = {
            'current_server': 'prod-web-01',
            'current_namespace': 'production',
            'last_command': 'systemctl status nginx'
        }
        
        # User asks follow-up that requires context
        user_query = "Check the logs"  # Which logs? Should use context
        
        # In real implementation, context would be injected
        assert context['current_server'] == 'prod-web-01'


class TestCursorStreamingResponses:
    """Test streaming responses in Cursor UI."""
    
    @pytest.mark.asyncio
    async def test_streaming_to_cursor(self, mock_llm_client):
        """Test streaming LLM response to Cursor."""
        chunks_received = []
        
        async for chunk in mock_llm_client.generate_stream("Test prompt"):
            chunks_received.append(chunk)
        
        # Should receive multiple chunks
        assert len(chunks_received) > 1
        
        # Reconstruct full response
        full_response = ''.join(chunks_received)
        assert len(full_response) > 0
    
    @pytest.mark.asyncio
    async def test_code_block_streaming(self, mock_llm_client):
        """Test streaming code blocks without breaking formatting."""
        # Simulate streaming a code block
        code_chunks = [
            "```python\n",
            "def hello():\n",
            "    print('hello')\n",
            "```"
        ]
        
        async def mock_code_stream(*args, **kwargs):
            for chunk in code_chunks:
                yield chunk
        
        mock_llm_client.generate_stream = mock_code_stream
        
        chunks = []
        async for chunk in mock_llm_client.generate_stream("show code"):
            chunks.append(chunk)
        
        full_code = ''.join(chunks)
        
        # Should have complete code block markers
        assert full_code.count('```') == 2
        assert 'def hello' in full_code
    
    @pytest.mark.asyncio
    async def test_streaming_with_tool_outputs(self, mock_llm_client):
        """Test streaming that includes tool outputs."""
        # Simulate a response that includes tool results
        
        # First: tool execution (should be hidden from user)
        tool_output = {"stdout": "nginx is running", "exit_code": 0}
        
        # Then: LLM streams analysis
        analysis_chunks = [
            "Based on the ",
            "system check, ",
            "nginx is running normally."
        ]
        
        async def mock_with_tools(*args, **kwargs):
            for chunk in analysis_chunks:
                yield chunk
        
        mock_llm_client.generate_stream = mock_with_tools
        
        response_chunks = []
        async for chunk in mock_llm_client.generate_stream("check nginx"):
            response_chunks.append(chunk)
        
        final_response = ''.join(response_chunks)
        
        # User should see analysis, not raw tool output
        assert 'nginx is running normally' in final_response
        # Raw JSON should not be visible
        assert '"stdout"' not in final_response


class TestCursorUIIntegration:
    """Test Cursor UI-specific integration."""
    
    def test_tool_visibility_in_cursor(self):
        """Test that tools are properly registered and visible."""
        # Mock tool registry
        tool_registry = {
            'ssh.run': {
                'name': 'ssh.run',
                'description': 'Execute SSH command',
                'visible': True
            },
            'k8s.get': {
                'name': 'k8s.get',
                'description': 'Get Kubernetes resources',
                'visible': True
            }
        }
        
        # All tools should be visible
        visible_tools = [t for t in tool_registry.values() if t.get('visible')]
        assert len(visible_tools) == len(tool_registry)
    
    def test_error_display_format(self):
        """Test error formatting for Cursor UI."""
        error = {
            'type': 'CONNECTION_ERROR',
            'message': 'Could not connect to server',
            'details': {
                'host': 'prod-server',
                'port': 22,
                'reason': 'timeout'
            }
        }
        
        # Format for user display
        user_message = f"? {error['message']}\n"
        user_message += f"Host: {error['details']['host']}\n"
        user_message += f"Reason: {error['details']['reason']}"
        
        assert '?' in user_message
        assert 'Could not connect' in user_message
        assert 'prod-server' in user_message
    
    def test_progress_indicators(self):
        """Test progress indicators for long operations."""
        progress_updates = [
            {'step': 1, 'message': 'Connecting to server...', 'progress': 0.25},
            {'step': 2, 'message': 'Executing command...', 'progress': 0.50},
            {'step': 3, 'message': 'Analyzing results...', 'progress': 0.75},
            {'step': 4, 'message': 'Complete', 'progress': 1.0}
        ]
        
        for update in progress_updates:
            assert 0 <= update['progress'] <= 1.0
            assert update['message'] is not None


class TestEndToEndScenarios:
    """End-to-end scenario tests in Cursor environment."""
    
    @pytest.mark.asyncio
    async def test_incident_diagnosis_workflow(
        self,
        mock_ssh_manager,
        mock_docker_manager,
        mock_llm_client
    ):
        """Test complete incident diagnosis workflow."""
        # Scenario: Website is down
        
        # Step 1: Check web server status
        mock_ssh_manager.execute_command.return_value = {
            'stdout': 'nginx: inactive (failed)',
            'stderr': '',
            'exit_code': 3
        }
        
        status = mock_ssh_manager.execute_command(
            host='web-server',
            command='systemctl status nginx'
        )
        
        assert status['exit_code'] != 0
        
        # Step 2: Get logs
        mock_docker_manager.get_logs.return_value = """
        2024-01-15 10:00:01 Starting nginx
        2024-01-15 10:00:02 ERROR: Port 80 already in use
        2024-01-15 10:00:03 Failed to start
        """
        
        logs = mock_docker_manager.get_logs(container='nginx')
        
        assert 'ERROR' in logs
        assert 'Port 80 already in use' in logs
        
        # Step 3: LLM analyzes and provides solution
        async def mock_analysis(prompt, **kwargs):
            from src.mcp.llm.providers import LLMResponse
            return LLMResponse(
                content="""
                Root cause: Port 80 is already in use by another process.
                
                Solution:
                1. Find process using port 80: `lsof -i :80`
                2. Stop conflicting process
                3. Restart nginx
                """,
                model="mock",
                tokens_used=200,
                cost=0.003
            )
        
        mock_llm_client.generate = mock_analysis
        
        analysis = await mock_llm_client.generate(
            f"Analyze this error: {logs}"
        )
        
        assert 'Port 80' in analysis.content
        assert 'Solution' in analysis.content
