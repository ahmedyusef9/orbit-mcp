# Contributing to MCP Server

Thank you for your interest in contributing to MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and professional in all interactions.

## How to Contribute

### Reporting Bugs

Before submitting a bug report:
1. Check the [existing issues](https://github.com/yourorg/mcp-server/issues) to avoid duplicates
2. Gather information about your environment (OS, Python version, etc.)
3. Try to reproduce the issue with the latest version

When submitting a bug report, include:
- Clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages or logs
- Environment details (OS, Python version, dependency versions)

### Suggesting Features

We welcome feature suggestions! Please:
1. Check existing issues and the roadmap
2. Clearly describe the use case
3. Explain how it would benefit users
4. Consider implementation challenges

### Pull Requests

#### Before Starting

1. Check existing pull requests
2. For major changes, open an issue first to discuss
3. Fork the repository
4. Create a branch from `main`

#### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/mcp-server.git
cd mcp-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .
```

#### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write your code**
   - Follow the existing code style
   - Add docstrings to functions and classes
   - Keep functions focused and modular
   - Add type hints where appropriate

3. **Write tests**
   - Add unit tests for new functionality
   - Ensure existing tests still pass
   - Aim for good test coverage

4. **Update documentation**
   - Update README if needed
   - Add docstrings
   - Update relevant documentation files

5. **Test your changes**
   ```bash
   # Run tests
   pytest
   
   # Run with coverage
   pytest --cov=mcp --cov-report=html
   
   # Check code style
   black src/
   flake8 src/
   
   # Type checking
   mypy src/
   ```

#### Commit Guidelines

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add support for Azure VM SSH connections"
git commit -m "Fix timeout issue in Docker container logs"
git commit -m "Update security documentation"

# Bad
git commit -m "fixes"
git commit -m "update"
git commit -m "wip"
```

Follow conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

Example:
```bash
git commit -m "feat: add support for Docker Swarm"
git commit -m "fix: handle connection timeout gracefully"
git commit -m "docs: update Kubernetes examples"
```

#### Submitting Pull Request

1. **Push your changes**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create pull request**
   - Use a clear title
   - Describe what changed and why
   - Reference related issues
   - Add screenshots if relevant

3. **Pull request template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Code refactoring
   
   ## Testing
   Describe how you tested the changes
   
   ## Checklist
   - [ ] Tests pass locally
   - [ ] Added/updated tests
   - [ ] Updated documentation
   - [ ] Code follows style guidelines
   - [ ] No new warnings
   
   ## Related Issues
   Closes #123
   ```

4. **Code review**
   - Address reviewer feedback
   - Update PR as needed
   - Keep discussion professional

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Maximum line length: 100 characters
- Use meaningful variable names
- Add type hints to function signatures

### Code Formatting

```bash
# Format code
black src/

# Sort imports
isort src/

# Check style
flake8 src/
```

### Example Code Style

```python
"""Module for SSH connection management."""

import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class SSHManager:
    """Manages SSH connections and operations."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize SSH manager.
        
        Args:
            timeout: Connection timeout in seconds
        """
        self.timeout = timeout
        self.connections = {}
    
    def connect(
        self,
        host: str,
        user: str,
        port: int = 22,
        key_path: Optional[str] = None
    ) -> bool:
        """
        Establish SSH connection.
        
        Args:
            host: Remote host address
            user: SSH username
            port: SSH port
            key_path: Path to private key
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Implementation
            logger.info(f"Connected to {user}@{host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Cannot connect to {host}: {e}")
```

## Testing Guidelines

### Writing Tests

```python
import pytest
from mcp.config import ConfigManager


def test_add_ssh_server():
    """Test adding SSH server configuration."""
    config = ConfigManager()
    config.add_ssh_server("test", "host", "user")
    
    server = config.get_ssh_server("test")
    assert server is not None
    assert server["host"] == "host"


@pytest.fixture
def temp_config():
    """Provide temporary configuration."""
    # Setup
    config = ConfigManager("/tmp/test-config.yaml")
    yield config
    # Teardown
    config.cleanup()
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::test_add_ssh_server

# Run with coverage
pytest --cov=mcp --cov-report=html

# Run with verbose output
pytest -v
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    More detailed description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

### Documentation Files

- Update README.md for user-facing changes
- Update docs/ files for detailed documentation
- Add examples to docs/examples.md
- Update CHANGELOG.md

## Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email security@yourcompany.com
2. Include detailed description
3. Provide steps to reproduce
4. Wait for response before disclosure

### Security Guidelines

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Validate all user inputs
- Use parameterized queries
- Follow principle of least privilege
- Keep dependencies updated

## Release Process

1. Update version in `setup.py` and `__init__.py`
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create pull request
6. After merge, tag release
7. Publish to PyPI (maintainers only)

## Getting Help

- Open an issue for questions
- Join discussions
- Check documentation
- Contact maintainers

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

Thank you for contributing to MCP Server! ??
