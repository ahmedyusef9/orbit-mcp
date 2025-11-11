"""Pytest configuration and shared fixtures for Orbit-MCP tests."""

import os
import tempfile
import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock
import yaml

# Test environment markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers", "llm: mark test as requiring LLM API (requires API keys)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )
    config.addinivalue_line(
        "markers", "ssh: mark test as requiring SSH setup"
    )
    config.addinivalue_line(
        "markers", "k8s: mark test as requiring Kubernetes"
    )
    config.addinivalue_line(
        "markers", "docker: mark test as requiring Docker"
    )


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / '.orbit'
        config_dir.mkdir(parents=True)
        yield config_dir


@pytest.fixture
def sample_config():
    """Provide sample Orbit-MCP configuration."""
    return {
        'ssh': {
            'servers': {
                'test-server': {
                    'host': '127.0.0.1',
                    'port': 2222,
                    'username': 'testuser',
                    'key_file': '/tmp/test_key'
                }
            }
        },
        'docker': {
            'hosts': {
                'local': {
                    'type': 'local',
                    'socket': 'unix:///var/run/docker.sock'
                }
            }
        },
        'kubernetes': {
            'clusters': {
                'test-k8s': {
                    'kubeconfig': '/tmp/test_kubeconfig',
                    'context': 'test-context',
                    'namespace': 'default'
                }
            }
        },
        'llm': {
            'default_provider': 'mock',
            'providers': {
                'mock': {
                    'enabled': True,
                    'model': 'mock-model'
                }
            },
            'cost_control': {
                'daily_budget': 10.0,
                'monthly_budget': 200.0
            }
        }
    }


@pytest.fixture
def config_file(temp_config_dir, sample_config):
    """Create a config file for testing."""
    config_path = temp_config_dir / 'config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f)
    return config_path


@pytest.fixture
def mock_ssh_manager():
    """Mock SSH manager for unit tests."""
    mock = MagicMock()
    mock.execute_command.return_value = {
        'stdout': 'command output',
        'stderr': '',
        'exit_code': 0
    }
    return mock


@pytest.fixture
def mock_docker_manager():
    """Mock Docker manager for unit tests."""
    mock = MagicMock()
    mock.list_containers.return_value = [
        {'id': 'abc123', 'name': 'test-container', 'status': 'running'}
    ]
    mock.get_logs.return_value = 'container log output'
    return mock


@pytest.fixture
def mock_k8s_manager():
    """Mock Kubernetes manager for unit tests."""
    mock = MagicMock()
    mock.list_pods.return_value = [
        {
            'name': 'test-pod',
            'namespace': 'default',
            'status': 'Running',
            'ready': '1/1'
        }
    ]
    return mock


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for unit tests."""
    mock = MagicMock()
    
    # Mock generate method
    async def mock_generate(prompt, **kwargs):
        from src.mcp.llm.providers import LLMResponse
        return LLMResponse(
            content="This is a mock LLM response",
            model="mock-model",
            tokens_used=100,
            cost=0.001
        )
    
    mock.generate = mock_generate
    
    # Mock streaming
    async def mock_generate_stream(prompt, **kwargs):
        chunks = ["This ", "is ", "a ", "mock ", "response"]
        for chunk in chunks:
            yield chunk
    
    mock.generate_stream = mock_generate_stream
    
    return mock


@pytest.fixture
def sample_log_file(tmp_path):
    """Create a sample log file for testing."""
    log_file = tmp_path / "test.log"
    log_content = """
2024-01-15 10:00:01 INFO Starting application
2024-01-15 10:00:02 INFO Connecting to database
2024-01-15 10:00:03 ERROR Connection failed: timeout
2024-01-15 10:00:04 WARN Retrying connection
2024-01-15 10:00:05 INFO Connection established
2024-01-15 10:00:06 ERROR NullPointerException in module X
2024-01-15 10:00:07 ERROR Stack trace follows...
2024-01-15 10:00:08 INFO Recovering from error
2024-01-15 10:00:09 WARN Performance degraded
2024-01-15 10:00:10 INFO Application running normally
"""
    log_file.write_text(log_content.strip())
    return log_file


@pytest.fixture
def sample_mdc_rules(tmp_path):
    """Create sample MDC rules for Cursor integration tests."""
    rules_dir = tmp_path / '.cursor' / 'rules'
    rules_dir.mkdir(parents=True)
    
    rule_file = rules_dir / 'devops.mdc'
    rule_content = """
# DevOps Safety Rules

## Command Execution Safety
- Never execute destructive commands without confirmation
- Always validate input before SSH execution
- Require explicit user approval for:
  - Service restarts
  - Data deletion
  - Configuration changes

## Response Formatting
- Format all commands in backticks
- Use structured output for technical data
- Provide clear error messages
- Always explain what actions were taken
"""
    rule_file.write_text(rule_content)
    return rules_dir


# Skip conditions for integration tests
def skip_if_no_api_key(key_name: str):
    """Skip test if API key not available."""
    return pytest.mark.skipif(
        not os.getenv(key_name),
        reason=f"{key_name} not set - skipping API integration test"
    )


def skip_if_no_docker():
    """Skip test if Docker not available."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return pytest.mark.skipif(False, reason="")
    except Exception:
        return pytest.mark.skipif(True, reason="Docker not available")


def skip_if_no_k8s():
    """Skip test if Kubernetes not available."""
    return pytest.mark.skipif(
        not os.path.exists(os.path.expanduser('~/.kube/config')),
        reason="Kubernetes config not found"
    )


# Pytest fixtures for external services
@pytest.fixture(scope="session")
def ssh_test_server():
    """
    Start SSH test server container (if Docker available).
    
    This fixture starts a lightweight SSH server for integration tests.
    Uses linuxserver/openssh-server image.
    """
    try:
        import docker
        client = docker.from_env()
        
        # Start SSH server container
        container = client.containers.run(
            "linuxserver/openssh-server:latest",
            detach=True,
            ports={'2222/tcp': 2222},
            environment={
                'PUID': '1000',
                'PGID': '1000',
                'TZ': 'UTC',
                'PASSWORD_ACCESS': 'true',
                'USER_PASSWORD': 'testpassword',
                'USER_NAME': 'testuser'
            },
            name='orbit-mcp-ssh-test'
        )
        
        # Wait for server to be ready
        import time
        time.sleep(5)
        
        yield {
            'host': '127.0.0.1',
            'port': 2222,
            'username': 'testuser',
            'password': 'testpassword'
        }
        
        # Cleanup
        container.stop()
        container.remove()
        
    except Exception as e:
        pytest.skip(f"Could not start SSH test server: {e}")


@pytest.fixture(scope="session")
def k8s_test_cluster():
    """
    Start kind (Kubernetes in Docker) test cluster.
    
    This fixture creates a minimal Kubernetes cluster for integration tests.
    Requires kind to be installed.
    """
    import subprocess
    import tempfile
    
    cluster_name = "orbit-mcp-test"
    
    try:
        # Check if kind is available
        subprocess.run(['kind', 'version'], check=True, capture_output=True)
        
        # Create cluster
        subprocess.run(
            ['kind', 'create', 'cluster', '--name', cluster_name],
            check=True,
            capture_output=True
        )
        
        # Get kubeconfig
        result = subprocess.run(
            ['kind', 'get', 'kubeconfig', '--name', cluster_name],
            check=True,
            capture_output=True,
            text=True
        )
        
        kubeconfig_path = tempfile.mktemp(suffix='.yaml')
        with open(kubeconfig_path, 'w') as f:
            f.write(result.stdout)
        
        yield {
            'kubeconfig': kubeconfig_path,
            'cluster_name': cluster_name
        }
        
        # Cleanup
        subprocess.run(
            ['kind', 'delete', 'cluster', '--name', cluster_name],
            check=False
        )
        os.remove(kubeconfig_path)
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("kind not available - skipping K8s integration tests")


@pytest.fixture
def env_vars():
    """Fixture to manage environment variables in tests."""
    original_env = os.environ.copy()
    
    yield os.environ
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_openai_api(monkeypatch):
    """Mock OpenAI API responses."""
    class MockResponse:
        def __init__(self):
            self.choices = [
                type('Choice', (), {
                    'message': type('Message', (), {
                        'content': 'Mock OpenAI response'
                    })(),
                    'finish_reason': 'stop'
                })()
            ]
            self.usage = type('Usage', (), {
                'total_tokens': 100,
                'prompt_tokens': 50,
                'completion_tokens': 50
            })()
    
    def mock_create(*args, **kwargs):
        return MockResponse()
    
    # This would need the actual openai module path
    # monkeypatch.setattr('openai.ChatCompletion.create', mock_create)
    
    return mock_create


@pytest.fixture
def mock_anthropic_api(monkeypatch):
    """Mock Anthropic API responses."""
    class MockMessage:
        def __init__(self):
            self.content = [type('Content', (), {'text': 'Mock Claude response'})()]
            self.stop_reason = 'end_turn'
            self.usage = type('Usage', (), {
                'input_tokens': 50,
                'output_tokens': 50
            })()
    
    def mock_create(*args, **kwargs):
        return MockMessage()
    
    return mock_create


# Assertion helpers
def assert_valid_mcp_response(response: Dict[str, Any]):
    """Assert that response follows MCP protocol structure."""
    assert isinstance(response, dict), "Response must be a dictionary"
    
    # Check for either result or error
    assert 'result' in response or 'error' in response, \
        "Response must contain 'result' or 'error'"
    
    if 'error' in response:
        error = response['error']
        assert 'code' in error, "Error must have a code"
        assert 'message' in error, "Error must have a message"


def assert_valid_tool_output(output: Dict[str, Any], tool_name: str):
    """Assert that tool output is valid."""
    assert isinstance(output, dict), f"{tool_name} output must be dict"
    
    # Check for common fields
    if 'error' not in output:
        assert 'data' in output or 'result' in output, \
            f"{tool_name} must return data or result"


# Performance helpers
@pytest.fixture
def performance_threshold():
    """Performance thresholds for various operations."""
    return {
        'ssh_exec': 5.0,      # seconds
        'docker_logs': 3.0,
        'k8s_get': 5.0,
        'llm_generate': 30.0,
        'logs_tail': 2.0
    }


def measure_time(func):
    """Decorator to measure function execution time."""
    import time
    from functools import wraps
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        result._execution_time = elapsed
        return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        if isinstance(result, dict):
            result['_execution_time'] = elapsed
        return result
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
