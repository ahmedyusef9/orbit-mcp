#!/bin/bash
# MCP Server Installation Script

set -e

echo "========================================="
echo "MCP Server Installation"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "? Error: Python 3.8 or higher is required"
    echo "   Current version: $python_version"
    exit 1
fi
echo "? Python version: $python_version"

# Check if virtual environment should be created
read -p "Create virtual environment? (recommended) [Y/n]: " create_venv
create_venv=${create_venv:-Y}

if [[ "$create_venv" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "? Virtual environment created and activated"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "? Dependencies installed"

# Install MCP Server
echo ""
echo "Installing MCP Server..."
pip install -e .
echo "? MCP Server installed"

# Verify installation
echo ""
echo "Verifying installation..."
if command -v mcp &> /dev/null; then
    echo "? MCP command available"
    mcp_version=$(python3 -c "import mcp; print(mcp.__version__)")
    echo "? Version: $mcp_version"
else
    echo "? Error: MCP command not found"
    exit 1
fi

# Initialize configuration
echo ""
read -p "Initialize MCP configuration? [Y/n]: " init_config
init_config=${init_config:-Y}

if [[ "$init_config" =~ ^[Yy]$ ]]; then
    echo "Initializing configuration..."
    mcp config init
    echo "? Configuration initialized at ~/.mcp/config.yaml"
fi

# Installation complete
echo ""
echo "========================================="
echo "? Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Add your first server:"
echo "     mcp config add-ssh my-server host.example.com user --key ~/.ssh/id_rsa"
echo ""
echo "  2. Test connection:"
echo "     mcp ssh exec my-server 'echo Hello from MCP!'"
echo ""
echo "  3. View help:"
echo "     mcp --help"
echo ""
echo "Documentation:"
echo "  - Quick Start: docs/quick-start.md"
echo "  - Configuration: docs/configuration.md"
echo "  - CLI Reference: docs/cli-reference.md"
echo ""

if [[ "$create_venv" =~ ^[Yy]$ ]]; then
    echo "Note: Remember to activate the virtual environment:"
    echo "  source venv/bin/activate"
    echo ""
fi

echo "Happy DevOps! ??"
