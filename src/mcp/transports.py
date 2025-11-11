"""MCP Server transports - STDIO and HTTP+SSE."""

import sys
import logging
import asyncio
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """Base class for MCP transports."""
    
    @abstractmethod
    async def start(self):
        """Start the transport."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the transport."""
        pass


class StdioTransport(MCPTransport):
    """STDIO transport for MCP server."""
    
    def __init__(self, server):
        """
        Initialize STDIO transport.
        
        Args:
            server: MCPDevOpsServer instance
        """
        self.server = server
        self.running = False
    
    async def start(self):
        """Start reading from stdin and writing to stdout."""
        logger.info("Starting STDIO transport")
        self.running = True
        
        try:
            while self.running:
                # Read line from stdin
                try:
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, sys.stdin.readline
                    )
                    
                    if not line:  # EOF
                        logger.info("EOF received, stopping server")
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    logger.debug(f"Received: {line}")
                    
                    # Process message
                    response = self.server.process_message(line)
                    
                    if response:
                        # Write response to stdout
                        sys.stdout.write(response + "\n")
                        sys.stdout.flush()
                        logger.debug(f"Sent: {response}")
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue processing next message
        
        finally:
            self.running = False
            logger.info("STDIO transport stopped")
    
    async def stop(self):
        """Stop the transport."""
        self.running = False


class HTTPSSETransport(MCPTransport):
    """HTTP with Server-Sent Events transport for MCP server."""
    
    def __init__(self, server, host: str = "127.0.0.1", port: int = 3000):
        """
        Initialize HTTP+SSE transport.
        
        Args:
            server: MCPDevOpsServer instance
            host: Host to bind to
            port: Port to bind to
        """
        self.server = server
        self.host = host
        self.port = port
        self.app = None
        self.runner = None
    
    async def start(self):
        """Start HTTP server."""
        try:
            from aiohttp import web
        except ImportError:
            logger.error("aiohttp not installed. Install with: pip install aiohttp")
            raise
        
        logger.info(f"Starting HTTP+SSE transport on {self.host}:{self.port}")
        
        # Create aiohttp app
        self.app = web.Application()
        self.app.router.add_post('/mcp', self.handle_request)
        self.app.router.add_get('/mcp/sse', self.handle_sse)
        
        # Setup and start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        
        logger.info(f"HTTP+SSE server listening on http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop HTTP server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("HTTP+SSE transport stopped")
    
    async def handle_request(self, request):
        """Handle POST request."""
        try:
            from aiohttp import web
        except ImportError:
            raise
        
        try:
            # Read request body
            body = await request.text()
            logger.debug(f"HTTP request: {body}")
            
            # Process message
            response = self.server.process_message(body)
            
            if response:
                return web.Response(
                    text=response,
                    content_type='application/json'
                )
            else:
                # Notification - no response
                return web.Response(status=204)
        
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return web.Response(
                text=f'{{"jsonrpc":"2.0","id":null,"error":{{"code":-32603,"message":"Internal error: {str(e)}"}}}}',
                status=500,
                content_type='application/json'
            )
    
    async def handle_sse(self, request):
        """Handle SSE connection."""
        try:
            from aiohttp import web
        except ImportError:
            raise
        
        logger.info("SSE connection established")
        
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        
        await response.prepare(request)
        
        try:
            # Keep connection alive
            while True:
                await asyncio.sleep(30)
                # Send keep-alive comment
                await response.write(b': keep-alive\n\n')
        
        except asyncio.CancelledError:
            logger.info("SSE connection closed")
        
        return response


async def run_stdio_server(server):
    """
    Run MCP server with STDIO transport.
    
    Args:
        server: MCPDevOpsServer instance
    """
    transport = StdioTransport(server)
    
    try:
        await transport.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await transport.stop()


async def run_http_server(server, host: str = "127.0.0.1", port: int = 3000):
    """
    Run MCP server with HTTP+SSE transport.
    
    Args:
        server: MCPDevOpsServer instance
        host: Host to bind to
        port: Port to bind to
    """
    transport = HTTPSSETransport(server, host, port)
    
    try:
        await transport.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await transport.stop()
