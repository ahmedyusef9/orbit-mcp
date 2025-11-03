"""Profile management for per-account customization."""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Profile:
    """Profile configuration for per-account customization."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize profile.
        
        Args:
            name: Profile name (e.g., "prod", "staging")
            config: Profile configuration
        """
        self.name = name
        self.config = config
        
        # SSH settings
        self.ssh_hosts = config.get("ssh", {}).get("hosts", {})
        self.ssh_allowed_commands = config.get("ssh", {}).get("allowed_commands", {})
        self.ssh_bastion = config.get("ssh", {}).get("bastion")
        self.ssh_redaction_rules = config.get("ssh", {}).get("redaction_rules", [])
        
        # Ticket settings
        self.ticket_system = config.get("tickets", {}).get("system", "jira")  # jira or github
        self.ticket_project = config.get("tickets", {}).get("project")
        self.ticket_labels = config.get("tickets", {}).get("labels", [])
        self.ticket_space = config.get("tickets", {}).get("space")  # For Confluence
        
        # Alert settings
        self.alert_source = config.get("alerts", {}).get("source", "alerta")
        self.alert_namespace = config.get("alerts", {}).get("namespace")
        self.alert_endpoint = config.get("alerts", {}).get("endpoint")
        
        # Wiki/Knowledge base
        self.kb_type = config.get("knowledge_base", {}).get("type", "confluence")
        self.kb_space = config.get("knowledge_base", {}).get("space")
        self.kb_endpoint = config.get("knowledge_base", {}).get("endpoint")
    
    def get_ssh_host(self, host_name: str) -> Optional[Dict[str, Any]]:
        """Get SSH host configuration."""
        return self.ssh_hosts.get(host_name)
    
    def is_command_allowed(self, cmd_key: str) -> bool:
        """Check if command key is allowed."""
        return cmd_key in self.ssh_allowed_commands
    
    def get_command_template(self, cmd_key: str) -> Optional[str]:
        """Get command template for key."""
        cmd_config = self.ssh_allowed_commands.get(cmd_key)
        if cmd_config:
            return cmd_config.get("template")
        return None


class ProfileManager:
    """Manages profiles and active profile selection."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize profile manager.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = Path(os.getenv("OPS_CONFIG", "/etc/ops-mcp/config.yaml"))
        
        self.config_path = Path(config_path)
        self.profiles: Dict[str, Profile] = {}
        self.active_profile: Optional[str] = None
        
        self._load_profiles()
        self._load_active_profile()
    
    def _load_profiles(self):
        """Load profiles from configuration."""
        import yaml
        
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            profiles_config = config.get("profiles", {})
            for name, profile_config in profiles_config.items():
                self.profiles[name] = Profile(name, profile_config)
            
            logger.info(f"Loaded {len(self.profiles)} profiles")
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}", exc_info=True)
    
    def _load_active_profile(self):
        """Load active profile from environment or config."""
        # Try environment variable first
        self.active_profile = os.getenv("MCP_PROFILE")
        
        # Fall back to config default
        if not self.active_profile:
            import yaml
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                    self.active_profile = config.get("default_profile", "default")
            except:
                self.active_profile = "default"
        
        # Ensure profile exists
        if self.active_profile not in self.profiles:
            logger.warning(f"Active profile '{self.active_profile}' not found, using 'default'")
            if "default" in self.profiles:
                self.active_profile = "default"
            else:
                # Create minimal default profile
                self.active_profile = None
                logger.warning("No profiles available")
    
    def get_active_profile(self) -> Optional[Profile]:
        """Get the active profile."""
        if self.active_profile and self.active_profile in self.profiles:
            return self.profiles[self.active_profile]
        return None
    
    def set_active_profile(self, name: str) -> bool:
        """
        Set active profile.
        
        Args:
            name: Profile name
            
        Returns:
            True if profile was set, False if not found
        """
        if name in self.profiles:
            self.active_profile = name
            logger.info(f"Active profile set to: {name}")
            return True
        else:
            logger.warning(f"Profile not found: {name}")
            return False
    
    def list_profiles(self) -> list[str]:
        """List available profile names."""
        return list(self.profiles.keys())