"""Interactive REPL mode for orbit-mcp AI agent."""

import asyncio
import sys
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner

from .agent import AIAgent


class OrbitREPL:
    """Interactive REPL for natural language DevOps interactions."""
    
    def __init__(self, agent: AIAgent):
        """
        Initialize REPL.
        
        Args:
            agent: AI agent instance
        """
        self.agent = agent
        self.console = Console()
        self.running = False
    
    def print_welcome(self):
        """Print welcome message."""
        welcome = """# Welcome to Orbit AI ??

Your intelligent DevOps assistant powered by LLM.

**Commands:**
- Type your DevOps questions or requests in natural language
- `/help` - Show help
- `/status` - Show usage statistics
- `/reset` - Reset conversation
- `/model <name>` - Switch LLM model
- `/exit` or Ctrl+C - Exit

**Examples:**
- "Check the status of server prod-web-01"
- "Show me the last 100 lines of nginx logs"
- "Why did the OpenSearch cluster fail?"
- "List all running containers on staging"
"""
        self.console.print(Panel(Markdown(welcome), title="Orbit AI", border_style="blue"))
    
    async def run(self):
        """Run interactive REPL loop."""
        self.running = True
        self.print_welcome()
        
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    await self._handle_command(user_input)
                    continue
                
                # Process with agent
                await self._process_input(user_input)
            
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]")
                continue
            
            except EOFError:
                break
            
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
        
        self.console.print("\n[cyan]Goodbye! ??[/cyan]")
    
    async def _process_input(self, user_input: str):
        """Process user input through agent."""
        # Show thinking indicator
        with Live(Spinner("dots", text="[yellow]Thinking...[/yellow]"), console=self.console):
            response = await self.agent.chat_turn(user_input)
        
        # Display response
        self.console.print(f"\n[bold green]Orbit AI[/bold green]:")
        self.console.print(Markdown(response))
    
    async def _handle_command(self, command: str):
        """Handle special commands."""
        cmd = command.lower().strip()
        
        if cmd == '/help':
            self._show_help()
        
        elif cmd == '/exit' or cmd == '/quit':
            self.running = False
        
        elif cmd == '/reset':
            self.agent.reset_conversation()
            self.console.print("[green]? Conversation reset[/green]")
        
        elif cmd == '/status':
            await self._show_status()
        
        elif cmd.startswith('/model'):
            parts = cmd.split(maxsplit=1)
            if len(parts) > 1:
                model = parts[1]
                await self._switch_model(model)
            else:
                self._list_models()
        
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("[yellow]Type /help for available commands[/yellow]")
    
    def _show_help(self):
        """Show help information."""
        help_text = """# Orbit AI Commands

**Conversation:**
- Just type your DevOps questions naturally
- Context is maintained across messages in a session

**Commands:**
- `/help` - Show this help
- `/status` - Show usage and cost statistics
- `/reset` - Start fresh conversation
- `/model [name]` - Switch LLM model or list available models
- `/exit` - Exit REPL

**Examples:**
```
Check if server prod-db-01 is running
Show me nginx error logs from last hour
What's the status of Kubernetes pods in staging?
Explain why the OpenSearch cluster is red
```
"""
        self.console.print(Markdown(help_text))
    
    async def _show_status(self):
        """Show usage statistics."""
        # Get cost manager stats if available
        if hasattr(self.agent.llm, 'cost_manager'):
            usage = self.agent.llm.cost_manager.get_usage_summary()
            
            status = f"""# Usage Statistics

**Today:**
- Cost: ${usage['daily']['cost']:.4f} / ${usage['daily']['limit']:.2f}
- Tokens: {usage['daily']['tokens']:,}
- Remaining: ${usage['daily']['remaining']:.2f}

**This Month:**
- Cost: ${usage['monthly']['cost']:.2f} / ${usage['monthly']['limit']:.2f}
- Tokens: {usage['monthly']['tokens']:,}
- Remaining: ${usage['monthly']['remaining']:.2f}

**All Time:**
- Total Cost: ${usage['total']['cost']:.2f}
- Total Tokens: {usage['total']['tokens']:,}
"""
            self.console.print(Markdown(status))
        else:
            self.console.print("[yellow]Usage tracking not available[/yellow]")
    
    def _list_models(self):
        """List available models."""
        providers = self.agent.llm.list_providers()
        default = self.agent.llm.get_default_provider()
        
        self.console.print("\n[bold]Available Models:[/bold]")
        for provider in providers:
            marker = "?" if provider == default else "  "
            self.console.print(f"{marker} {provider}")
        
        self.console.print(f"\n[dim]Current: {default}[/dim]")
        self.console.print("[dim]Use: /model <name> to switch[/dim]")
    
    async def _switch_model(self, model: str):
        """Switch LLM model."""
        try:
            self.agent.llm.set_default_provider(model)
            self.console.print(f"[green]? Switched to: {model}[/green]")
        except Exception as e:
            self.console.print(f"[red]Failed to switch model: {e}[/red]")


async def start_repl(agent: AIAgent):
    """
    Start interactive REPL.
    
    Args:
        agent: AI agent instance
    """
    repl = OrbitREPL(agent)
    await repl.run()
