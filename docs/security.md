# Security Guide for MCP Server

## Overview

Security is a paramount concern for MCP Server as it manages access to critical infrastructure. This document outlines security best practices, current implementation details, and future security enhancements.

## Current Security Model (Phase 1 - MVP)

### Local-First Architecture

MCP Server currently operates as a local CLI tool that runs on each developer's machine. This design provides several security benefits:

1. **No External Exposure**: Infrastructure access remains within your trusted network
2. **User-Level Credentials**: Each developer uses their own credentials
3. **No Centralized Credential Store**: Reduces attack surface
4. **Local Audit Trail**: All operations are performed by identifiable users

### Credential Storage

#### Configuration File Security

- Configuration stored in `~/.mcp/config.yaml`
- Directory permissions: `0700` (owner read/write/execute only)
- File permissions: `0600` (owner read/write only)
- Automatically set during initialization

#### Supported Authentication Methods

1. **SSH Key-Based Authentication** (Recommended)
   ```bash
   mcp config add-ssh prod-server host user --key ~/.ssh/id_rsa
   ```
   - Most secure option
   - No password stored in configuration
   - Supports SSH agent for key management
   - Keys never transmitted, only used locally

2. **SSH Password Authentication** (Not Recommended)
   ```bash
   mcp config add-ssh server host user --password 'mypass'
   ```
   - ?? WARNING: Stores password in plain text
   - Only use in development/testing environments
   - Never commit configuration files with passwords

3. **Kubernetes Authentication**
   - Uses existing kubeconfig files
   - Supports multiple authentication methods (certificates, tokens, exec)
   - Leverages kubectl's security model

4. **Docker Authentication**
   - SSH-based connection to remote Docker daemons
   - Local Docker socket for local operations

## Security Best Practices

### 1. Credential Management

#### DO:
- ? Use SSH key-based authentication
- ? Use dedicated service accounts with minimal permissions
- ? Store SSH keys with proper permissions (600)
- ? Use SSH agent for key management
- ? Rotate credentials regularly
- ? Use different keys for different environments

#### DON'T:
- ? Store passwords in configuration files
- ? Commit configuration files to version control
- ? Share SSH keys between team members
- ? Use root or admin accounts unnecessarily
- ? Reuse credentials across environments

### 2. Access Control

#### Principle of Least Privilege

Configure credentials with the minimum required permissions:

**SSH Access:**
```bash
# Good: Limited user account
mcp config add-ssh app-server host app-user --key ~/.ssh/app_key

# Bad: Root access
mcp config add-ssh app-server host root --key ~/.ssh/root_key
```

**Kubernetes RBAC:**
```yaml
# Example: Limited service account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-reader
  namespace: production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list"]
```

**SSH User Restrictions:**
```bash
# /etc/ssh/sshd_config on remote server
# Restrict user to specific commands
Match User mcp-user
    ForceCommand /usr/local/bin/mcp-allowed-commands
    PermitOpen none
    X11Forwarding no
```

### 3. Network Security

#### SSH Configuration

**Client-side (`~/.ssh/config`):**
```
Host prod-*
    User deploy-user
    IdentityFile ~/.ssh/prod_key
    StrictHostKeyChecking yes
    UserKnownHostsFile ~/.ssh/known_hosts
    ServerAliveInterval 60
    ServerAliveCountMax 3

Host dev-*
    User dev-user
    IdentityFile ~/.ssh/dev_key
```

**Server-side Best Practices:**
- Disable password authentication
- Use key-based authentication only
- Enable fail2ban or similar intrusion prevention
- Restrict SSH access by IP if possible
- Use non-standard SSH port (security through obscurity)
- Enable SSH session logging

### 4. Configuration File Security

#### Git Ignore Configuration

The `.gitignore` file includes:
```gitignore
# MCP Configuration (contains sensitive credentials)
.mcp/
mcp-config.json
mcp-config.yaml
*.key
*.pem
```

#### Never Commit Credentials

```bash
# Before committing, always check:
git status
git diff --staged

# If you accidentally staged config files:
git reset HEAD ~/.mcp/config.yaml
```

#### Environment Separation

Keep separate configurations for different environments:

```bash
# Development
~/.mcp/config-dev.yaml

# Staging
~/.mcp/config-staging.yaml

# Production
~/.mcp/config-prod.yaml

# Use with:
mcp --config ~/.mcp/config-prod.yaml ssh exec ...
```

### 5. Audit Logging

#### Current Logging

MCP Server logs all operations to console output. For audit purposes:

```bash
# Redirect to log file
mcp ssh exec server "command" | tee -a ~/.mcp/audit.log

# Or use shell logging
script -a ~/.mcp/session-$(date +%Y%m%d-%H%M%S).log
mcp ssh exec server "command"
exit
```

#### Log Rotation

```bash
# Create logrotate configuration
cat > /etc/logrotate.d/mcp <<EOF
/home/*/.mcp/*.log {
    weekly
    rotate 12
    compress
    delaycompress
    notifempty
    missingok
}
EOF
```

### 6. Kubernetes Security

#### Service Account Best Practices

Create dedicated service accounts for MCP:

```bash
# Create namespace
kubectl create namespace mcp-access

# Create service account
kubectl create serviceaccount mcp-user -n mcp-access

# Create role with limited permissions
kubectl create role mcp-viewer \
  --verb=get,list,watch \
  --resource=pods,services,deployments \
  -n mcp-access

# Bind role to service account
kubectl create rolebinding mcp-viewer-binding \
  --role=mcp-viewer \
  --serviceaccount=mcp-access:mcp-user \
  -n mcp-access

# Get service account token
kubectl create token mcp-user -n mcp-access
```

#### Network Policies

Restrict Kubernetes API access:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-api-access
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8  # Internal network only
```

## Security Checklist

### Before Deployment

- [ ] SSH keys generated with strong encryption (Ed25519 or RSA 4096-bit)
- [ ] Configuration file permissions verified (600)
- [ ] No passwords in configuration files
- [ ] All credentials use least-privilege access
- [ ] SSH hosts verified in known_hosts
- [ ] Kubernetes RBAC policies reviewed
- [ ] Configuration files excluded from version control

### Regular Maintenance

- [ ] Rotate SSH keys every 90 days
- [ ] Review and update Kubernetes tokens
- [ ] Audit access logs monthly
- [ ] Remove unused server configurations
- [ ] Update MCP Server and dependencies
- [ ] Review and revoke unnecessary permissions
- [ ] Test disaster recovery procedures

### Incident Response

If credentials are compromised:

1. **Immediate Actions:**
   ```bash
   # Revoke compromised SSH key
   # On remote server:
   sed -i '/compromised-key-identifier/d' ~/.ssh/authorized_keys
   
   # Revoke Kubernetes token
   kubectl delete serviceaccount mcp-user -n mcp-access
   
   # Generate new keys
   ssh-keygen -t ed25519 -f ~/.ssh/new_mcp_key -C "mcp-new-key"
   ```

2. **Investigation:**
   - Review audit logs
   - Check SSH logs on target servers: `/var/log/auth.log`
   - Review Kubernetes audit logs
   - Identify scope of access

3. **Recovery:**
   - Generate new credentials
   - Update MCP configuration
   - Notify security team
   - Document incident

## Future Security Enhancements

### Phase 2: Enhanced Credential Security

1. **OS Keychain Integration**
   - macOS: Keychain Access
   - Linux: GNOME Keyring / KWallet
   - Windows: Windows Credential Manager

2. **Encrypted Configuration**
   - Encrypt sensitive fields in configuration
   - Master password or key-based encryption

### Phase 3: Secret Management Integration

1. **HashiCorp Vault**
   ```bash
   # Future command structure
   mcp config add-vault-backend \
     --url https://vault.example.com \
     --auth-method token \
     --path secret/mcp
   
   # Credentials fetched at runtime
   mcp ssh exec prod-server "command"
   # Automatically retrieves SSH key from Vault
   ```

2. **AWS Secrets Manager**
   ```bash
   mcp config add-secrets-backend aws \
     --region us-west-2 \
     --secret-prefix mcp/
   ```

3. **Azure Key Vault**
   ```bash
   mcp config add-secrets-backend azure \
     --vault-name my-keyvault \
     --secret-prefix mcp-
   ```

### Phase 4: Central Server Security

1. **Authentication:**
   - SSO integration (SAML, OAuth 2.0)
   - Multi-factor authentication (TOTP, WebAuthn)
   - API key management

2. **Authorization:**
   - Role-based access control (RBAC)
   - Attribute-based access control (ABAC)
   - Just-in-time (JIT) access

3. **Audit & Compliance:**
   - Comprehensive audit logging
   - Compliance reporting (SOC 2, ISO 27001)
   - Alert on suspicious activity

4. **Network Security:**
   - TLS 1.3 for all communications
   - Certificate pinning
   - Zero-trust networking

## Security Resources

### Tools for Security Testing

```bash
# Check file permissions
ls -la ~/.mcp/

# Scan for secrets in code
trufflehog git file://. --json

# Check SSH configuration
ssh-audit localhost

# Kubernetes security scanning
kubesec scan deployment.yaml
```

### Security Training

- OWASP Top 10
- CIS Benchmarks
- NIST Cybersecurity Framework
- Cloud security best practices (AWS, Azure, GCP)

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email security@yourcompany.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

## Compliance

MCP Server is designed to support:

- **SOC 2** - Audit logging, access controls
- **GDPR** - No personal data collection
- **HIPAA** - Encryption at rest and in transit (future)
- **PCI DSS** - Secure credential management (future)

---

**Remember**: Security is everyone's responsibility. Always follow your organization's security policies and procedures when using MCP Server.
