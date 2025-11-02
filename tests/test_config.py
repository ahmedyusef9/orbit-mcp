"""Tests for configuration management."""

import pytest
import tempfile
import os
from pathlib import Path
import yaml

from mcp.config import ConfigManager


@pytest.fixture
def temp_config_dir():
    """Create temporary configuration directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        yield config_path


def test_config_initialization(temp_config_dir):
    """Test configuration initialization."""
    config = ConfigManager(str(temp_config_dir))
    
    assert config.config_path.exists()
    assert config.config['version'] == '1.0'
    assert 'ssh_servers' in config.config
    assert 'docker_hosts' in config.config
    assert 'kubernetes_clusters' in config.config
    assert 'aliases' in config.config


def test_add_ssh_server(temp_config_dir):
    """Test adding SSH server configuration."""
    config = ConfigManager(str(temp_config_dir))
    
    config.add_ssh_server(
        name='test-server',
        host='test.example.com',
        user='testuser',
        key_path='~/.ssh/test_key',
        port=22
    )
    
    server = config.get_ssh_server('test-server')
    assert server is not None
    assert server['host'] == 'test.example.com'
    assert server['user'] == 'testuser'
    assert server['port'] == 22
    assert server['key_path'] == '~/.ssh/test_key'


def test_add_docker_host(temp_config_dir):
    """Test adding Docker host configuration."""
    config = ConfigManager(str(temp_config_dir))
    
    config.add_docker_host(
        name='test-docker',
        host='docker.example.com',
        connection_type='ssh'
    )
    
    host = config.get_docker_host('test-docker')
    assert host is not None
    assert host['host'] == 'docker.example.com'
    assert host['connection_type'] == 'ssh'


def test_add_k8s_cluster(temp_config_dir):
    """Test adding Kubernetes cluster configuration."""
    config = ConfigManager(str(temp_config_dir))
    
    config.add_k8s_cluster(
        name='test-k8s',
        kubeconfig_path='~/.kube/config',
        context='test-context'
    )
    
    cluster = config.get_k8s_cluster('test-k8s')
    assert cluster is not None
    assert cluster['kubeconfig_path'] == '~/.kube/config'
    assert cluster['context'] == 'test-context'


def test_add_alias(temp_config_dir):
    """Test adding command alias."""
    config = ConfigManager(str(temp_config_dir))
    
    config.add_alias('test-alias', 'echo "test"')
    
    alias = config.get_alias('test-alias')
    assert alias == 'echo "test"'


def test_list_profiles(temp_config_dir):
    """Test listing all profiles."""
    config = ConfigManager(str(temp_config_dir))
    
    config.add_ssh_server('server1', 'host1', 'user1')
    config.add_docker_host('docker1', 'dockerhost1')
    config.add_k8s_cluster('k8s1', '~/.kube/config')
    config.add_alias('alias1', 'command1')
    
    profiles = config.list_profiles()
    
    assert 'server1' in profiles['ssh_servers']
    assert 'docker1' in profiles['docker_hosts']
    assert 'k8s1' in profiles['k8s_clusters']
    assert 'alias1' in profiles['aliases']


def test_config_persistence(temp_config_dir):
    """Test that configuration persists across instances."""
    config1 = ConfigManager(str(temp_config_dir))
    config1.add_ssh_server('server1', 'host1', 'user1')
    
    # Create new instance with same config path
    config2 = ConfigManager(str(temp_config_dir))
    server = config2.get_ssh_server('server1')
    
    assert server is not None
    assert server['host'] == 'host1'


def test_config_file_permissions(temp_config_dir):
    """Test that configuration file has restricted permissions."""
    config = ConfigManager(str(temp_config_dir))
    
    # Check file permissions (should be 0600)
    stat_info = os.stat(config.config_path)
    permissions = oct(stat_info.st_mode)[-3:]
    
    # On Unix-like systems, should be 600
    if os.name != 'nt':  # Skip on Windows
        assert permissions == '600'


def test_update_server(temp_config_dir):
    """Test updating existing server configuration."""
    config = ConfigManager(str(temp_config_dir))
    
    config.add_ssh_server('server1', 'host1', 'user1', port=22)
    config.add_ssh_server('server1', 'host2', 'user2', port=2222)
    
    server = config.get_ssh_server('server1')
    assert server['host'] == 'host2'
    assert server['user'] == 'user2'
    assert server['port'] == 2222
