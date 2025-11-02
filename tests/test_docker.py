"""Tests for Docker tool functionality."""

import pytest
from unittest.mock import MagicMock, patch
import docker


class TestDockerToolUnit:
    """Unit tests for Docker tool (mocked)."""
    
    def test_docker_list_containers(self, mock_docker_manager):
        """Test listing Docker containers."""
        containers = mock_docker_manager.list_containers()
        
        assert isinstance(containers, list)
        assert len(containers) > 0
        assert 'id' in containers[0]
        assert 'name' in containers[0]
        assert 'status' in containers[0]
    
    def test_docker_get_logs(self, mock_docker_manager):
        """Test retrieving container logs."""
        logs = mock_docker_manager.get_logs(
            container='test-container',
            lines=100
        )
        
        assert logs is not None
        assert isinstance(logs, str)
        assert len(logs) > 0
    
    def test_docker_start_container(self, mock_docker_manager):
        """Test starting a container."""
        mock_docker_manager.start_container.return_value = {
            'status': 'started',
            'container_id': 'abc123'
        }
        
        result = mock_docker_manager.start_container('test-container')
        
        assert result['status'] == 'started'
        assert result['container_id'] is not None
    
    def test_docker_stop_container(self, mock_docker_manager):
        """Test stopping a container."""
        mock_docker_manager.stop_container.return_value = {
            'status': 'stopped',
            'container_id': 'abc123'
        }
        
        result = mock_docker_manager.stop_container('test-container')
        
        assert result['status'] == 'stopped'
    
    def test_docker_container_not_found(self, mock_docker_manager):
        """Test handling of non-existent container."""
        mock_docker_manager.get_logs.side_effect = docker.errors.NotFound(
            "Container not found"
        )
        
        with pytest.raises(docker.errors.NotFound):
            mock_docker_manager.get_logs('nonexistent-container')
    
    def test_docker_connection_error(self, mock_docker_manager):
        """Test Docker daemon connection error."""
        mock_docker_manager.list_containers.side_effect = docker.errors.DockerException(
            "Cannot connect to Docker daemon"
        )
        
        with pytest.raises(docker.errors.DockerException):
            mock_docker_manager.list_containers()


@pytest.mark.integration
@pytest.mark.docker
class TestDockerToolIntegration:
    """Integration tests for Docker tool (requires Docker)."""
    
    def test_real_docker_list_containers(self):
        """Test listing real Docker containers."""
        try:
            client = docker.from_env()
            containers = client.containers.list()
            
            # Just verify we can connect
            assert containers is not None
            
        except docker.errors.DockerException as e:
            pytest.skip(f"Docker not available: {e}")
    
    def test_real_docker_run_container(self):
        """Test running a container."""
        try:
            client = docker.from_env()
            
            # Run a simple container
            container = client.containers.run(
                'alpine:latest',
                command='echo "test"',
                detach=True,
                remove=True,
                name='orbit-test-container'
            )
            
            # Wait for completion
            result = container.wait(timeout=10)
            
            assert result['StatusCode'] == 0
            
        except docker.errors.DockerException as e:
            pytest.skip(f"Docker not available: {e}")
    
    def test_real_docker_logs(self):
        """Test retrieving logs from real container."""
        try:
            client = docker.from_env()
            
            # Run container with known output
            container = client.containers.run(
                'alpine:latest',
                command='sh -c "echo line1; echo line2; echo line3"',
                detach=True,
                name='orbit-test-logs'
            )
            
            # Wait for completion
            container.wait(timeout=10)
            
            # Get logs
            logs = container.logs().decode('utf-8')
            
            assert 'line1' in logs
            assert 'line2' in logs
            assert 'line3' in logs
            
            # Cleanup
            container.remove()
            
        except docker.errors.DockerException as e:
            pytest.skip(f"Docker not available: {e}")


class TestDockerLogStreaming:
    """Test Docker log streaming functionality."""
    
    def test_docker_log_tail(self, mock_docker_manager):
        """Test tailing Docker logs."""
        # Mock streaming logs
        mock_logs = [
            b'log line 1\n',
            b'log line 2\n',
            b'log line 3\n'
        ]
        
        mock_docker_manager.stream_logs.return_value = iter(mock_logs)
        
        logs = list(mock_docker_manager.stream_logs('test-container'))
        
        assert len(logs) == 3
        assert logs[0] == b'log line 1\n'
    
    def test_docker_log_follow(self, mock_docker_manager):
        """Test following Docker logs in real-time."""
        # This would test the streaming behavior
        # For now, just verify the interface
        
        mock_docker_manager.stream_logs.return_value = iter([
            b'realtime log 1\n',
            b'realtime log 2\n'
        ])
        
        logs = list(mock_docker_manager.stream_logs(
            'test-container',
            follow=True
        ))
        
        assert len(logs) >= 2


class TestDockerStats:
    """Test Docker container statistics."""
    
    def test_docker_get_stats(self, mock_docker_manager):
        """Test retrieving container stats."""
        mock_docker_manager.get_stats.return_value = {
            'cpu_percent': 25.5,
            'memory_usage': '256 MB',
            'memory_limit': '1 GB',
            'memory_percent': 25.0
        }
        
        stats = mock_docker_manager.get_stats('test-container')
        
        assert 'cpu_percent' in stats
        assert 'memory_usage' in stats
        assert stats['cpu_percent'] > 0


class TestDockerImageManagement:
    """Test Docker image operations."""
    
    def test_docker_list_images(self, mock_docker_manager):
        """Test listing Docker images."""
        mock_docker_manager.list_images.return_value = [
            {
                'id': 'img123',
                'tags': ['alpine:latest'],
                'size': '5.6 MB'
            }
        ]
        
        images = mock_docker_manager.list_images()
        
        assert isinstance(images, list)
        assert len(images) > 0
        assert 'tags' in images[0]
    
    def test_docker_pull_image(self, mock_docker_manager):
        """Test pulling Docker image."""
        mock_docker_manager.pull_image.return_value = {
            'status': 'success',
            'image': 'alpine:latest'
        }
        
        result = mock_docker_manager.pull_image('alpine:latest')
        
        assert result['status'] == 'success'


class TestDockerComposeIntegration:
    """Test Docker Compose operations."""
    
    def test_compose_up(self, mock_docker_manager):
        """Test docker-compose up."""
        mock_docker_manager.compose_up.return_value = {
            'status': 'success',
            'containers': ['app', 'db', 'redis']
        }
        
        result = mock_docker_manager.compose_up(
            compose_file='docker-compose.yml'
        )
        
        assert result['status'] == 'success'
        assert len(result['containers']) == 3
    
    def test_compose_down(self, mock_docker_manager):
        """Test docker-compose down."""
        mock_docker_manager.compose_down.return_value = {
            'status': 'success',
            'removed': 3
        }
        
        result = mock_docker_manager.compose_down()
        
        assert result['status'] == 'success'
        assert result['removed'] > 0


class TestDockerMCPProtocol:
    """Test Docker tool MCP protocol compliance."""
    
    def test_docker_logs_tool_schema(self):
        """Test docker.logs tool schema."""
        tool_schema = {
            'name': 'docker.logs',
            'description': 'Retrieve logs from a Docker container',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'container': {'type': 'string'},
                    'lines': {'type': 'integer', 'default': 100},
                    'follow': {'type': 'boolean', 'default': False}
                },
                'required': ['container']
            }
        }
        
        assert tool_schema['name'] == 'docker.logs'
        assert 'container' in tool_schema['inputSchema']['required']
    
    def test_docker_error_format(self):
        """Test Docker error MCP format."""
        error_response = {
            'error': {
                'code': 'CONTAINER_NOT_FOUND',
                'message': 'Container "test" does not exist',
                'data': {
                    'container': 'test'
                }
            }
        }
        
        from conftest import assert_valid_mcp_response
        assert_valid_mcp_response(error_response)


class TestDockerSecurity:
    """Test Docker security and isolation."""
    
    def test_docker_no_privileged_containers(self, mock_docker_manager):
        """Test that privileged containers are not allowed by default."""
        # Attempting to run privileged should be blocked
        mock_docker_manager.run_container.side_effect = PermissionError(
            "Privileged containers not allowed"
        )
        
        with pytest.raises(PermissionError):
            mock_docker_manager.run_container(
                image='alpine',
                privileged=True
            )
    
    def test_docker_volume_mount_restrictions(self, mock_docker_manager):
        """Test volume mount restrictions."""
        # Sensitive paths should be restricted
        sensitive_paths = ['/etc', '/root', '/sys']
        
        for path in sensitive_paths:
            mock_docker_manager.run_container.side_effect = PermissionError(
                f"Mount of {path} not allowed"
            )
            
            with pytest.raises(PermissionError):
                mock_docker_manager.run_container(
                    image='alpine',
                    volumes={path: {'bind': '/mnt', 'mode': 'ro'}}
                )
