#!/usr/bin/env python3
"""MCP Server entry point."""

import asyncio
import logging
import argparse
import sys

from .mcp_server import MCPDevOpsServer
from .transports import run_stdio_server, run_http_server


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Log to stderr to avoid interfering with STDIO protocol
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )


def main():
    """Main entry point for MCP server."""
    parser = argparse.ArgumentParser(
        description='MCP DevOps Server - Model Context Protocol server for DevOps tools'
    )
    
    parser.add_argument(
        '--transport',
        choices=['stdio', 'http'],
        default='stdio',
        help='Transport type (default: stdio)'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host for HTTP transport (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=3000,
        help='Port for HTTP transport (default: 3000)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting MCP DevOps Server")
    
    # Create server
    try:
        server = MCPDevOpsServer(config_path=args.config)
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}", exc_info=True)
        sys.exit(1)
    
    # Run with selected transport
    try:
        if args.transport == 'stdio':
            logger.info("Using STDIO transport")
            asyncio.run(run_stdio_server(server))
        else:  # http
            logger.info(f"Using HTTP transport on {args.host}:{args.port}")
            asyncio.run(run_http_server(server, args.host, args.port))
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
