#!/usr/bin/env python3
"""Setup script for MCP Server."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-server",
    version="0.1.0",
    author="DevOps Team",
    description="Multi-Cloud Platform Server - Unified environment management tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "paramiko>=3.0.0",
        "docker>=6.0.0",
        "kubernetes>=25.0.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "cryptography>=41.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp=mcp.cli:main",
            "mcp-server=mcp.mcp_main:main",
        ],
    },
)
