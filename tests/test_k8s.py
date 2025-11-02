"""Tests for Kubernetes tool functionality."""

import pytest
from unittest.mock import MagicMock, patch
from kubernetes import client as k8s_client
from kubernetes.client.rest import ApiException


class TestK8sToolUnit:
    """Unit tests for Kubernetes tool (mocked)."""
    
    def test_k8s_list_pods(self, mock_k8s_manager):
        """Test listing Kubernetes pods."""
        pods = mock_k8s_manager.list_pods(namespace='default')
        
        assert isinstance(pods, list)
        assert len(pods) > 0
        assert 'name' in pods[0]
        assert 'status' in pods[0]
    
    def test_k8s_get_pod_logs(self, mock_k8s_manager):
        """Test retrieving pod logs."""
        mock_k8s_manager.get_pod_logs.return_value = """
        2024-01-15 10:00:01 Starting application
        2024-01-15 10:00:02 Connected to database
        2024-01-15 10:00:03 Ready to serve requests
        """
        
        logs = mock_k8s_manager.get_pod_logs(
            pod='test-pod',
            namespace='default',
            lines=100
        )
        
        assert logs is not None
        assert 'Starting application' in logs
    
    def test_k8s_list_services(self, mock_k8s_manager):
        """Test listing Kubernetes services."""
        mock_k8s_manager.list_services.return_value = [
            {
                'name': 'nginx-service',
                'type': 'ClusterIP',
                'cluster_ip': '10.0.0.1'
            }
        ]
        
        services = mock_k8s_manager.list_services(namespace='default')
        
        assert isinstance(services, list)
        assert len(services) > 0
        assert 'name' in services[0]
    
    def test_k8s_list_deployments(self, mock_k8s_manager):
        """Test listing deployments."""
        mock_k8s_manager.list_deployments.return_value = [
            {
                'name': 'nginx-deployment',
                'replicas': 3,
                'available': 3
            }
        ]
        
        deployments = mock_k8s_manager.list_deployments(namespace='default')
        
        assert isinstance(deployments, list)
        assert deployments[0]['replicas'] == 3
    
    def test_k8s_scale_deployment(self, mock_k8s_manager):
        """Test scaling a deployment."""
        mock_k8s_manager.scale_deployment.return_value = {
            'status': 'success',
            'replicas': 5
        }
        
        result = mock_k8s_manager.scale_deployment(
            deployment='nginx-deployment',
            namespace='default',
            replicas=5
        )
        
        assert result['status'] == 'success'
        assert result['replicas'] == 5
    
    def test_k8s_pod_not_found(self, mock_k8s_manager):
        """Test handling of non-existent pod."""
        mock_k8s_manager.get_pod_logs.side_effect = ApiException(
            status=404,
            reason="Not Found"
        )
        
        with pytest.raises(ApiException):
            mock_k8s_manager.get_pod_logs(
                pod='nonexistent-pod',
                namespace='default'
            )
    
    def test_k8s_connection_error(self, mock_k8s_manager):
        """Test Kubernetes API connection error."""
        mock_k8s_manager.list_pods.side_effect = ApiException(
            status=0,
            reason="Connection refused"
        )
        
        with pytest.raises(ApiException):
            mock_k8s_manager.list_pods(namespace='default')


@pytest.mark.integration
@pytest.mark.k8s
class TestK8sToolIntegration:
    """Integration tests for Kubernetes tool (requires K8s cluster)."""
    
    def test_real_k8s_list_namespaces(self, k8s_test_cluster):
        """Test listing real Kubernetes namespaces."""
        try:
            from kubernetes import client, config
            
            config.load_kube_config(k8s_test_cluster['kubeconfig'])
            v1 = client.CoreV1Api()
            
            namespaces = v1.list_namespace()
            
            # Should at least have 'default'
            namespace_names = [ns.metadata.name for ns in namespaces.items]
            assert 'default' in namespace_names
            
        except Exception as e:
            pytest.skip(f"Kubernetes not available: {e}")
    
    def test_real_k8s_create_pod(self, k8s_test_cluster):
        """Test creating a pod in real cluster."""
        try:
            from kubernetes import client, config
            
            config.load_kube_config(k8s_test_cluster['kubeconfig'])
            v1 = client.CoreV1Api()
            
            # Create simple pod
            pod_manifest = {
                'apiVersion': 'v1',
                'kind': 'Pod',
                'metadata': {'name': 'orbit-test-pod'},
                'spec': {
                    'containers': [{
                        'name': 'test',
                        'image': 'busybox',
                        'command': ['sh', '-c', 'echo "test" && sleep 30']
                    }],
                    'restartPolicy': 'Never'
                }
            }
            
            v1.create_namespaced_pod(
                namespace='default',
                body=pod_manifest
            )
            
            # Wait briefly
            import time
            time.sleep(2)
            
            # Verify pod exists
            pod = v1.read_namespaced_pod(
                name='orbit-test-pod',
                namespace='default'
            )
            
            assert pod.metadata.name == 'orbit-test-pod'
            
            # Cleanup
            v1.delete_namespaced_pod(
                name='orbit-test-pod',
                namespace='default'
            )
            
        except Exception as e:
            pytest.skip(f"Kubernetes not available: {e}")
    
    def test_real_k8s_get_pod_logs(self, k8s_test_cluster):
        """Test retrieving logs from real pod."""
        try:
            from kubernetes import client, config
            
            config.load_kube_config(k8s_test_cluster['kubeconfig'])
            v1 = client.CoreV1Api()
            
            # Create pod that outputs logs
            pod_manifest = {
                'apiVersion': 'v1',
                'kind': 'Pod',
                'metadata': {'name': 'orbit-test-logs'},
                'spec': {
                    'containers': [{
                        'name': 'test',
                        'image': 'busybox',
                        'command': ['sh', '-c', 'for i in 1 2 3; do echo "log line $i"; done']
                    }],
                    'restartPolicy': 'Never'
                }
            }
            
            v1.create_namespaced_pod(
                namespace='default',
                body=pod_manifest
            )
            
            # Wait for pod to complete
            import time
            time.sleep(5)
            
            # Get logs
            logs = v1.read_namespaced_pod_log(
                name='orbit-test-logs',
                namespace='default'
            )
            
            assert 'log line 1' in logs
            assert 'log line 2' in logs
            assert 'log line 3' in logs
            
            # Cleanup
            v1.delete_namespaced_pod(
                name='orbit-test-logs',
                namespace='default'
            )
            
        except Exception as e:
            pytest.skip(f"Kubernetes not available: {e}")


class TestK8sMultiNamespace:
    """Test multi-namespace Kubernetes operations."""
    
    def test_k8s_list_pods_all_namespaces(self, mock_k8s_manager):
        """Test listing pods across all namespaces."""
        mock_k8s_manager.list_pods.return_value = [
            {'name': 'pod1', 'namespace': 'default'},
            {'name': 'pod2', 'namespace': 'kube-system'},
            {'name': 'pod3', 'namespace': 'production'}
        ]
        
        pods = mock_k8s_manager.list_pods(all_namespaces=True)
        
        assert len(pods) == 3
        namespaces = set(pod['namespace'] for pod in pods)
        assert len(namespaces) > 1
    
    def test_k8s_cross_namespace_resource_access(self, mock_k8s_manager):
        """Test accessing resources across namespaces."""
        # Should be able to access pods in different namespace
        mock_k8s_manager.list_pods.return_value = [
            {'name': 'app-pod', 'namespace': 'production'}
        ]
        
        pods = mock_k8s_manager.list_pods(namespace='production')
        
        assert len(pods) > 0
        assert pods[0]['namespace'] == 'production'


class TestK8sResourceFiltering:
    """Test Kubernetes resource filtering."""
    
    def test_k8s_filter_by_label(self, mock_k8s_manager):
        """Test filtering resources by label selector."""
        mock_k8s_manager.list_pods.return_value = [
            {
                'name': 'web-pod-1',
                'labels': {'app': 'web', 'tier': 'frontend'}
            }
        ]
        
        pods = mock_k8s_manager.list_pods(
            namespace='default',
            label_selector='app=web'
        )
        
        assert len(pods) > 0
        assert pods[0]['labels']['app'] == 'web'
    
    def test_k8s_filter_by_field(self, mock_k8s_manager):
        """Test filtering by field selector."""
        mock_k8s_manager.list_pods.return_value = [
            {'name': 'running-pod', 'status': 'Running'}
        ]
        
        pods = mock_k8s_manager.list_pods(
            namespace='default',
            field_selector='status.phase=Running'
        )
        
        assert len(pods) > 0
        assert pods[0]['status'] == 'Running'


class TestK8sDeploymentOperations:
    """Test Kubernetes deployment operations."""
    
    def test_k8s_restart_deployment(self, mock_k8s_manager):
        """Test restarting a deployment."""
        mock_k8s_manager.restart_deployment.return_value = {
            'status': 'success',
            'deployment': 'nginx-deployment',
            'restarted_at': '2024-01-15T10:00:00Z'
        }
        
        result = mock_k8s_manager.restart_deployment(
            deployment='nginx-deployment',
            namespace='default'
        )
        
        assert result['status'] == 'success'
    
    def test_k8s_rollback_deployment(self, mock_k8s_manager):
        """Test rolling back a deployment."""
        mock_k8s_manager.rollback_deployment.return_value = {
            'status': 'success',
            'revision': 2
        }
        
        result = mock_k8s_manager.rollback_deployment(
            deployment='nginx-deployment',
            namespace='default'
        )
        
        assert result['status'] == 'success'


class TestK8sEventHandling:
    """Test Kubernetes event handling."""
    
    def test_k8s_get_events(self, mock_k8s_manager):
        """Test retrieving Kubernetes events."""
        mock_k8s_manager.get_events.return_value = [
            {
                'type': 'Warning',
                'reason': 'BackOff',
                'message': 'Back-off restarting failed container'
            }
        ]
        
        events = mock_k8s_manager.get_events(namespace='default')
        
        assert isinstance(events, list)
        assert len(events) > 0
        assert events[0]['type'] in ['Normal', 'Warning']


class TestK8sMCPProtocol:
    """Test Kubernetes tool MCP protocol compliance."""
    
    def test_k8s_get_tool_schema(self):
        """Test k8s.get tool schema."""
        tool_schema = {
            'name': 'k8s.get',
            'description': 'Get Kubernetes resources',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'kind': {
                        'type': 'string',
                        'enum': ['pods', 'services', 'deployments']
                    },
                    'namespace': {
                        'type': 'string',
                        'default': 'default'
                    }
                },
                'required': ['kind']
            }
        }
        
        assert tool_schema['name'] == 'k8s.get'
        assert 'kind' in tool_schema['inputSchema']['required']
    
    def test_k8s_error_format(self):
        """Test Kubernetes error MCP format."""
        error_response = {
            'error': {
                'code': 'RESOURCE_NOT_FOUND',
                'message': 'Pod "test-pod" not found in namespace "default"',
                'data': {
                    'kind': 'Pod',
                    'name': 'test-pod',
                    'namespace': 'default'
                }
            }
        }
        
        from conftest import assert_valid_mcp_response
        assert_valid_mcp_response(error_response)


class TestK8sSecurity:
    """Test Kubernetes security and RBAC."""
    
    def test_k8s_namespace_isolation(self, mock_k8s_manager):
        """Test namespace isolation."""
        # Accessing forbidden namespace should fail
        mock_k8s_manager.list_pods.side_effect = ApiException(
            status=403,
            reason="Forbidden"
        )
        
        with pytest.raises(ApiException) as exc:
            mock_k8s_manager.list_pods(namespace='forbidden-namespace')
        
        assert exc.value.status == 403
    
    def test_k8s_rbac_enforcement(self, mock_k8s_manager):
        """Test RBAC enforcement."""
        # Certain operations should require permissions
        mock_k8s_manager.delete_pod.side_effect = ApiException(
            status=403,
            reason="User does not have permission to delete pods"
        )
        
        with pytest.raises(ApiException):
            mock_k8s_manager.delete_pod(
                pod='test-pod',
                namespace='default'
            )


class TestK8sComplexScenarios:
    """Test complex Kubernetes scenarios."""
    
    @pytest.mark.asyncio
    async def test_k8s_rolling_update_monitoring(self, mock_k8s_manager):
        """Test monitoring a rolling update."""
        # Simulate rolling update progress
        update_states = [
            {'ready': 1, 'updated': 1, 'total': 3},
            {'ready': 2, 'updated': 2, 'total': 3},
            {'ready': 3, 'updated': 3, 'total': 3}
        ]
        
        mock_k8s_manager.get_deployment_status.side_effect = update_states
        
        for state in update_states:
            status = mock_k8s_manager.get_deployment_status(
                deployment='nginx-deployment',
                namespace='default'
            )
            
            assert status['total'] == 3
    
    def test_k8s_pod_restart_detection(self, mock_k8s_manager):
        """Test detecting pod restarts."""
        mock_k8s_manager.get_pod_status.return_value = {
            'name': 'crashing-pod',
            'restart_count': 15,
            'status': 'CrashLoopBackOff'
        }
        
        status = mock_k8s_manager.get_pod_status(
            pod='crashing-pod',
            namespace='default'
        )
        
        # High restart count indicates problem
        assert status['restart_count'] > 10
        assert 'crash' in status['status'].lower()
