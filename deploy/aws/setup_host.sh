#!/usr/bin/env bash
# ==============================================================================
# Script: deploy/aws/setup_host.sh
# Purpose: Idempotent host preparation for Reckon on Ubuntu 22.04 / 24.04 LTS (x86_64).
#          Installs Docker Engine, Docker Compose, UFW firewall, and deployment dirs.
# Usage: sudo bash deploy/aws/setup_host.sh
# ==============================================================================

set -euo pipefail

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [SETUP] $*"
}

log_err() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [SETUP-ERROR] $*" >&2
}

# 1. Root verification
if [[ "${EUID}" -ne 0 ]]; then
    log_err "This script must be run as root. Please execute with sudo."
    exit 1
fi

TARGET_USER="${SUDO_USER:-$(id -un)}"
log "Starting host setup for target user: ${TARGET_USER}"

# 2. Operating System check
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    if [[ "${ID}" != "ubuntu" && "${ID_LIKE:-}" != *"ubuntu"* && "${ID_LIKE:-}" != *"debian"* ]]; then
        log_err "Unsupported OS: ${ID}. This script targets Ubuntu/Debian LTS."
        exit 1
    fi
    log "Operating system confirmed: ${PRETTY_NAME:-Ubuntu}"
else
    log_err "Cannot determine OS release (/etc/os-release missing)."
    exit 1
fi

# 3. Base dependency installation
log "Updating apt package index and installing foundational utilities..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    ufw \
    jq \
    sqlite3 \
    tar \
    gzip \
    iproute2

# 4. Configure UFW Firewall (Zero Public Ingress for Application)
log "Configuring host firewall (UFW)..."
ufw default deny incoming
ufw default allow outgoing

# Allow inbound SSH only
ufw allow 22/tcp comment 'SSH Remote Administration'

# Ensure Docker bridge networks can route to host Ollama (11434)
# Docker default bridge uses 172.17.0.0/16; custom Compose bridge networks use 172.16.0.0/12 range
ufw allow in on lo to any port 11434 proto tcp comment 'Ollama Loopback Interface'
ufw allow from 127.0.0.1 to any port 11434 proto tcp comment 'Ollama Localhost'
ufw allow from 172.16.0.0/12 to any port 11434 proto tcp comment 'Ollama Docker Bridge Subnet'

# Deny any external ingress to Ollama, Gateway, or Backend ports
ufw deny 11434/tcp comment 'Block External Ollama'
ufw deny 3000/tcp comment 'Block External Application Gateway'
ufw deny 8000/tcp comment 'Block External FastAPI Backend'
ufw deny 8080/tcp comment 'Block External Nginx Upstream'

# Log note for live EC2 validation
log "Configured UFW rules for loopback and Docker bridge subnets (172.16.0.0/12)."
log "Note for live EC2 testing: Verify bridge network subnet matches 172.16.0.0/12 via 'ip addr show'."

# Enable UFW non-interactively
ufw --force enable
log "Firewall configured successfully. Active UFW status:"
ufw status verbose

# 5. Install Docker Engine and Docker Compose Plugin
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    log "Docker and Docker Compose are already installed: $(docker --version), $(docker compose version)"
else
    log "Installing Docker Engine and Compose plugin from official repository..."
    install -m 0755 -d /etc/apt/keyrings
    if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg
    fi

    ARCH="$(dpkg --print-architecture)"
    CODENAME="${VERSION_CODENAME:-$(lsb_release -cs)}"
    echo "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
        | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Ensure docker service is enabled and started
systemctl enable --now docker
log "Docker service status: $(systemctl is-active docker)"

# Add target user to docker group if not already a member
if ! id -nG "${TARGET_USER}" | grep -qw "docker"; then
    log "Adding user '${TARGET_USER}' to 'docker' group..."
    usermod -aG docker "${TARGET_USER}"
    log "User '${TARGET_USER}' added. Note: User must log out and back in, or run 'newgrp docker'."
fi

# 6. Create deployment and backup directory trees
log "Creating Reckon directory structure..."
install -d -m 0755 -o "${TARGET_USER}" -g "${TARGET_USER}" /opt/reckon
install -d -m 0750 -o "${TARGET_USER}" -g "${TARGET_USER}" /opt/reckon/backups

# 7. Configure vm swap and memory headroom parameters
log "Checking kernel swap and vm configuration..."
if [[ $(cat /proc/sys/vm/swappiness) -gt 20 ]]; then
    log "Tuning vm.swappiness to 10 for memory stability..."
    sysctl -w vm.swappiness=10
    echo "vm.swappiness=10" | tee -a /etc/sysctl.d/99-reckon.conf > /dev/null
fi

log "Host setup completed successfully. Proceed to: bash deploy/aws/install_ollama.sh"
