"""SSH command execution with allow-listing and security guardrails."""

import re
import logging
import subprocess
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class SSHWrapper:
    """Secure SSH command wrapper with allow-listing."""
    
    def __init__(self, profile):
        """
        Initialize SSH wrapper.
        
        Args:
            profile: Active Profile instance
        """
        self.profile = profile
        self.redaction_patterns = self._compile_redaction_patterns()
    
    def _compile_redaction_patterns(self) -> List[re.Pattern]:
        """Compile redaction regex patterns."""
        patterns = []
        
        # Default patterns
        default_patterns = [
            r'(?i)(password|passwd|pwd)\s*[:=]\s*(\S+)',  # password: value
            r'(?i)(api[_-]?key|apikey)\s*[:=]\s*(\S+)',  # api_key: value
            r'(?i)(token|secret)\s*[:=]\s*(\S+)',        # token: value
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email addresses
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',      # Credit cards
        ]
        
        # Add profile-specific patterns
        profile_patterns = self.profile.ssh_redaction_rules
        for pattern_str in profile_patterns + default_patterns:
            try:
                patterns.append(re.compile(pattern_str))
            except re.error as e:
                logger.warning(f"Invalid redaction pattern: {pattern_str}: {e}")
        
        return patterns
    
    def redact_secrets(self, text: str) -> Tuple[str, bool]:
        """
        Redact secrets from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Tuple of (redacted_text, was_redacted)
        """
        was_redacted = False
        redacted = text
        
        for pattern in self.redaction_patterns:
            matches = list(pattern.finditer(redacted))
            if matches:
                was_redacted = True
                # Replace matches with [REDACTED]
                for match in reversed(matches):  # Reverse to preserve positions
                    redacted = redacted[:match.start()] + "[REDACTED]" + redacted[match.end():]
        
        return redacted, was_redacted
    
    def validate_command(self, cmd_key: str, args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate command key and render template.
        
        Args:
            cmd_key: Command key from allow-list
            args: Arguments to render template
            
        Returns:
            Tuple of (is_valid, rendered_command_or_error)
        """
        if not self.profile.is_command_allowed(cmd_key):
            return False, f"Command key '{cmd_key}' not in allow-list"
        
        template = self.profile.get_command_template(cmd_key)
        if not template:
            return False, f"No template found for command key '{cmd_key}'"
        
        try:
            # Simple template rendering (support {key} placeholders)
            rendered = template.format(**args)
            return True, rendered
        except KeyError as e:
            return False, f"Missing required argument: {e}"
        except Exception as e:
            return False, f"Template rendering error: {e}"
    
    def execute_command(
        self,
        host_name: str,
        command: str,
        timeout_sec: int = 60
    ) -> Dict[str, Any]:
        """
        Execute command on remote host via SSH.
        
        Args:
            host_name: Host name from profile
            command: Rendered command to execute
            timeout_sec: Timeout in seconds (max 120)
            
        Returns:
            Execution result
        """
        # Validate timeout
        timeout_sec = min(timeout_sec, 120)
        
        # Get host config
        host_config = self.profile.get_ssh_host(host_name)
        if not host_config:
            return {
                "success": False,
                "error": "HOST_UNREACHABLE",
                "message": f"Host '{host_name}' not found in profile"
            }
        
        # Build SSH command
        ssh_user = host_config.get("user", "root")
        ssh_host = host_config.get("host")
        ssh_key = host_config.get("key_path")
        ssh_port = host_config.get("port", 22)
        
        if not ssh_host:
            return {
                "success": False,
                "error": "HOST_UNREACHABLE",
                "message": f"Host config missing 'host' field"
            }
        
        # Build ssh command
        ssh_args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
        
        if ssh_key:
            ssh_args.extend(["-i", ssh_key])
        
        if ssh_port != 22:
            ssh_args.extend(["-p", str(ssh_port)])
        
        # Handle bastion if configured
        if self.profile.ssh_bastion:
            bastion_config = self.profile.ssh_bastion
            proxy_cmd = f"ssh -W %h:%p {bastion_config.get('user', 'root')}@{bastion_config.get('host')}"
            ssh_args.extend(["-o", f"ProxyCommand={proxy_cmd}"])
        
        ssh_target = f"{ssh_user}@{ssh_host}"
        ssh_args.append(ssh_target)
        ssh_args.append(command)
        
        try:
            # Execute command
            logger.debug(f"Executing SSH: {' '.join(ssh_args[:6])}... {command[:50]}")
            
            result = subprocess.run(
                ssh_args,
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            
            # Redact output
            stdout_redacted, stdout_redacted_flag = self.redact_secrets(result.stdout)
            stderr_redacted, stderr_redacted_flag = self.redact_secrets(result.stderr)
            
            if stdout_redacted_flag or stderr_redacted_flag:
                logger.warning("Output was redacted due to potential secrets")
            
            # Truncate output if too large (keep first/last 2KB)
            max_output_size = 2000
            if len(stdout_redacted) > max_output_size * 2:
                stdout_summary = (
                    stdout_redacted[:max_output_size] + 
                    "\n... [truncated] ...\n" + 
                    stdout_redacted[-max_output_size:]
                )
            else:
                stdout_summary = stdout_redacted
            
            if len(stderr_redacted) > max_output_size * 2:
                stderr_summary = (
                    stderr_redacted[:max_output_size] + 
                    "\n... [truncated] ...\n" + 
                    stderr_redacted[-max_output_size:]
                )
            else:
                stderr_summary = stderr_redacted
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": stdout_summary,
                "stderr": stderr_summary,
                "bytes_stdout": len(result.stdout),
                "bytes_stderr": len(result.stderr),
                "was_redacted": stdout_redacted_flag or stderr_redacted_flag
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "TIMEOUT",
                "message": f"Command timed out after {timeout_sec}s"
            }
        
        except Exception as e:
            logger.error(f"SSH execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": "HOST_UNREACHABLE",
                "message": str(e)
            }
    
    def tail_logs(
        self,
        host_name: str,
        log_path: str,
        lines: int = 100
    ) -> Dict[str, Any]:
        """
        Tail logs from remote host.
        
        Args:
            host_name: Host name
            log_path: Path to log file
            lines: Number of lines to fetch
            
        Returns:
            Log content
        """
        # Use tail command
        command = f"tail -n {lines} {log_path}"
        result = self.execute_command(host_name, command)
        
        if result.get("success"):
            return {
                "success": True,
                "content": result["stdout"],
                "path": log_path
            }
        else:
            return result
    
    def healthcheck(self, host_name: str) -> Dict[str, Any]:
        """
        Run healthcheck diagnostic bundle.
        
        Args:
            host_name: Host name
            
        Returns:
            Healthcheck results
        """
        # Collect diagnostics
        commands = {
            "uptime": "uptime",
            "load": "uptime | awk -F'load average:' '{print $2}'",
            "disk": "df -h",
            "memory": "free -h",
            "top_processes": "top -bn1 | head -20"
        }
        
        results = {}
        for name, cmd in commands.items():
            result = self.execute_command(host_name, cmd, timeout_sec=30)
            results[name] = result
        
        return {
            "success": True,
            "host": host_name,
            "diagnostics": results
        }