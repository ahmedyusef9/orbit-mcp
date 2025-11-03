#!/usr/bin/env python3
"""Ops MCP Server entry point."""

import asyncio
import logging
import argparse
import sys
from pathlib import Path

from .ops.ops_server import OpsMCPServer
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
    """Main entry point for Ops MCP Server."""
    parser = argparse.ArgumentParser(
        description='Ops MCP Server - Global DevOps operations server'
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
        default=3001,
        help='Port for HTTP transport (default: 3001)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file (default: OPS_CONFIG env or /etc/ops-mcp/config.yaml)'
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
    logger.info("Starting Ops MCP Server")
    
    # Create server
    import os
    config_path = None
    if args.config:
        config_path = Path(args.config)
    elif 'OPS_CONFIG' in os.environ:
        config_path = Path(os.environ['OPS_CONFIG'])
    
    try:
        server = OpsMCPServer(config_path=config_path)
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
    import os
    main()