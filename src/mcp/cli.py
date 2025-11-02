"""Command-line interface for MCP Server."""

import click
import logging
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler
from rich import print as rprint

from .config import ConfigManager
from .ssh_manager import SSHManager
from .docker_manager import DockerManager
from .k8s_manager import KubernetesManager

# Initialize console for rich output
console = Console()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, console=console)]
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def main(ctx, config, verbose):
    """MCP Server - Unified environment management tool for DevOps."""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize managers
    ctx.obj['config'] = ConfigManager(config)
    ctx.obj['ssh'] = SSHManager()
    ctx.obj['docker'] = DockerManager(ctx.obj['ssh'])
    ctx.obj['k8s'] = KubernetesManager()


# Configuration Commands
@main.group()
def config():
    """Manage MCP configuration."""
    pass


@config.command('init')
@click.pass_context
def config_init(ctx):
    """Initialize MCP configuration."""
    config_mgr = ctx.obj['config']
    console.print("[green]MCP configuration initialized successfully![/green]")
    console.print(f"Configuration file: {config_mgr.config_path}")


@config.command('list')
@click.pass_context
def config_list(ctx):
    """List all configured profiles."""
    config_mgr = ctx.obj['config']
    profiles = config_mgr.list_profiles()
    
    console.print("\n[bold]Configured Profiles:[/bold]\n")
    
    if profiles['ssh_servers']:
        console.print("[cyan]SSH Servers:[/cyan]")
        for server in profiles['ssh_servers']:
            console.print(f"  ? {server}")
    
    if profiles['docker_hosts']:
        console.print("\n[cyan]Docker Hosts:[/cyan]")
        for host in profiles['docker_hosts']:
            console.print(f"  ? {host}")
    
    if profiles['k8s_clusters']:
        console.print("\n[cyan]Kubernetes Clusters:[/cyan]")
        for cluster in profiles['k8s_clusters']:
            console.print(f"  ? {cluster}")
    
    if profiles['aliases']:
        console.print("\n[cyan]Aliases:[/cyan]")
        for alias in profiles['aliases']:
            console.print(f"  ? {alias}")


@config.command('add-ssh')
@click.argument('name')
@click.argument('host')
@click.argument('user')
@click.option('--port', default=22, help='SSH port')
@click.option('--key', help='Path to SSH private key')
@click.option('--password', help='SSH password (not recommended)')
@click.pass_context
def config_add_ssh(ctx, name, host, user, port, key, password):
    """Add SSH server configuration."""
    config_mgr = ctx.obj['config']
    config_mgr.add_ssh_server(name, host, user, key, password, port)
    console.print(f"[green]Added SSH server: {name}[/green]")


@config.command('add-docker')
@click.argument('name')
@click.argument('host')
@click.option('--ssh-server', help='SSH server profile to use for connection')
@click.pass_context
def config_add_docker(ctx, name, host, ssh_server):
    """Add Docker host configuration."""
    config_mgr = ctx.obj['config']
    ssh_config = None
    if ssh_server:
        ssh_config = config_mgr.get_ssh_server(ssh_server)
        if not ssh_config:
            console.print(f"[red]SSH server not found: {ssh_server}[/red]")
            return
    
    config_mgr.add_docker_host(name, host, "ssh", ssh_config)
    console.print(f"[green]Added Docker host: {name}[/green]")


@config.command('add-k8s')
@click.argument('name')
@click.argument('kubeconfig')
@click.option('--context', help='Kubernetes context to use')
@click.pass_context
def config_add_k8s(ctx, name, kubeconfig, context):
    """Add Kubernetes cluster configuration."""
    config_mgr = ctx.obj['config']
    config_mgr.add_k8s_cluster(name, kubeconfig, context)
    console.print(f"[green]Added Kubernetes cluster: {name}[/green]")


@config.command('add-alias')
@click.argument('name')
@click.argument('command')
@click.pass_context
def config_add_alias(ctx, name, command):
    """Add command alias."""
    config_mgr = ctx.obj['config']
    config_mgr.add_alias(name, command)
    console.print(f"[green]Added alias: {name}[/green]")


# SSH Commands
@main.group()
def ssh():
    """SSH operations."""
    pass


@ssh.command('exec')
@click.argument('server')
@click.argument('command')
@click.pass_context
def ssh_exec(ctx, server, command):
    """Execute command on remote server."""
    config_mgr = ctx.obj['config']
    ssh_mgr = ctx.obj['ssh']
    
    # Get server config
    server_config = config_mgr.get_ssh_server(server)
    if not server_config:
        console.print(f"[red]Server not found: {server}[/red]")
        return
    
    # Check if command is an alias
    alias_cmd = config_mgr.get_alias(command)
    if alias_cmd:
        command = alias_cmd
        console.print(f"[dim]Using alias: {command}[/dim]")
    
    try:
        client = ssh_mgr.connect(
            server_config['host'],
            server_config['user'],
            server_config.get('port', 22),
            server_config.get('key_path'),
            server_config.get('password')
        )
        
        stdout, stderr, exit_code = ssh_mgr.execute_command(client, command)
        
        if stdout:
            console.print(stdout)
        if stderr:
            console.print(f"[red]{stderr}[/red]", file=sys.stderr)
        
        sys.exit(exit_code)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@ssh.command('logs')
@click.argument('server')
@click.argument('log_path')
@click.option('--lines', '-n', default=50, help='Number of lines to show')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.pass_context
def ssh_logs(ctx, server, log_path, lines, follow):
    """Tail logs from remote server."""
    config_mgr = ctx.obj['config']
    ssh_mgr = ctx.obj['ssh']
    
    server_config = config_mgr.get_ssh_server(server)
    if not server_config:
        console.print(f"[red]Server not found: {server}[/red]")
        return
    
    try:
        client = ssh_mgr.connect(
            server_config['host'],
            server_config['user'],
            server_config.get('port', 22),
            server_config.get('key_path'),
            server_config.get('password')
        )
        
        console.print(f"[dim]Tailing {log_path} on {server}...[/dim]\n")
        
        for line in ssh_mgr.tail_log(client, log_path, lines, follow):
            console.print(line)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped tailing log[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# Docker Commands
@main.group()
def docker():
    """Docker operations."""
    pass


@docker.command('ps')
@click.option('--host', help='Docker host name from config')
@click.option('--all', '-a', is_flag=True, help='Show all containers')
@click.pass_context
def docker_ps(ctx, host, all):
    """List Docker containers."""
    docker_mgr = ctx.obj['docker']
    
    try:
        if host:
            config_mgr = ctx.obj['config']
            host_config = config_mgr.get_docker_host(host)
            if not host_config:
                console.print(f"[red]Docker host not found: {host}[/red]")
                return
            # For remote, we'd need to implement SSH tunnel or remote connection
            client = None
        else:
            client = None
        
        containers = docker_mgr.list_containers(client, all)
        
        table = Table(title="Docker Containers")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Image", style="blue")
        
        for container in containers:
            table.add_row(
                container['id'],
                container['name'],
                container['status'],
                container['image']
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@docker.command('logs')
@click.argument('container')
@click.option('--tail', '-n', default=100, help='Number of lines to show')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.pass_context
def docker_logs(ctx, container, tail, follow):
    """Get Docker container logs."""
    docker_mgr = ctx.obj['docker']
    
    try:
        console.print(f"[dim]Fetching logs for {container}...[/dim]\n")
        
        for line in docker_mgr.get_container_logs(container, tail=tail, follow=follow):
            console.print(line)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped following logs[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@docker.command('start')
@click.argument('container')
@click.pass_context
def docker_start(ctx, container):
    """Start Docker container."""
    docker_mgr = ctx.obj['docker']
    
    try:
        docker_mgr.start_container(container)
        console.print(f"[green]Started container: {container}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@docker.command('stop')
@click.argument('container')
@click.pass_context
def docker_stop(ctx, container):
    """Stop Docker container."""
    docker_mgr = ctx.obj['docker']
    
    try:
        docker_mgr.stop_container(container)
        console.print(f"[green]Stopped container: {container}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@docker.command('restart')
@click.argument('container')
@click.pass_context
def docker_restart(ctx, container):
    """Restart Docker container."""
    docker_mgr = ctx.obj['docker']
    
    try:
        docker_mgr.restart_container(container)
        console.print(f"[green]Restarted container: {container}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# Kubernetes Commands
@main.group()
def k8s():
    """Kubernetes operations."""
    pass


@k8s.command('contexts')
@click.option('--kubeconfig', help='Path to kubeconfig file')
@click.pass_context
def k8s_contexts(ctx, kubeconfig):
    """List Kubernetes contexts."""
    k8s_mgr = ctx.obj['k8s']
    
    try:
        contexts = k8s_mgr.list_contexts(kubeconfig)
        console.print("\n[bold]Available Contexts:[/bold]\n")
        for context in contexts:
            console.print(f"  ? {context}")
        console.print()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@k8s.command('use')
@click.argument('cluster')
@click.pass_context
def k8s_use(ctx, cluster):
    """Switch to Kubernetes cluster."""
    config_mgr = ctx.obj['config']
    k8s_mgr = ctx.obj['k8s']
    
    cluster_config = config_mgr.get_k8s_cluster(cluster)
    if not cluster_config:
        console.print(f"[red]Cluster not found: {cluster}[/red]")
        return
    
    try:
        context = k8s_mgr.load_kubeconfig(
            cluster_config['kubeconfig_path'],
            cluster_config.get('context')
        )
        console.print(f"[green]Switched to cluster: {cluster} (context: {context})[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@k8s.command('pods')
@click.option('--namespace', '-n', default='default', help='Kubernetes namespace')
@click.option('--cluster', help='Cluster name from config')
@click.pass_context
def k8s_pods(ctx, namespace, cluster):
    """List pods in namespace."""
    k8s_mgr = ctx.obj['k8s']
    
    if cluster:
        config_mgr = ctx.obj['config']
        cluster_config = config_mgr.get_k8s_cluster(cluster)
        if not cluster_config:
            console.print(f"[red]Cluster not found: {cluster}[/red]")
            return
        k8s_mgr.load_kubeconfig(
            cluster_config['kubeconfig_path'],
            cluster_config.get('context')
        )
    
    try:
        pods = k8s_mgr.list_pods(namespace)
        
        table = Table(title=f"Pods in {namespace}")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Node", style="yellow")
        table.add_column("IP", style="blue")
        table.add_column("Containers", style="magenta")
        
        for pod in pods:
            table.add_row(
                pod['name'],
                pod['status'],
                pod['node'] or 'N/A',
                pod['ip'] or 'N/A',
                str(pod['containers'])
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@k8s.command('logs')
@click.argument('pod')
@click.option('--namespace', '-n', default='default', help='Kubernetes namespace')
@click.option('--container', '-c', help='Container name')
@click.option('--tail', default=100, help='Number of lines')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.pass_context
def k8s_logs(ctx, pod, namespace, container, tail, follow):
    """Get pod logs."""
    k8s_mgr = ctx.obj['k8s']
    
    try:
        console.print(f"[dim]Fetching logs for {pod}...[/dim]\n")
        
        if follow:
            for line in k8s_mgr.get_pod_logs(pod, namespace, container, tail, follow):
                console.print(line.decode('utf-8').rstrip('\n'))
        else:
            logs = k8s_mgr.get_pod_logs(pod, namespace, container, tail, follow)
            console.print(logs)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped following logs[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@k8s.command('services')
@click.option('--namespace', '-n', default='default', help='Kubernetes namespace')
@click.pass_context
def k8s_services(ctx, namespace):
    """List services in namespace."""
    k8s_mgr = ctx.obj['k8s']
    
    try:
        services = k8s_mgr.list_services(namespace)
        
        table = Table(title=f"Services in {namespace}")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Cluster IP", style="yellow")
        table.add_column("Ports", style="blue")
        
        for svc in services:
            ports_str = ", ".join([f"{p['port']}/{p['protocol']}" for p in svc['ports']])
            table.add_row(
                svc['name'],
                svc['type'],
                svc['cluster_ip'] or 'None',
                ports_str
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@k8s.command('deployments')
@click.option('--namespace', '-n', default='default', help='Kubernetes namespace')
@click.pass_context
def k8s_deployments(ctx, namespace):
    """List deployments in namespace."""
    k8s_mgr = ctx.obj['k8s']
    
    try:
        deployments = k8s_mgr.list_deployments(namespace)
        
        table = Table(title=f"Deployments in {namespace}")
        table.add_column("Name", style="cyan")
        table.add_column("Desired", style="green")
        table.add_column("Ready", style="yellow")
        table.add_column("Available", style="blue")
        table.add_column("Updated", style="magenta")
        
        for deploy in deployments:
            table.add_row(
                deploy['name'],
                str(deploy['replicas']),
                str(deploy['ready_replicas']),
                str(deploy['available_replicas']),
                str(deploy['updated_replicas'])
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@k8s.command('scale')
@click.argument('deployment')
@click.argument('replicas', type=int)
@click.option('--namespace', '-n', default='default', help='Kubernetes namespace')
@click.pass_context
def k8s_scale(ctx, deployment, replicas, namespace):
    """Scale deployment."""
    k8s_mgr = ctx.obj['k8s']
    
    try:
        k8s_mgr.scale_deployment(deployment, replicas, namespace)
        console.print(f"[green]Scaled {deployment} to {replicas} replicas[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@k8s.command('restart')
@click.argument('deployment')
@click.option('--namespace', '-n', default='default', help='Kubernetes namespace')
@click.pass_context
def k8s_restart(ctx, deployment, namespace):
    """Restart deployment."""
    k8s_mgr = ctx.obj['k8s']
    
    try:
        k8s_mgr.restart_deployment(deployment, namespace)
        console.print(f"[green]Restarted deployment: {deployment}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
