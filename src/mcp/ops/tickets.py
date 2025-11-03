"""Ticket system integrations (Jira, GitHub Issues)."""

import logging
from typing import Dict, Any, Optional, List
import requests

logger = logging.getLogger(__name__)


class TicketSystem:
    """Base class for ticket system integrations."""
    
    def create_ticket(
        self,
        project: str,
        title: str,
        body: str,
        labels: List[str],
        priority: str
    ) -> Dict[str, Any]:
        """Create a ticket."""
        raise NotImplementedError
    
    def update_status(self, ticket_id: str, status: str) -> Dict[str, Any]:
        """Update ticket status."""
        raise NotImplementedError
    
    def add_comment(self, ticket_id: str, comment: str) -> Dict[str, Any]:
        """Add comment to ticket."""
        raise NotImplementedError


class JiraTicketSystem(TicketSystem):
    """Jira integration."""
    
    def __init__(self, endpoint: str, email: str, api_token: str, project: Optional[str] = None):
        """
        Initialize Jira client.
        
        Args:
            endpoint: Jira base URL (e.g., https://company.atlassian.net)
            email: Jira user email
            api_token: Jira API token
            project: Default project key
        """
        self.endpoint = endpoint.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.default_project = project
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_ticket(
        self,
        project: str,
        title: str,
        body: str,
        labels: List[str],
        priority: str = "Medium"
    ) -> Dict[str, Any]:
        """Create Jira issue."""
        project = project or self.default_project
        if not project:
            return {
                "success": False,
                "error": "PROJECT_REQUIRED",
                "message": "Project key required"
            }
        
        # Map priority
        priority_map = {
            "Low": "Lowest",
            "Medium": "Medium",
            "High": "High",
            "Critical": "Highest"
        }
        jira_priority = priority_map.get(priority, "Medium")
        
        # Create issue payload
        payload = {
            "fields": {
                "project": {"key": project},
                "summary": title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": body}]
                        }
                    ]
                },
                "issuetype": {"name": "Bug"},
                "priority": {"name": jira_priority}
            }
        }
        
        if labels:
            payload["fields"]["labels"] = labels
        
        try:
            url = f"{self.endpoint}/rest/api/3/issue"
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            issue_key = data.get("key")
            issue_url = f"{self.endpoint}/browse/{issue_key}"
            
            return {
                "success": True,
                "id": issue_key,
                "url": issue_url,
                "system": "jira"
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Jira API error: {e}")
            return {
                "success": False,
                "error": "API_ERROR",
                "message": str(e)
            }
    
    def update_status(self, ticket_id: str, status: str) -> Dict[str, Any]:
        """Update Jira issue status."""
        try:
            # First get available transitions
            url = f"{self.endpoint}/rest/api/3/issue/{ticket_id}/transitions"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            transitions = response.json().get("transitions", [])
            transition_id = None
            
            # Find transition matching status
            for transition in transitions:
                if status.lower() in transition.get("name", "").lower():
                    transition_id = transition["id"]
                    break
            
            if not transition_id:
                return {
                    "success": False,
                    "error": "INVALID_STATUS",
                    "message": f"Status '{status}' not available"
                }
            
            # Execute transition
            payload = {"transition": {"id": transition_id}}
            url = f"{self.endpoint}/rest/api/3/issue/{ticket_id}/transitions"
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return {
                "success": True,
                "id": ticket_id,
                "status": status
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Jira API error: {e}")
            return {
                "success": False,
                "error": "API_ERROR",
                "message": str(e)
            }
    
    def add_comment(self, ticket_id: str, comment: str) -> Dict[str, Any]:
        """Add comment to Jira issue."""
        try:
            url = f"{self.endpoint}/rest/api/3/issue/{ticket_id}/comment"
            payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": comment}]
                        }
                    ]
                }
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return {
                "success": True,
                "id": ticket_id,
                "comment_id": response.json().get("id")
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Jira API error: {e}")
            return {
                "success": False,
                "error": "API_ERROR",
                "message": str(e)
            }


class GitHubTicketSystem(TicketSystem):
    """GitHub Issues integration."""
    
    def __init__(self, owner: str, repo: str, token: str):
        """
        Initialize GitHub client.
        
        Args:
            owner: Repository owner
            repo: Repository name
            token: GitHub personal access token
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.endpoint = f"https://api.github.com/repos/{owner}/{repo}"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        })
    
    def create_ticket(
        self,
        project: Optional[str],
        title: str,
        body: str,
        labels: List[str],
        priority: str = "Medium"
    ) -> Dict[str, Any]:
        """Create GitHub issue."""
        # Map priority to labels if not already present
        priority_labels = {
            "Critical": "priority:critical",
            "High": "priority:high",
            "Medium": "priority:medium",
            "Low": "priority:low"
        }
        
        all_labels = labels.copy()
        if priority in priority_labels:
            all_labels.append(priority_labels[priority])
        
        payload = {
            "title": title,
            "body": body,
            "labels": all_labels
        }
        
        try:
            url = f"{self.endpoint}/issues"
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            issue_number = data.get("number")
            issue_url = data.get("html_url")
            
            return {
                "success": True,
                "id": str(issue_number),
                "url": issue_url,
                "system": "github"
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error: {e}")
            return {
                "success": False,
                "error": "API_ERROR",
                "message": str(e)
            }
    
    def update_status(self, ticket_id: str, status: str) -> Dict[str, Any]:
        """Update GitHub issue status (open/closed)."""
        state = "closed" if status.lower() in ("done", "closed", "resolved") else "open"
        
        try:
            url = f"{self.endpoint}/issues/{ticket_id}"
            payload = {"state": state}
            
            response = self.session.patch(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return {
                "success": True,
                "id": ticket_id,
                "status": state
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error: {e}")
            return {
                "success": False,
                "error": "API_ERROR",
                "message": str(e)
            }
    
    def add_comment(self, ticket_id: str, comment: str) -> Dict[str, Any]:
        """Add comment to GitHub issue."""
        try:
            url = f"{self.endpoint}/issues/{ticket_id}/comments"
            payload = {"body": comment}
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return {
                "success": True,
                "id": ticket_id,
                "comment_id": response.json().get("id")
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error: {e}")
            return {
                "success": False,
                "error": "API_ERROR",
                "message": str(e)
            }


def create_ticket_system(profile, config: Dict[str, Any]) -> Optional[TicketSystem]:
    """
    Create ticket system instance from profile and config.
    
    Args:
        profile: Active profile
        config: Ticket system configuration
        
    Returns:
        TicketSystem instance or None
    """
    system_type = profile.ticket_system or config.get("system", "jira")
    
    if system_type == "jira":
        endpoint = config.get("endpoint")
        email = config.get("email")
        api_token = config.get("api_token")
        
        if not all([endpoint, email, api_token]):
            logger.warning("Jira configuration incomplete")
            return None
        
        return JiraTicketSystem(
            endpoint=endpoint,
            email=email,
            api_token=api_token,
            project=profile.ticket_project
        )
    
    elif system_type == "github":
        owner = config.get("owner")
        repo = config.get("repo")
        token = config.get("token")
        
        if not all([owner, repo, token]):
            logger.warning("GitHub configuration incomplete")
            return None
        
        return GitHubTicketSystem(owner=owner, repo=repo, token=token)
    
    else:
        logger.warning(f"Unknown ticket system: {system_type}")
        return None