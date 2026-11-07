#!/usr/bin/env bash
# ==============================================================================
# Script: deploy/aws/install_ollama.sh
# Purpose: Idempotent installation of Ollama on Linux host, configured with systemd
#          override to bind 0.0.0.0:11434 (for Docker bridge access), and pulling
#          required models: 'qwen3:4b-q4_K_M' and 'all-minilm:22m'.
# Usage: sudo bash deploy/aws/install_ollama.sh
# ==============================================================================

set -euo pipefail

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [OLLAMA] $*"
}

log_err() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [OLLAMA-ERROR] $*" >&2
}

# 1. Root verification
if [[ "${EUID}" -ne 0 ]]; then
    log_err "This script must be run as root. Please execute with sudo."
    exit 1
fi

GEN_MODEL="qwen3:4b-q4_K_M"
EMBED_MODEL="all-minilm:22m"

# 2. Install Ollama if not present
if command -v ollama &>/dev/null; then
    log "Ollama binary already installed: $(ollama --version)"
else
    log "Downloading and installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# 3. Configure systemd override for bridge network listening
# Ollama by default binds only to 127.0.0.1.
# On Linux Docker with bridge networking, packets from containers arrive at the
# host bridge gateway IP (e.g. 172.18.0.1). Therefore, Ollama must listen on 0.0.0.0,
# while host UFW and AWS Security Groups block all external inbound traffic.
OVERRIDE_DIR="/etc/systemd/system/ollama.service.d"
OVERRIDE_FILE="${OVERRIDE_DIR}/override.conf"

log "Configuring systemd service override in ${OVERRIDE_FILE}..."
install -d -m 0755 "${OVERRIDE_DIR}"

cat <<'EOF' > "${OVERRIDE_FILE}"
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
Environment="OLLAMA_KEEP_ALIVE=24h"
Environment="OLLAMA_NUM_PARALLEL=1"
EOF

log "Reloading systemd daemon and restarting Ollama service..."
systemctl daemon-reload
systemctl restart ollama
systemctl enable ollama

# 4. Wait for Ollama service to become healthy
log "Waiting for Ollama API to respond on http://127.0.0.1:11434/api/version..."
RETRY_COUNT=0
MAX_RETRIES=30
until curl -fsS "http://127.0.0.1:11434/api/version" &>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [[ ${RETRY_COUNT} -ge ${MAX_RETRIES} ]]; then
        log_err "Ollama service failed to become ready within 30 seconds."
        systemctl status ollama --no-pager || true
        exit 1
    fi
    sleep 1
done

OLLAMA_VER=$(curl -s "http://127.0.0.1:11434/api/version" | jq -r '.version // "unknown"')
log "Ollama service active and healthy (version: ${OLLAMA_VER})."

# 5. Pull generation model (qwen3:4b-q4_K_M)
log "Verifying generation model: ${GEN_MODEL}..."
if ollama list | grep -q "${GEN_MODEL}"; then
    log "Generation model '${GEN_MODEL}' is already pulled."
else
    log "Pulling generation model '${GEN_MODEL}' (this may take several minutes)..."
    ollama pull "${GEN_MODEL}"
fi

# 6. Pull embedding model (all-minilm:22m)
log "Verifying embedding model: ${EMBED_MODEL}..."
if ollama list | grep -q "${EMBED_MODEL}"; then
    log "Embedding model '${EMBED_MODEL}' is already pulled."
else
    log "Pulling embedding model '${EMBED_MODEL}'..."
    ollama pull "${EMBED_MODEL}"
fi

# 7. Final inventory check
log "Verifying available models via Ollama API:"
AVAILABLE_MODELS=$(curl -s "http://127.0.0.1:11434/api/tags" | jq -r '.models[].name')
echo "${AVAILABLE_MODELS}"

if echo "${AVAILABLE_MODELS}" | grep -q "${GEN_MODEL}" && echo "${AVAILABLE_MODELS}" | grep -q "${EMBED_MODEL}"; then
    log "SUCCESS: Both required models are installed and verified."
else
    log_err "FAILURE: One or more models missing from Ollama tags."
    exit 1
fi
