"""Resource resolvers for read-only, file-like data."""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class ResourceResolver:
    """Resolves resources (runbooks, documentation, etc.)."""
    
    def __init__(self, profile, config: Dict[str, Any]):
        """
        Initialize resource resolver.
        
        Args:
            profile: Active profile
            config: Resource configuration
        """
        self.profile = profile
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def list_resources(self) -> List[Dict[str, str]]:
        """
        List available resources.
        
        Returns:
            List of resource URIs with metadata
        """
        resources = []
        
        # Runbooks from knowledge base
        if self.profile.kb_space:
            # This would query Confluence/wiki for available runbooks
            # For now, return example structure
            resources.append({
                "uri": f"runbooks/service-a.md",
                "name": "Service A Runbook",
                "description": "Runbook for Service A",
                "mimeType": "text/markdown"
            })
        
        # Tickets (generated resources)
        resources.append({
            "uri": "tickets/*",
            "name": "Tickets",
            "description": "Ticket metadata and status",
            "mimeType": "application/json"
        })
        
        # Incidents
        resources.append({
            "uri": "incidents/current",
            "name": "Current Incidents",
            "description": "List of active incidents",
            "mimeType": "application/json"
        })
        
        return resources
    
    def read_resource(self, uri: str) -> Optional[Dict[str, Any]]:
        """
        Read resource content.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content or None if not found
        """
        # Check cache first
        if uri in self.cache:
            return self.cache[uri]
        
        # Parse URI
        if uri.startswith("runbooks/"):
            return self._read_runbook(uri)
        elif uri.startswith("tickets/"):
            return self._read_ticket(uri)
        elif uri == "incidents/current":
            return self._read_incidents()
        else:
            logger.warning(f"Unknown resource URI: {uri}")
            return None
    
    def _read_runbook(self, uri: str) -> Optional[Dict[str, Any]]:
        """Read runbook from knowledge base."""
        # Extract service name
        service_name = uri.replace("runbooks/", "").replace(".md", "")
        
        # Try to fetch from Confluence/wiki
        if self.profile.kb_type == "confluence" and self.profile.kb_endpoint:
            try:
                # This is a simplified example - real implementation would use Confluence API
                url = f"{self.profile.kb_endpoint}/rest/api/content"
                # Query for runbook page
                # ... implementation ...
                pass
            except Exception as e:
                logger.error(f"Failed to fetch runbook: {e}")
        
        # Fallback to local file
        local_path = Path(f"docs/runbooks/{service_name}.md")
        if local_path.exists():
            content = local_path.read_text()
            return {
                "uri": uri,
                "mimeType": "text/markdown",
                "text": content
            }
        
        return None
    
    def _read_ticket(self, uri: str) -> Optional[Dict[str, Any]]:
        """Read ticket metadata."""
        # Extract ticket ID
        ticket_id = uri.replace("tickets/", "").replace(".md", "")
        
        # This would query the ticket system for metadata
        # For now, return placeholder
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps({
                "id": ticket_id,
                "status": "unknown",
                "note": "Ticket metadata would be fetched from ticket system"
            })
        }
    
    def _read_incidents(self) -> Optional[Dict[str, Any]]:
        """Read current incidents."""
        # This would query alert system
        return {
            "uri": "incidents/current",
            "mimeType": "application/json",
            "text": json.dumps({
                "incidents": [],
                "note": "Incidents would be fetched from alert system"
            })
        }


class PromptRegistry:
    """Registry for reusable prompt templates."""
    
    def __init__(self):
        """Initialize prompt registry."""
        self.prompts = {
            "triage": {
                "name": "triage",
                "description": "Triage a defect using available tools",
                "arguments": [
                    {
                        "name": "service",
                        "description": "Service name",
                        "required": True
                    },
                    {
                        "name": "symptoms",
                        "description": "Observed symptoms",
                        "required": True
                    },
                    {
                        "name": "last_change",
                        "description": "Last deployment or change",
                        "required": False
                    }
                ]
            },
            "rollback": {
                "name": "rollback",
                "description": "Prepare a rollback plan",
                "arguments": [
                    {
                        "name": "service",
                        "description": "Service to rollback",
                        "required": True
                    },
                    {
                        "name": "version",
                        "description": "Version to rollback to",
                        "required": True
                    }
                ]
            },
            "deploy_verify": {
                "name": "deploy_verify",
                "description": "Verify a deployment",
                "arguments": [
                    {
                        "name": "service",
                        "description": "Service name",
                        "required": True
                    },
                    {
                        "name": "version",
                        "description": "Deployed version",
                        "required": True
                    }
                ]
            }
        }
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """List available prompts."""
        return list(self.prompts.values())
    
    def get_prompt(self, name: str, arguments: Dict[str, str]) -> Optional[str]:
        """
        Get prompt template rendered with arguments.
        
        Args:
            name: Prompt name
            arguments: Prompt arguments
            
        Returns:
            Rendered prompt text
        """
        prompt_def = self.prompts.get(name)
        if not prompt_def:
            return None
        
        if name == "triage":
            return self._render_triage_prompt(arguments)
        elif name == "rollback":
            return self._render_rollback_prompt(arguments)
        elif name == "deploy_verify":
            return self._render_deploy_verify_prompt(arguments)
        
        return None
    
    def _render_triage_prompt(self, args: Dict[str, str]) -> str:
        """Render triage prompt."""
        service = args.get("service", "unknown")
        symptoms = args.get("symptoms", "unknown")
        last_change = args.get("last_change", "unknown")
        
        return f"""Triage defect for service: {service}

Observed Symptoms:
{symptoms}

Last Change:
{last_change}

Use the following tools in order:
1. ssh.healthcheck - Check service health on all hosts
2. ssh.tail - Review recent logs for errors
3. alert.list - Check for related alerts
4. ticket.create - Create incident ticket if needed

Analyze the situation and provide:
- Root cause hypothesis
- Immediate mitigation steps
- Long-term fix recommendations"""
    
    def _render_rollback_prompt(self, args: Dict[str, str]) -> str:
        """Render rollback prompt."""
        service = args.get("service", "unknown")
        version = args.get("version", "unknown")
        
        return f"""Prepare rollback plan for {service} to version {version}

Steps to follow:
1. Verify version {version} exists and is stable
2. ssh.healthcheck on all {service} hosts
3. Run deploy.verify for version {version}
4. Create rollback ticket
5. Schedule rollback window
6. Execute rollback with monitoring

Provide detailed rollback procedure."""
    
    def _render_deploy_verify_prompt(self, args: Dict[str, str]) -> str:
        """Render deploy verify prompt."""
        service = args.get("service", "unknown")
        version = args.get("version", "unknown")
        
        return f"""Verify deployment of {service} version {version}

Checklist:
1. ssh.healthcheck - All hosts healthy
2. ssh.tail - No errors in logs
3. alert.list - No new alerts
4. Service responding correctly
5. Metrics within normal range

Report verification status and any issues found."""