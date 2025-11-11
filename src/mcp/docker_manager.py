"""Docker container management."""

import docker
import logging
from typing import List, Dict, Any, Optional
from .ssh_manager import SSHManager

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker containers on local and remote hosts."""
    
    def __init__(self, ssh_manager: Optional[SSHManager] = None):
        """
        Initialize Docker manager.
        
        Args:
            ssh_manager: SSH manager instance for remote Docker access
        """
        self.ssh_manager = ssh_manager or SSHManager()
        self.local_client = None
    
    def get_local_client(self) -> docker.DockerClient:
        """Get local Docker client."""
        if self.local_client is None:
            try:
                self.local_client = docker.from_env()
                logger.info("Connected to local Docker daemon")
            except Exception as e:
                logger.error(f"Failed to connect to local Docker: {e}")
                raise ConnectionError(f"Cannot connect to local Docker daemon: {e}")
        return self.local_client
    
    def get_remote_client(self, host: str, ssh_config: Dict[str, Any]) -> docker.DockerClient:
        """
        Get Docker client for remote host via SSH.
        
        Args:
            host: Remote host address
            ssh_config: SSH configuration dictionary
            
        Returns:
            Docker client connected via SSH
        """
        try:
            # Connect via SSH tunnel
            ssh_url = f"ssh://{ssh_config['user']}@{host}"
            client = docker.DockerClient(base_url=ssh_url)
            logger.info(f"Connected to Docker on {host}")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to remote Docker: {e}")
            raise ConnectionError(f"Cannot connect to Docker on {host}: {e}")
    
    def execute_docker_command_remote(self, ssh_client, command: str) -> tuple:
        """
        Execute Docker command on remote host via SSH.
        
        Args:
            ssh_client: SSH client instance
            command: Docker command to execute
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        return self.ssh_manager.execute_command(ssh_client, f"docker {command}")
    
    def list_containers(self, client: Optional[docker.DockerClient] = None,
                       all: bool = False) -> List[Dict[str, Any]]:
        """
        List Docker containers.
        
        Args:
            client: Docker client (uses local if None)
            all: Include stopped containers
            
        Returns:
            List of container information dictionaries
        """
        if client is None:
            client = self.get_local_client()
        
        try:
            containers = client.containers.list(all=all)
            result = []
            
            for container in containers:
                result.append({
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else container.image.short_id,
                    "created": container.attrs['Created'],
                    "ports": container.attrs.get('NetworkSettings', {}).get('Ports', {})
                })
            
            logger.info(f"Found {len(result)} containers")
            return result
            
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            raise RuntimeError(f"Failed to list containers: {e}")
    
    def get_container(self, container_id: str,
                     client: Optional[docker.DockerClient] = None):
        """
        Get container by ID or name.
        
        Args:
            container_id: Container ID or name
            client: Docker client (uses local if None)
            
        Returns:
            Container object
        """
        if client is None:
            client = self.get_local_client()
        
        try:
            return client.containers.get(container_id)
        except docker.errors.NotFound:
            raise ValueError(f"Container not found: {container_id}")
        except Exception as e:
            logger.error(f"Failed to get container: {e}")
            raise
    
    def start_container(self, container_id: str,
                       client: Optional[docker.DockerClient] = None):
        """Start a container."""
        try:
            container = self.get_container(container_id, client)
            container.start()
            logger.info(f"Started container: {container_id}")
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise
    
    def stop_container(self, container_id: str,
                      client: Optional[docker.DockerClient] = None,
                      timeout: int = 10):
        """Stop a container."""
        try:
            container = self.get_container(container_id, client)
            container.stop(timeout=timeout)
            logger.info(f"Stopped container: {container_id}")
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
            raise
    
    def restart_container(self, container_id: str,
                         client: Optional[docker.DockerClient] = None,
                         timeout: int = 10):
        """Restart a container."""
        try:
            container = self.get_container(container_id, client)
            container.restart(timeout=timeout)
            logger.info(f"Restarted container: {container_id}")
        except Exception as e:
            logger.error(f"Failed to restart container: {e}")
            raise
    
    def remove_container(self, container_id: str,
                        client: Optional[docker.DockerClient] = None,
                        force: bool = False):
        """Remove a container."""
        try:
            container = self.get_container(container_id, client)
            container.remove(force=force)
            logger.info(f"Removed container: {container_id}")
        except Exception as e:
            logger.error(f"Failed to remove container: {e}")
            raise
    
    def get_container_logs(self, container_id: str,
                          client: Optional[docker.DockerClient] = None,
                          tail: int = 100,
                          follow: bool = False,
                          timestamps: bool = False):
        """
        Get container logs.
        
        Args:
            container_id: Container ID or name
            client: Docker client
            tail: Number of lines to retrieve
            follow: Stream logs in real-time
            timestamps: Include timestamps
            
        Yields:
            Log lines
        """
        try:
            container = self.get_container(container_id, client)
            
            for line in container.logs(stream=follow, tail=tail, 
                                      timestamps=timestamps, 
                                      follow=follow):
                yield line.decode('utf-8').rstrip('\n')
                
        except Exception as e:
            logger.error(f"Failed to get container logs: {e}")
            raise
    
    def execute_in_container(self, container_id: str, command: str,
                           client: Optional[docker.DockerClient] = None) -> tuple:
        """
        Execute command in a running container.
        
        Args:
            container_id: Container ID or name
            command: Command to execute
            client: Docker client
            
        Returns:
            Tuple of (exit_code, output)
        """
        try:
            container = self.get_container(container_id, client)
            exit_code, output = container.exec_run(command)
            logger.debug(f"Executed command in {container_id}: {command}")
            return exit_code, output.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to execute command in container: {e}")
            raise
    
    def get_container_stats(self, container_id: str,
                          client: Optional[docker.DockerClient] = None) -> Dict[str, Any]:
        """
        Get container resource statistics.
        
        Args:
            container_id: Container ID or name
            client: Docker client
            
        Returns:
            Dictionary with CPU, memory, and network stats
        """
        try:
            container = self.get_container(container_id, client)
            stats = container.stats(stream=False)
            
            # Parse and simplify stats
            cpu_stats = stats['cpu_stats']
            mem_stats = stats['memory_stats']
            
            result = {
                "cpu_percent": self._calculate_cpu_percent(stats),
                "memory_usage": mem_stats.get('usage', 0),
                "memory_limit": mem_stats.get('limit', 0),
                "memory_percent": (mem_stats.get('usage', 0) / mem_stats.get('limit', 1)) * 100,
                "network_rx": sum([net.get('rx_bytes', 0) for net in stats.get('networks', {}).values()]),
                "network_tx": sum([net.get('tx_bytes', 0) for net in stats.get('networks', {}).values()])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get container stats: {e}")
            raise
    
    def _calculate_cpu_percent(self, stats: Dict[str, Any]) -> float:
        """Calculate CPU percentage from stats."""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_count = stats['cpu_stats'].get('online_cpus', 1)
            
            if system_delta > 0 and cpu_delta > 0:
                return (cpu_delta / system_delta) * cpu_count * 100.0
            return 0.0
        except (KeyError, ZeroDivisionError):
            return 0.0
    
    def list_images(self, client: Optional[docker.DockerClient] = None) -> List[Dict[str, Any]]:
        """List Docker images."""
        if client is None:
            client = self.get_local_client()
        
        try:
            images = client.images.list()
            result = []
            
            for image in images:
                result.append({
                    "id": image.short_id,
                    "tags": image.tags,
                    "size": image.attrs.get('Size', 0),
                    "created": image.attrs.get('Created', '')
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            raise
    
    def pull_image(self, image: str, tag: str = "latest",
                  client: Optional[docker.DockerClient] = None):
        """Pull Docker image."""
        if client is None:
            client = self.get_local_client()
        
        try:
            logger.info(f"Pulling image: {image}:{tag}")
            client.images.pull(image, tag=tag)
            logger.info(f"Successfully pulled {image}:{tag}")
        except Exception as e:
            logger.error(f"Failed to pull image: {e}")
            raise
