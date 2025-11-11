# Orbit-MCP Test Suite

Comprehensive testing for Orbit-MCP DevOps automation platform.

## Overview

This test suite covers:
- **Unit Tests**: Fast, isolated tests with mocked dependencies
- **Integration Tests**: Tests with real external services (SSH, Docker, K8s)
- **LLM Tests**: Tests for AI/LLM integrations (mocked + real API)
- **Transport Tests**: Tests for STDIO, HTTP, and SSE transports
- **Cursor Integration**: Tests for Cursor IDE + MDC rules
- **Security Tests**: Command injection, credential handling
- **Performance Tests**: Response times, throughput

## Quick Start

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all unit tests (fast)
pytest tests/ -m "not integration and not llm and not slow"

# Run all tests including integration
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Run Specific Test Suites

```bash
# SSH tests only
pytest tests/test_ssh.py -v

# LLM tests only
pytest tests/test_llm.py -v

# Integration tests only
pytest tests/ -m integration

# Cursor integration
pytest tests/test_cursor_integration.py -v
```

## Test Organization

```
tests/
??? __init__.py
??? conftest.py                      # Shared fixtures and configuration
??? test_ssh.py                      # SSH tool tests
??? test_docker.py                   # Docker tool tests (TODO)
??? test_k8s.py                      # Kubernetes tool tests (TODO)
??? test_llm.py                      # LLM integration tests
??? test_transport.py                # Transport mode tests
??? test_cursor_integration.py       # Cursor + MDC tests
??? data/                            # Test data files
    ??? sample_logs/
    ??? mdc_rules/
    ??? configs/
```

## Test Categories

### Unit Tests (Fast, No External Dependencies)

```bash
pytest tests/ -m "not integration and not llm"
```

**Features:**
- All external services mocked
- Fast execution (< 1 minute)
- No API keys needed
- Run on every commit

**Coverage:**
- Function logic
- Error handling
- Input validation
- Output formatting

### Integration Tests (Requires External Services)

```bash
# Requires Docker
pytest tests/ -m "integration and docker"

# Requires Kubernetes (kind)
pytest tests/ -m "integration and k8s"

# Requires SSH server
pytest tests/ -m "integration and ssh"
```

**Setup:**

1. **Docker**: Install Docker Desktop or Docker Engine
2. **Kubernetes**: Install kind
   ```bash
   # Install kind
   curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
   chmod +x ./kind
   sudo mv ./kind /usr/local/bin/kind
   
   # Create test cluster
   kind create cluster --name orbit-test
   ```
3. **SSH**: Test server started automatically via Docker

### LLM Integration Tests

```bash
# Mock LLM tests (no API keys)
pytest tests/test_llm.py -m "not llm"

# Real API tests (requires keys)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
pytest tests/test_llm.py -m llm
```

**Cost Management:**
- LLM tests are marked and skipped by default
- Run only when API keys are set
- Use cheap models (gpt-3.5-turbo, claude-haiku)
- Typical cost: < $0.10 per full run

### Transport Tests

```bash
pytest tests/test_transport.py -v
```

Tests all three transport modes:
- STDIO (terminal)
- HTTP (REST API)
- SSE (Server-Sent Events for streaming)

### Cursor Integration Tests

```bash
pytest tests/test_cursor_integration.py -v
```

Tests:
- MDC rules loading and enforcement
- Tool orchestration and chaining
- Multi-turn conversations
- Streaming responses
- Error handling in Cursor UI

## Running Tests Locally

### Minimal Setup (Unit Tests Only)

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run unit tests
pytest tests/ -m "not integration and not llm and not slow"
```

### Full Setup (All Tests)

```bash
# 1. Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 2. Set up Docker (if not installed)
# See: https://docs.docker.com/get-docker/

# 3. Set up kind for Kubernetes tests
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
kind create cluster --name orbit-test

# 4. (Optional) Set up LLM API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# 5. Run all tests
pytest tests/ -v
```

### With Ollama (Local LLM, Free)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama2

# Run LLM tests with local model
pytest tests/test_llm.py -k ollama -v
```

## CI/CD Integration

Tests run automatically in GitHub Actions:

### On Every Push/PR:
- Linting (flake8, black, mypy)
- Unit tests (all Python versions)
- Docker integration tests
- Kubernetes integration tests
- Transport tests
- Cursor integration tests

### Nightly (Scheduled):
- All above tests
- LLM integration tests (with real APIs)
- Performance tests
- Security scans

### Configuration

See `.github/workflows/test.yml` for full CI configuration.

## Writing New Tests

### Test Structure

```python
# tests/test_new_feature.py

import pytest
from unittest.mock import MagicMock

class TestNewFeature:
    """Test suite for new feature."""
    
    def test_basic_functionality(self):
        """Test basic case."""
        # Arrange
        input_data = {"key": "value"}
        
        # Act
        result = new_feature_function(input_data)
        
        # Assert
        assert result['status'] == 'success'
    
    def test_error_handling(self):
        """Test error cases."""
        with pytest.raises(ValueError):
            new_feature_function(invalid_input)
    
    @pytest.mark.integration
    def test_with_real_service(self):
        """Integration test with real service."""
        # This will only run with -m integration
        pass
```

### Best Practices

1. **Use descriptive test names**
   ```python
   # Good
   def test_ssh_connection_timeout_returns_error(self):
   
   # Bad
   def test_ssh_1(self):
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert)
   ```python
   def test_example(self):
       # Arrange
       setup = create_test_data()
       
       # Act
       result = function_under_test(setup)
       
       # Assert
       assert result == expected
   ```

3. **Use fixtures for common setup**
   ```python
   @pytest.fixture
   def sample_data(self):
       return {"test": "data"}
   
   def test_with_fixture(self, sample_data):
       result = process(sample_data)
       assert result is not None
   ```

4. **Mark tests appropriately**
   ```python
   @pytest.mark.integration
   @pytest.mark.slow
   def test_expensive_operation(self):
       pass
   ```

5. **Mock external dependencies**
   ```python
   @patch('module.external_api')
   def test_with_mock(self, mock_api):
       mock_api.return_value = {"mocked": "data"}
       # Test code
   ```

## Test Markers

Use markers to categorize tests:

```bash
# Run only fast tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run SSH tests
pytest -m ssh

# Run everything except LLM tests
pytest -m "not llm"
```

Available markers:
- `integration` - Requires external services
- `llm` - Requires LLM API keys
- `slow` - Takes > 5 seconds
- `ssh` - SSH-specific
- `k8s` - Kubernetes-specific
- `docker` - Docker-specific
- `security` - Security tests
- `performance` - Performance tests

## Debugging Tests

### Run with verbose output

```bash
pytest tests/test_ssh.py -vv
```

### Show print statements

```bash
pytest tests/test_ssh.py -s
```

### Run specific test

```bash
pytest tests/test_ssh.py::TestSSHToolUnit::test_ssh_execute_success -v
```

### Drop into debugger on failure

```bash
pytest tests/ --pdb
```

### Show locals on failure

```bash
pytest tests/ -l
```

## Coverage

### Generate coverage report

```bash
pytest tests/ --cov=src --cov-report=html
```

### View HTML report

```bash
# Report generated in: htmlcov/index.html
open htmlcov/index.html
```

### Coverage requirements

- Target: 80% overall coverage
- Critical paths: 100% coverage
- New code: Must include tests

## Performance Testing

### Run performance tests

```bash
pytest tests/ -m performance --durations=10
```

### Benchmark specific function

```python
def test_performance(benchmark):
    result = benchmark(function_to_test, arg1, arg2)
    assert result is not None
```

## Troubleshooting

### Tests hang or timeout

```bash
# Set shorter timeout
pytest tests/ --timeout=30
```

### Docker tests fail

```bash
# Check Docker is running
docker ps

# Check test containers
docker ps -a | grep orbit-test
```

### Kubernetes tests fail

```bash
# Check kind cluster
kind get clusters

# Check cluster status
kubectl cluster-info --context kind-orbit-test
```

### LLM tests fail

```bash
# Verify API keys
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Test API connectivity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure tests pass locally
3. Run linting: `flake8 src/ tests/`
4. Check formatting: `black --check src/ tests/`
5. Update test documentation if needed
6. CI will run full test suite on PR

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [MCP Protocol Spec](https://modelcontextprotocol.io/)
- [Orbit-MCP Documentation Hub](../doc-hub.md)

## Support

For test-related issues:
- Check this README first
- Review test output and logs
- Open an issue with:
  - Test command used
  - Full error output
  - Environment details (OS, Python version, etc.)
