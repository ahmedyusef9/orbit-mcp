"""Kubernetes cluster management."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class KubernetesManager:
    """Manages Kubernetes cluster operations."""
    
    def __init__(self):
        """Initialize Kubernetes manager."""
        self.contexts = {}
        self.current_context = None
    
    def load_kubeconfig(self, kubeconfig_path: Optional[str] = None,
                       context: Optional[str] = None) -> str:
        """
        Load kubeconfig file.
        
        Args:
            kubeconfig_path: Path to kubeconfig file (defaults to ~/.kube/config)
            context: Specific context to use
            
        Returns:
            Active context name
        """
        try:
            if kubeconfig_path:
                kubeconfig_path = str(Path(kubeconfig_path).expanduser())
            else:
                kubeconfig_path = str(Path.home() / ".kube" / "config")
            
            config.load_kube_config(config_file=kubeconfig_path, context=context)
            
            # Get active context
            contexts, active_context = config.list_kube_config_contexts(config_file=kubeconfig_path)
            self.current_context = context or active_context['name']
            
            logger.info(f"Loaded kubeconfig from {kubeconfig_path}, context: {self.current_context}")
            return self.current_context
            
        except Exception as e:
            logger.error(f"Failed to load kubeconfig: {e}")
            raise RuntimeError(f"Failed to load kubeconfig: {e}")
    
    def list_contexts(self, kubeconfig_path: Optional[str] = None) -> List[str]:
        """List available contexts."""
        try:
            if kubeconfig_path:
                kubeconfig_path = str(Path(kubeconfig_path).expanduser())
            
            contexts, _ = config.list_kube_config_contexts(config_file=kubeconfig_path)
            return [ctx['name'] for ctx in contexts]
            
        except Exception as e:
            logger.error(f"Failed to list contexts: {e}")
            raise
    
    def switch_context(self, context: str, kubeconfig_path: Optional[str] = None):
        """Switch to different context."""
        self.load_kubeconfig(kubeconfig_path, context)
    
    def list_namespaces(self) -> List[str]:
        """List all namespaces."""
        try:
            v1 = client.CoreV1Api()
            namespaces = v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except ApiException as e:
            logger.error(f"Failed to list namespaces: {e}")
            raise
    
    def list_pods(self, namespace: str = "default",
                  label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List pods in namespace.
        
        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector filter
            
        Returns:
            List of pod information dictionaries
        """
        try:
            v1 = client.CoreV1Api()
            pods = v1.list_namespaced_pod(namespace, label_selector=label_selector)
            
            result = []
            for pod in pods.items:
                result.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "node": pod.spec.node_name,
                    "ip": pod.status.pod_ip,
                    "containers": len(pod.spec.containers),
                    "created": pod.metadata.creation_timestamp
                })
            
            logger.info(f"Found {len(result)} pods in namespace {namespace}")
            return result
            
        except ApiException as e:
            logger.error(f"Failed to list pods: {e}")
            raise
    
    def get_pod(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        """Get detailed pod information."""
        try:
            v1 = client.CoreV1Api()
            pod = v1.read_namespaced_pod(name, namespace)
            
            return {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "node": pod.spec.node_name,
                "ip": pod.status.pod_ip,
                "labels": pod.metadata.labels,
                "containers": [c.name for c in pod.spec.containers],
                "conditions": [{"type": c.type, "status": c.status} 
                             for c in (pod.status.conditions or [])],
                "created": pod.metadata.creation_timestamp
            }
            
        except ApiException as e:
            logger.error(f"Failed to get pod: {e}")
            raise
    
    def delete_pod(self, name: str, namespace: str = "default"):
        """Delete a pod."""
        try:
            v1 = client.CoreV1Api()
            v1.delete_namespaced_pod(name, namespace)
            logger.info(f"Deleted pod {name} in namespace {namespace}")
        except ApiException as e:
            logger.error(f"Failed to delete pod: {e}")
            raise
    
    def get_pod_logs(self, name: str, namespace: str = "default",
                    container: Optional[str] = None,
                    tail_lines: Optional[int] = 100,
                    follow: bool = False):
        """
        Get pod logs.
        
        Args:
            name: Pod name
            namespace: Namespace
            container: Container name (if pod has multiple containers)
            tail_lines: Number of lines to retrieve
            follow: Stream logs in real-time
            
        Returns:
            Log content
        """
        try:
            v1 = client.CoreV1Api()
            
            if follow:
                # For streaming, return a generator
                logs = v1.read_namespaced_pod_log(
                    name, namespace,
                    container=container,
                    tail_lines=tail_lines,
                    follow=True,
                    _preload_content=False
                )
                return logs.stream()
            else:
                logs = v1.read_namespaced_pod_log(
                    name, namespace,
                    container=container,
                    tail_lines=tail_lines
                )
                return logs
                
        except ApiException as e:
            logger.error(f"Failed to get pod logs: {e}")
            raise
    
    def list_services(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """List services in namespace."""
        try:
            v1 = client.CoreV1Api()
            services = v1.list_namespaced_service(namespace)
            
            result = []
            for svc in services.items:
                result.append({
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "external_ips": svc.spec.external_i_ps or [],
                    "ports": [{"port": p.port, "protocol": p.protocol, 
                              "target_port": str(p.target_port)} 
                             for p in (svc.spec.ports or [])],
                    "selector": svc.spec.selector
                })
            
            return result
            
        except ApiException as e:
            logger.error(f"Failed to list services: {e}")
            raise
    
    def list_deployments(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """List deployments in namespace."""
        try:
            apps_v1 = client.AppsV1Api()
            deployments = apps_v1.list_namespaced_deployment(namespace)
            
            result = []
            for deploy in deployments.items:
                result.append({
                    "name": deploy.metadata.name,
                    "namespace": deploy.metadata.namespace,
                    "replicas": deploy.spec.replicas,
                    "ready_replicas": deploy.status.ready_replicas or 0,
                    "available_replicas": deploy.status.available_replicas or 0,
                    "updated_replicas": deploy.status.updated_replicas or 0,
                    "labels": deploy.metadata.labels,
                    "selector": deploy.spec.selector.match_labels,
                    "created": deploy.metadata.creation_timestamp
                })
            
            return result
            
        except ApiException as e:
            logger.error(f"Failed to list deployments: {e}")
            raise
    
    def scale_deployment(self, name: str, replicas: int, 
                        namespace: str = "default"):
        """Scale deployment to specified replica count."""
        try:
            apps_v1 = client.AppsV1Api()
            
            # Get current deployment
            deployment = apps_v1.read_namespaced_deployment(name, namespace)
            
            # Update replicas
            deployment.spec.replicas = replicas
            
            # Apply changes
            apps_v1.patch_namespaced_deployment(name, namespace, deployment)
            
            logger.info(f"Scaled deployment {name} to {replicas} replicas")
            
        except ApiException as e:
            logger.error(f"Failed to scale deployment: {e}")
            raise
    
    def restart_deployment(self, name: str, namespace: str = "default"):
        """Restart deployment by updating restart annotation."""
        try:
            apps_v1 = client.AppsV1Api()
            
            # Get current deployment
            deployment = apps_v1.read_namespaced_deployment(name, namespace)
            
            # Add restart annotation
            from datetime import datetime
            if not deployment.spec.template.metadata.annotations:
                deployment.spec.template.metadata.annotations = {}
            
            deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = \
                datetime.now().isoformat()
            
            # Apply changes
            apps_v1.patch_namespaced_deployment(name, namespace, deployment)
            
            logger.info(f"Restarted deployment {name}")
            
        except ApiException as e:
            logger.error(f"Failed to restart deployment: {e}")
            raise
    
    def get_node_info(self) -> List[Dict[str, Any]]:
        """Get information about cluster nodes."""
        try:
            v1 = client.CoreV1Api()
            nodes = v1.list_node()
            
            result = []
            for node in nodes.items:
                result.append({
                    "name": node.metadata.name,
                    "status": [c.type for c in node.status.conditions if c.status == "True"],
                    "capacity": node.status.capacity,
                    "allocatable": node.status.allocatable,
                    "os": node.status.node_info.os_image,
                    "kernel": node.status.node_info.kernel_version,
                    "container_runtime": node.status.node_info.container_runtime_version
                })
            
            return result
            
        except ApiException as e:
            logger.error(f"Failed to get node info: {e}")
            raise
    
    def execute_in_pod(self, name: str, command: List[str],
                      namespace: str = "default",
                      container: Optional[str] = None) -> str:
        """
        Execute command in a pod.
        
        Args:
            name: Pod name
            command: Command to execute (as list)
            namespace: Namespace
            container: Container name (if multiple containers)
            
        Returns:
            Command output
        """
        try:
            from kubernetes.stream import stream
            
            v1 = client.CoreV1Api()
            
            resp = stream(
                v1.connect_get_namespaced_pod_exec,
                name,
                namespace,
                container=container,
                command=command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )
            
            return resp
            
        except ApiException as e:
            logger.error(f"Failed to execute command in pod: {e}")
            raise
