# MCP Server - Usage Examples

This document provides practical examples and common use cases for MCP Server.

## Table of Contents

- [Initial Setup](#initial-setup)
- [SSH Operations](#ssh-operations)
- [Docker Management](#docker-management)
- [Kubernetes Operations](#kubernetes-operations)
- [Common Workflows](#common-workflows)
- [Advanced Usage](#advanced-usage)

## Initial Setup

### First-Time Configuration

```bash
# Initialize MCP configuration
mcp config init

# Add your first server
mcp config add-ssh prod-web \
    web1.example.com \
    deploy-user \
    --key ~/.ssh/deploy_key \
    --port 22

# Verify configuration
mcp config list
```

### Multi-Environment Setup

```bash
# Development environment
mcp config add-ssh dev-app dev.example.com devuser --key ~/.ssh/dev_key
mcp config add-k8s dev-k8s ~/.kube/config --context dev-cluster

# Staging environment
mcp config add-ssh staging-app staging.example.com stageuser --key ~/.ssh/stage_key
mcp config add-k8s staging-k8s ~/.kube/config --context staging-cluster

# Production environment
mcp config add-ssh prod-app prod.example.com produser --key ~/.ssh/prod_key
mcp config add-k8s prod-k8s ~/.kube/config --context prod-cluster
```

## SSH Operations

### Basic Command Execution

```bash
# Check system uptime
mcp ssh exec prod-web "uptime"

# Check disk usage
mcp ssh exec prod-web "df -h"

# Check memory usage
mcp ssh exec prod-web "free -h"

# View running processes
mcp ssh exec prod-web "ps aux | grep nginx"
```

### Service Management

```bash
# Check service status
mcp ssh exec prod-web "systemctl status nginx"

# Restart a service (using alias)
mcp config add-alias restart-nginx "sudo systemctl restart nginx"
mcp ssh exec prod-web restart-nginx

# View service logs
mcp ssh exec prod-web "journalctl -u nginx -n 50"
```

### Log Monitoring

```bash
# View application logs
mcp ssh logs prod-web /var/log/app/application.log -n 100

# Follow logs in real-time
mcp ssh logs prod-web /var/log/app/error.log -f

# Multiple log sources (use separate terminals)
# Terminal 1:
mcp ssh logs prod-web /var/log/nginx/access.log -f

# Terminal 2:
mcp ssh logs prod-web /var/log/nginx/error.log -f
```

### Troubleshooting Scenarios

#### Debugging High CPU Usage

```bash
# Check load average
mcp ssh exec prod-web "uptime"

# Find top CPU consumers
mcp ssh exec prod-web "top -b -n 1 | head -20"

# Detailed process information
mcp ssh exec prod-web "ps aux --sort=-%cpu | head -10"

# Check for zombie processes
mcp ssh exec prod-web "ps aux | grep -w Z"
```

#### Investigating Disk Space Issues

```bash
# Check disk usage
mcp ssh exec prod-web "df -h"

# Find large files
mcp ssh exec prod-web "du -h /var/log | sort -h | tail -20"

# Check inode usage
mcp ssh exec prod-web "df -i"

# Find large directories
mcp ssh exec prod-web "du -sh /* | sort -h"
```

#### Network Diagnostics

```bash
# Check listening ports
mcp ssh exec prod-web "netstat -tuln"

# Check established connections
mcp ssh exec prod-web "netstat -anp | grep ESTABLISHED"

# Test connectivity
mcp ssh exec prod-web "ping -c 4 google.com"

# Check DNS resolution
mcp ssh exec prod-web "dig example.com"

# Test specific port
mcp ssh exec prod-web "nc -zv database.example.com 5432"
```

## Docker Management

### Container Lifecycle

```bash
# List all containers
mcp docker ps -a

# Start a stopped container
mcp docker start myapp-container

# Stop a running container
mcp docker stop myapp-container

# Restart a container
mcp docker restart myapp-container
```

### Container Monitoring

```bash
# View container logs
mcp docker logs myapp-container -n 100

# Follow container logs
mcp docker logs myapp-container -f

# Filter logs
mcp docker logs myapp-container -n 500 | grep ERROR
```

### Container Troubleshooting

```bash
# Check container details
mcp ssh exec prod-web "docker inspect myapp-container"

# View container resource usage
mcp ssh exec prod-web "docker stats --no-stream myapp-container"

# Execute command in container
mcp ssh exec prod-web "docker exec myapp-container ps aux"

# Access container shell
mcp ssh exec prod-web "docker exec -it myapp-container /bin/bash"

# Check container logs for errors
mcp docker logs myapp-container -n 1000 | grep -i error
```

### Multi-Container Applications

```bash
# List all containers for an application
mcp docker ps | grep myapp

# Restart all containers of an app (using alias)
mcp config add-alias restart-myapp "docker-compose -f /app/myapp/docker-compose.yml restart"
mcp ssh exec prod-web restart-myapp

# View logs from multiple containers
mcp ssh exec prod-web "docker-compose -f /app/myapp/docker-compose.yml logs --tail=100"
```

## Kubernetes Operations

### Cluster Management

```bash
# List available contexts
mcp k8s contexts

# Switch to production cluster
mcp k8s use prod-k8s

# List namespaces
mcp ssh exec prod-web "kubectl get namespaces"
```

### Pod Operations

```bash
# List pods in default namespace
mcp k8s pods

# List pods in specific namespace
mcp k8s pods -n production

# Get detailed pod information
mcp ssh exec prod-web "kubectl describe pod myapp-pod -n production"

# View pod logs
mcp k8s logs myapp-pod -n production

# Follow pod logs
mcp k8s logs myapp-pod -f -n production

# Logs from specific container
mcp k8s logs myapp-pod -c app-container -n production
```

### Service and Deployment Management

```bash
# List services
mcp k8s services -n production

# List deployments
mcp k8s deployments -n production

# Scale deployment
mcp k8s scale myapp-deployment 5 -n production

# Restart deployment
mcp k8s restart myapp-deployment -n production

# Check rollout status
mcp ssh exec prod-web "kubectl rollout status deployment/myapp-deployment -n production"
```

### Troubleshooting Kubernetes

#### Pod Not Starting

```bash
# Check pod status
mcp k8s pods -n production

# Get detailed pod information
mcp ssh exec prod-web "kubectl describe pod failing-pod -n production"

# Check events
mcp ssh exec prod-web "kubectl get events -n production --sort-by='.lastTimestamp'"

# View pod logs
mcp k8s logs failing-pod -n production

# Check previous container logs (if pod restarted)
mcp ssh exec prod-web "kubectl logs failing-pod -n production --previous"
```

#### Service Not Accessible

```bash
# Check service
mcp ssh exec prod-web "kubectl describe service myapp-service -n production"

# Check endpoints
mcp ssh exec prod-web "kubectl get endpoints myapp-service -n production"

# Check network policies
mcp ssh exec prod-web "kubectl get networkpolicies -n production"

# Test service from within cluster
mcp ssh exec prod-web "kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- myapp-service:80"
```

#### Resource Issues

```bash
# Check node resources
mcp ssh exec prod-web "kubectl top nodes"

# Check pod resource usage
mcp ssh exec prod-web "kubectl top pods -n production"

# View resource quotas
mcp ssh exec prod-web "kubectl get resourcequota -n production"

# View limit ranges
mcp ssh exec prod-web "kubectl get limitrange -n production"
```

## Common Workflows

### Deployment Workflow

```bash
# 1. Check current deployment status
mcp k8s deployments -n production

# 2. Update application
mcp ssh exec prod-web "kubectl set image deployment/myapp myapp=myapp:v2.0 -n production"

# 3. Watch rollout
mcp ssh exec prod-web "kubectl rollout status deployment/myapp -n production"

# 4. Verify deployment
mcp k8s pods -n production

# 5. Check logs
mcp k8s logs myapp-pod-xyz -n production -n 50

# 6. Rollback if needed
# mcp ssh exec prod-web "kubectl rollout undo deployment/myapp -n production"
```

### Troubleshooting Workflow

```bash
# 1. Check system health
mcp ssh exec prod-web "uptime && free -h && df -h"

# 2. Check application logs
mcp ssh logs prod-web /var/log/app/error.log -n 100

# 3. Check container status
mcp docker ps

# 4. Check Kubernetes pods
mcp k8s pods -n production

# 5. Investigate specific pod
mcp k8s logs problem-pod -n production --tail 500

# 6. Get detailed info
mcp ssh exec prod-web "kubectl describe pod problem-pod -n production"

# 7. Check recent events
mcp ssh exec prod-web "kubectl get events -n production --sort-by='.lastTimestamp' | tail -20"
```

### Database Maintenance

```bash
# Check database service
mcp ssh exec db-server "systemctl status postgresql"

# View database logs
mcp ssh logs db-server /var/log/postgresql/postgresql.log -n 100

# Create backup (using alias)
mcp config add-alias db-backup "pg_dump -U postgres mydb > /backup/mydb-\$(date +%Y%m%d).sql"
mcp ssh exec db-server db-backup

# Check backup status
mcp ssh exec db-server "ls -lh /backup | tail -5"

# Check database connections
mcp ssh exec db-server "psql -U postgres -c 'SELECT count(*) FROM pg_stat_activity;'"
```

### Security Audit

```bash
# Check failed login attempts
mcp ssh exec prod-web "grep 'Failed password' /var/log/auth.log | tail -20"

# Check sudo usage
mcp ssh exec prod-web "grep sudo /var/log/auth.log | tail -20"

# List open ports
mcp ssh exec prod-web "netstat -tuln"

# Check for running rootkits
mcp ssh exec prod-web "rkhunter --check --skip-keypress"

# Verify file integrity
mcp ssh exec prod-web "aide --check"
```

## Advanced Usage

### Creating Complex Aliases

```bash
# Multi-step deployment
mcp config add-alias deploy-app "cd /app && git pull && docker-compose build && docker-compose up -d && docker-compose logs -f"

# Health check
mcp config add-alias health-check "systemctl is-active nginx && systemctl is-active myapp && df -h | grep -E '/$' && free -h"

# Comprehensive diagnostics
mcp config add-alias full-diag "echo '=== Load ===' && uptime && echo '=== Memory ===' && free -h && echo '=== Disk ===' && df -h && echo '=== Processes ===' && ps aux | head -10"
```

### Parallel Operations

```bash
# Check multiple servers (using shell background jobs)
mcp ssh exec dev-app "uptime" &
mcp ssh exec staging-app "uptime" &
mcp ssh exec prod-app "uptime" &
wait

# Gather logs from multiple sources
mcp ssh logs prod-web /var/log/app/app.log -n 100 > web.log &
mcp ssh logs prod-api /var/log/api/api.log -n 100 > api.log &
mcp k8s logs worker-pod -n production --tail 100 > worker.log &
wait

# Aggregate and analyze
cat web.log api.log worker.log | grep ERROR | sort | uniq -c
```

### Scripting with MCP

```bash
#!/bin/bash
# check-all-services.sh

echo "Checking all production services..."

services=(
    "prod-web:nginx"
    "prod-app:myapp"
    "prod-db:postgresql"
)

for entry in "${services[@]}"; do
    IFS=':' read -r server service <<< "$entry"
    echo "Checking $service on $server..."
    mcp ssh exec "$server" "systemctl is-active $service" && \
        echo "? $service is running" || \
        echo "? $service is NOT running"
done
```

### Integration with CI/CD

```bash
# GitLab CI example
deploy_production:
  stage: deploy
  script:
    - mcp k8s use prod-k8s
    - mcp ssh exec prod-web "kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG -n production"
    - mcp ssh exec prod-web "kubectl rollout status deployment/myapp -n production"
  only:
    - tags
```

### Monitoring and Alerting

```bash
#!/bin/bash
# monitor-disk-usage.sh

THRESHOLD=80

usage=$(mcp ssh exec prod-web "df -h / | awk 'NR==2 {print \$5}' | sed 's/%//'")

if [ "$usage" -gt "$THRESHOLD" ]; then
    echo "ALERT: Disk usage is ${usage}% on prod-web"
    # Send notification
    curl -X POST https://hooks.slack.com/... -d "{\"text\":\"Disk usage alert: ${usage}%\"}"
else
    echo "Disk usage is normal: ${usage}%"
fi
```

---

For more examples and use cases, check the [MCP Server GitHub repository](https://github.com/yourorg/mcp-server).
