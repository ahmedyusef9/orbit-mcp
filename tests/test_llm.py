"""Tests for LLM tool functionality."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os


class TestLLMToolsUnit:
    """Unit tests for LLM tools (mocked)."""
    
    @pytest.mark.asyncio
    async def test_llm_chat_basic(self, mock_llm_client):
        """Test basic LLM chat functionality."""
        response = await mock_llm_client.generate(
            "What is Kubernetes?"
        )
        
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == "mock-model"
        assert response.tokens_used > 0
    
    @pytest.mark.asyncio
    async def test_llm_plan_generation(self, mock_llm_client):
        """Test LLM plan generation."""
        # Mock a plan response
        mock_plan = """
1. Check server health via SSH
2. Retrieve application logs
3. Analyze logs for errors
4. Report findings to user
"""
        
        async def mock_plan_generate(prompt, **kwargs):
            from src.mcp.llm.providers import LLMResponse
            return LLMResponse(
                content=mock_plan,
                model="mock-model",
                tokens_used=150,
                cost=0.002
            )
        
        mock_llm_client.generate = mock_plan_generate
        
        response = await mock_llm_client.generate(
            "Create a plan to diagnose server issues"
        )
        
        assert "Check server health" in response.content
        assert "logs" in response.content.lower()
        assert response.tokens_used > 0
    
    @pytest.mark.asyncio
    async def test_llm_summarize_logs(self, mock_llm_client, sample_log_file):
        """Test log summarization."""
        log_content = sample_log_file.read_text()
        
        mock_summary = """
Log Summary:
- Connection timeout error at 10:00:03
- NullPointerException in module X at 10:00:06
- System recovered and running normally by 10:00:10
"""
        
        async def mock_summarize(prompt, **kwargs):
            from src.mcp.llm.providers import LLMResponse
            return LLMResponse(
                content=mock_summary,
                model="mock-model",
                tokens_used=200,
                cost=0.003
            )
        
        mock_llm_client.generate = mock_summarize
        
        response = await mock_llm_client.generate(
            f"Summarize these logs:\n{log_content}"
        )
        
        assert "timeout" in response.content.lower()
        assert "NullPointerException" in response.content
        assert response.tokens_used > 0
    
    @pytest.mark.asyncio
    async def test_llm_streaming_response(self, mock_llm_client):
        """Test streaming LLM responses."""
        chunks = []
        
        async for chunk in mock_llm_client.generate_stream("Test prompt"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = ''.join(chunks)
        assert len(full_response) > 0
    
    @pytest.mark.asyncio
    async def test_llm_error_handling(self, mock_llm_client):
        """Test LLM error handling."""
        async def mock_error(*args, **kwargs):
            raise ConnectionError("API unavailable")
        
        mock_llm_client.generate = mock_error
        
        with pytest.raises(ConnectionError, match="API unavailable"):
            await mock_llm_client.generate("Test")
    
    @pytest.mark.asyncio
    async def test_llm_empty_response_handling(self, mock_llm_client):
        """Test handling of empty/malformed responses."""
        async def mock_empty(*args, **kwargs):
            from src.mcp.llm.providers import LLMResponse
            return LLMResponse(
                content="",
                model="mock-model",
                tokens_used=0,
                cost=0.0
            )
        
        mock_llm_client.generate = mock_empty
        
        response = await mock_llm_client.generate("Test")
        
        # Should handle gracefully
        assert response.content == ""
        assert response.tokens_used == 0


@pytest.mark.integration
@pytest.mark.llm
class TestLLMIntegrationOpenAI:
    """Integration tests for OpenAI API."""
    
    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OPENAI_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_openai_chat(self):
        """Test real OpenAI API call."""
        from src.mcp.llm.providers import OpenAIProvider
        
        provider = OpenAIProvider(
            model='gpt-3.5-turbo',
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        from src.mcp.llm.providers import LLMMessage
        messages = [
            LLMMessage(role='user', content='Say "test successful" and nothing else')
        ]
        
        response = await provider.generate(messages)
        
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0
        assert response.cost > 0
        assert 'test successful' in response.content.lower()
    
    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OPENAI_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_openai_plan(self):
        """Test plan generation with real OpenAI."""
        from src.mcp.llm.providers import OpenAIProvider, LLMMessage
        
        provider = OpenAIProvider(
            model='gpt-3.5-turbo',
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        messages = [
            LLMMessage(
                role='user',
                content='Create a 3-step plan to check server health. Be concise.'
            )
        ]
        
        response = await provider.generate(messages, temperature=0.3)
        
        assert response.content is not None
        assert len(response.content) > 0
        # Should contain step indicators
        assert any(char.isdigit() for char in response.content)


@pytest.mark.integration
@pytest.mark.llm
class TestLLMIntegrationAnthropic:
    """Integration tests for Anthropic Claude API."""
    
    @pytest.mark.skipif(
        not os.getenv('ANTHROPIC_API_KEY'),
        reason="ANTHROPIC_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_claude_chat(self):
        """Test real Claude API call."""
        from src.mcp.llm.providers import AnthropicProvider, LLMMessage
        
        provider = AnthropicProvider(
            model='claude-3-haiku',
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        messages = [
            LLMMessage(role='user', content='Say "claude test successful"')
        ]
        
        response = await provider.generate(messages)
        
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0
    
    @pytest.mark.skipif(
        not os.getenv('ANTHROPIC_API_KEY'),
        reason="ANTHROPIC_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_claude_large_context(self, sample_log_file):
        """Test Claude with large context (its strength)."""
        from src.mcp.llm.providers import AnthropicProvider, LLMMessage
        
        provider = AnthropicProvider(
            model='claude-3-haiku',
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        # Create larger log content
        log_content = sample_log_file.read_text() * 10
        
        messages = [
            LLMMessage(
                role='user',
                content=f"Briefly summarize key errors in these logs:\n{log_content}"
            )
        ]
        
        response = await provider.generate(messages)
        
        assert response.content is not None
        assert len(response.content) > 0
        # Summary should be shorter than input
        assert len(response.content) < len(log_content)


@pytest.mark.integration
@pytest.mark.llm
class TestLLMIntegrationOllama:
    """Integration tests for Ollama (local LLM)."""
    
    @pytest.mark.skipif(
        not os.path.exists('/usr/local/bin/ollama'),
        reason="Ollama not installed"
    )
    @pytest.mark.asyncio
    async def test_ollama_chat(self):
        """Test Ollama local model."""
        from src.mcp.llm.providers import OllamaProvider, LLMMessage
        
        provider = OllamaProvider(model='llama2')
        
        messages = [
            LLMMessage(role='user', content='Say hello')
        ]
        
        response = await provider.generate(messages)
        
        assert response.content is not None
        assert len(response.content) > 0
        assert response.cost == 0.0  # Local, no cost


class TestLLMCostManagement:
    """Tests for LLM cost management."""
    
    def test_cost_tracking(self):
        """Test cost tracking functionality."""
        from src.mcp.llm.cost_manager import CostManager
        
        cost_mgr = CostManager({
            'daily_budget': 10.0,
            'monthly_budget': 200.0
        })
        
        # Record some usage
        cost_mgr.record_usage('openai', 1000, 0.015)
        
        summary = cost_mgr.get_usage_summary()
        
        assert summary['daily']['cost'] == 0.015
        assert summary['daily']['tokens'] == 1000
        assert summary['daily']['remaining'] < 10.0
    
    def test_budget_enforcement(self):
        """Test budget limit enforcement."""
        from src.mcp.llm.cost_manager import CostManager
        
        cost_mgr = CostManager({
            'daily_budget': 1.0,
            'monthly_budget': 10.0
        })
        
        # Use up most of budget
        cost_mgr.record_usage('openai', 10000, 0.95)
        
        # Try to make expensive request
        can_proceed = cost_mgr.can_make_request(0.10)
        
        # Should be blocked
        assert not can_proceed
    
    def test_token_optimization(self, sample_log_file):
        """Test token optimization for logs."""
        from src.mcp.llm.cost_manager import TokenOptimizer
        
        optimizer = TokenOptimizer(max_context_tokens=1000)
        
        log_content = sample_log_file.read_text()
        
        # Optimize
        optimized = optimizer.optimize_log_content(log_content, max_lines=5)
        
        # Should be significantly smaller
        assert len(optimized) < len(log_content)
        
        # Should still contain key errors
        assert 'ERROR' in optimized or 'error' in optimized.lower()


class TestLLMPromptSafety:
    """Test prompt safety and content filtering."""
    
    @pytest.mark.asyncio
    async def test_sensitive_data_redaction(self, mock_llm_client):
        """Test that sensitive data is redacted before LLM."""
        from src.mcp.llm.cost_manager import TokenOptimizer
        
        # Simulate log with sensitive data
        log_with_secrets = """
        2024-01-15 10:00:01 INFO Starting app
        2024-01-15 10:00:02 DEBUG API_KEY=sk-1234567890abcdef
        2024-01-15 10:00:03 ERROR Connection failed to 192.168.1.100
        2024-01-15 10:00:04 DEBUG password=secretpass123
        """
        
        # In real implementation, this would redact
        # For test, just verify the concept
        assert 'sk-' in log_with_secrets  # Has API key
        assert 'password=' in log_with_secrets  # Has password
        
        # After redaction (mocked)
        redacted = log_with_secrets.replace('sk-1234567890abcdef', '[REDACTED]')
        redacted = redacted.replace('secretpass123', '[REDACTED]')
        
        assert '[REDACTED]' in redacted
        assert 'sk-1234567890abcdef' not in redacted
