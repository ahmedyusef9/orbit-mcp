"""Configuration management for MCP Server."""

import json
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages MCP configuration including credentials and profiles."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. Defaults to ~/.mcp/config.yaml
        """
        if config_path is None:
            self.config_path = Path.home() / ".mcp" / "config.yaml"
        else:
            self.config_path = Path(config_path)
        
        self.config_dir = self.config_path.parent
        self.config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        self.config: Dict[str, Any] = {}
        self.encryption_key: Optional[bytes] = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                if self.config_path.suffix == '.json':
                    self.config = json.load(f)
                else:
                    self.config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {}
    
    def _create_default_config(self):
        """Create a default configuration file."""
        default_config = {
            "version": "1.0",
            "profiles": {},
            "ssh_servers": [],
            "docker_hosts": [],
            "kubernetes_clusters": [],
            "aliases": {},
            "settings": {
                "log_level": "INFO",
                "timeout": 30,
                "retry_count": 3
            }
        }
        
        self.config = default_config
        self.save_config()
        logger.info(f"Created default configuration at {self.config_path}")
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            # Ensure config file has restricted permissions
            os.chmod(self.config_path, 0o600)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def get_ssh_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Get SSH server configuration by name."""
        for server in self.config.get("ssh_servers", []):
            if server.get("name") == name:
                return server
        return None
    
    def get_docker_host(self, name: str) -> Optional[Dict[str, Any]]:
        """Get Docker host configuration by name."""
        for host in self.config.get("docker_hosts", []):
            if host.get("name") == name:
                return host
        return None
    
    def get_k8s_cluster(self, name: str) -> Optional[Dict[str, Any]]:
        """Get Kubernetes cluster configuration by name."""
        for cluster in self.config.get("kubernetes_clusters", []):
            if cluster.get("name") == name:
                return cluster
        return None
    
    def get_alias(self, name: str) -> Optional[str]:
        """Get command alias by name."""
        return self.config.get("aliases", {}).get(name)
    
    def add_ssh_server(self, name: str, host: str, user: str, 
                       key_path: Optional[str] = None, 
                       password: Optional[str] = None,
                       port: int = 22):
        """Add or update SSH server configuration."""
        servers = self.config.get("ssh_servers", [])
        
        # Remove existing server with same name
        servers = [s for s in servers if s.get("name") != name]
        
        server_config = {
            "name": name,
            "host": host,
            "user": user,
            "port": port
        }
        
        if key_path:
            server_config["key_path"] = key_path
        if password:
            # TODO: Encrypt password in future implementation
            logger.warning("Storing password in plain text. Use key-based auth instead.")
            server_config["password"] = password
        
        servers.append(server_config)
        self.config["ssh_servers"] = servers
        self.save_config()
    
    def add_docker_host(self, name: str, host: str, 
                        connection_type: str = "ssh",
                        ssh_config: Optional[Dict[str, Any]] = None):
        """Add or update Docker host configuration."""
        hosts = self.config.get("docker_hosts", [])
        
        # Remove existing host with same name
        hosts = [h for h in hosts if h.get("name") != name]
        
        host_config = {
            "name": name,
            "host": host,
            "connection_type": connection_type
        }
        
        if ssh_config:
            host_config["ssh_config"] = ssh_config
        
        hosts.append(host_config)
        self.config["docker_hosts"] = hosts
        self.save_config()
    
    def add_k8s_cluster(self, name: str, kubeconfig_path: str,
                        context: Optional[str] = None):
        """Add or update Kubernetes cluster configuration."""
        clusters = self.config.get("kubernetes_clusters", [])
        
        # Remove existing cluster with same name
        clusters = [c for c in clusters if c.get("name") != name]
        
        cluster_config = {
            "name": name,
            "kubeconfig_path": kubeconfig_path
        }
        
        if context:
            cluster_config["context"] = context
        
        clusters.append(cluster_config)
        self.config["kubernetes_clusters"] = clusters
        self.save_config()
    
    def add_alias(self, name: str, command: str):
        """Add or update command alias."""
        if "aliases" not in self.config:
            self.config["aliases"] = {}
        
        self.config["aliases"][name] = command
        self.save_config()
    
    def list_profiles(self):
        """List all configured profiles."""
        return {
            "ssh_servers": [s.get("name") for s in self.config.get("ssh_servers", [])],
            "docker_hosts": [h.get("name") for h in self.config.get("docker_hosts", [])],
            "k8s_clusters": [c.get("name") for c in self.config.get("kubernetes_clusters", [])],
            "aliases": list(self.config.get("aliases", {}).keys())
        }
