"""CLI mode for orbit-mcp AI agent - one-shot queries."""

import asyncio
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live

from .agent import AIAgent


async def process_one_shot(agent: AIAgent, prompt: str) -> str:
    """
    Process a single prompt and return response.
    
    Args:
        agent: AI agent instance
        prompt: User prompt
        
    Returns:
        Response text
    """
    console = Console()
    
    # Show progress
    with Live(Spinner("dots", text="[yellow]Processing...[/yellow]"), console=console):
        response = await agent.process_prompt(prompt)
    
    return response


async def run_ai_cli(agent: AIAgent, prompt: str, output_format: str = 'markdown'):
    """
    Run AI agent in CLI mode (one-shot).
    
    Args:
        agent: AI agent instance
        prompt: User prompt
        output_format: Output format (markdown, plain, json)
    """
    console = Console()
    
    try:
        response = await process_one_shot(agent, prompt)
        
        # Format output
        if output_format == 'markdown':
            console.print("\n")
            console.print(Panel(Markdown(response), title="Orbit AI Response", border_style="green"))
        
        elif output_format == 'plain':
            console.print(response)
        
        elif output_format == 'json':
            import json
            output = {
                'prompt': prompt,
                'response': response,
                'status': 'success'
            }
            console.print(json.dumps(output, indent=2))
        
        # Show cost if available
        if hasattr(agent.llm, 'cost_manager'):
            usage = agent.llm.cost_manager.get_usage_summary()
            console.print(f"\n[dim]Cost: ${usage['daily']['cost']:.4f} today[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", style="bold")
        
        if output_format == 'json':
            import json
            error_output = {
                'prompt': prompt,
                'error': str(e),
                'status': 'error'
            }
            console.print(json.dumps(error_output, indent=2))
