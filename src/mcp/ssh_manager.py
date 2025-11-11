"""SSH connection and command execution manager."""

import paramiko
import socket
import logging
from typing import Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SSHManager:
    """Manages SSH connections and remote command execution."""
    
    def __init__(self):
        """Initialize SSH manager."""
        self.connections = {}
    
    def connect(self, host: str, user: str, port: int = 22,
                key_path: Optional[str] = None,
                password: Optional[str] = None,
                timeout: int = 30) -> paramiko.SSHClient:
        """
        Establish SSH connection to remote host.
        
        Args:
            host: Remote host address
            user: SSH username
            port: SSH port (default 22)
            key_path: Path to SSH private key
            password: SSH password (use key-based auth instead when possible)
            timeout: Connection timeout in seconds
            
        Returns:
            SSH client instance
            
        Raises:
            ConnectionError: If connection fails
        """
        connection_key = f"{user}@{host}:{port}"
        
        # Return existing connection if available
        if connection_key in self.connections:
            client = self.connections[connection_key]
            try:
                # Test if connection is still alive
                transport = client.get_transport()
                if transport and transport.is_active():
                    logger.info(f"Reusing existing connection to {connection_key}")
                    return client
                else:
                    # Connection is dead, remove it
                    del self.connections[connection_key]
            except Exception:
                # Connection check failed, remove it
                del self.connections[connection_key]
        
        # Create new connection
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": user,
                "timeout": timeout,
                "allow_agent": True,
                "look_for_keys": True
            }
            
            if key_path:
                key_path_obj = Path(key_path).expanduser()
                if key_path_obj.exists():
                    try:
                        # Try different key types
                        for key_class in [paramiko.RSAKey, paramiko.Ed25519Key, 
                                         paramiko.ECDSAKey, paramiko.DSSKey]:
                            try:
                                pkey = key_class.from_private_key_file(str(key_path_obj))
                                connect_kwargs["pkey"] = pkey
                                break
                            except paramiko.ssh_exception.SSHException:
                                continue
                    except Exception as e:
                        logger.warning(f"Failed to load key from {key_path}: {e}")
                else:
                    logger.warning(f"Key file not found: {key_path}")
            
            if password:
                connect_kwargs["password"] = password
            
            client.connect(**connect_kwargs)
            self.connections[connection_key] = client
            logger.info(f"Successfully connected to {connection_key}")
            
            return client
            
        except paramiko.AuthenticationException as e:
            logger.error(f"Authentication failed for {connection_key}: {e}")
            raise ConnectionError(f"Authentication failed: {e}")
        except socket.timeout:
            logger.error(f"Connection timeout for {connection_key}")
            raise ConnectionError(f"Connection timeout to {host}:{port}")
        except socket.error as e:
            logger.error(f"Socket error for {connection_key}: {e}")
            raise ConnectionError(f"Socket error: {e}")
        except Exception as e:
            logger.error(f"Failed to connect to {connection_key}: {e}")
            raise ConnectionError(f"Connection failed: {e}")
    
    def execute_command(self, client: paramiko.SSHClient, command: str,
                       timeout: Optional[int] = None) -> Tuple[str, str, int]:
        """
        Execute command on remote host.
        
        Args:
            client: SSH client instance
            command: Command to execute
            timeout: Command execution timeout
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        try:
            logger.debug(f"Executing command: {command}")
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            
            logger.debug(f"Command exit code: {exit_code}")
            
            return stdout_data, stderr_data, exit_code
            
        except socket.timeout:
            logger.error("Command execution timeout")
            raise TimeoutError("Command execution timeout")
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise RuntimeError(f"Command execution failed: {e}")
    
    def execute_commands(self, client: paramiko.SSHClient, 
                        commands: List[str],
                        timeout: Optional[int] = None) -> List[Tuple[str, str, int]]:
        """
        Execute multiple commands sequentially.
        
        Args:
            client: SSH client instance
            commands: List of commands to execute
            timeout: Command execution timeout per command
            
        Returns:
            List of tuples (stdout, stderr, exit_code) for each command
        """
        results = []
        for cmd in commands:
            result = self.execute_command(client, cmd, timeout)
            results.append(result)
            # Stop on first failure
            if result[2] != 0:
                logger.warning(f"Command failed with exit code {result[2]}: {cmd}")
                break
        return results
    
    def get_file(self, client: paramiko.SSHClient, 
                 remote_path: str, local_path: str):
        """
        Download file from remote host.
        
        Args:
            client: SSH client instance
            remote_path: Path to file on remote host
            local_path: Local path to save file
        """
        try:
            sftp = client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            logger.info(f"Downloaded {remote_path} to {local_path}")
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise RuntimeError(f"File download failed: {e}")
    
    def put_file(self, client: paramiko.SSHClient,
                 local_path: str, remote_path: str):
        """
        Upload file to remote host.
        
        Args:
            client: SSH client instance
            local_path: Local file path
            remote_path: Path on remote host
        """
        try:
            sftp = client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            logger.info(f"Uploaded {local_path} to {remote_path}")
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise RuntimeError(f"File upload failed: {e}")
    
    def tail_log(self, client: paramiko.SSHClient, log_path: str,
                 lines: int = 50, follow: bool = False):
        """
        Tail log file from remote host.
        
        Args:
            client: SSH client instance
            log_path: Path to log file on remote host
            lines: Number of lines to retrieve
            follow: If True, continuously tail the file (like tail -f)
            
        Yields:
            Log lines
        """
        if follow:
            command = f"tail -f -n {lines} {log_path}"
            try:
                stdin, stdout, stderr = client.exec_command(command)
                
                # Read lines as they come
                for line in iter(stdout.readline, ""):
                    yield line.rstrip('\n')
                    
            except KeyboardInterrupt:
                logger.info("Stopped tailing log")
            except Exception as e:
                logger.error(f"Failed to tail log: {e}")
                raise
        else:
            command = f"tail -n {lines} {log_path}"
            stdout, stderr, exit_code = self.execute_command(client, command)
            
            if exit_code != 0:
                raise RuntimeError(f"Failed to tail log: {stderr}")
            
            for line in stdout.splitlines():
                yield line
    
    def close(self, host: str, user: str, port: int = 22):
        """Close SSH connection."""
        connection_key = f"{user}@{host}:{port}"
        if connection_key in self.connections:
            try:
                self.connections[connection_key].close()
                logger.info(f"Closed connection to {connection_key}")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                del self.connections[connection_key]
    
    def close_all(self):
        """Close all SSH connections."""
        for connection_key in list(self.connections.keys()):
            try:
                self.connections[connection_key].close()
            except Exception as e:
                logger.warning(f"Error closing connection {connection_key}: {e}")
        self.connections.clear()
        logger.info("Closed all connections")
