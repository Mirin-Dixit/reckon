#!/usr/bin/env bash
# ==============================================================================
# Script: deploy/aws/deploy.sh
# Purpose: Idempotent deployment of Reckon services using compose.yaml and
#          deploy/compose.aws.yaml. Verifies Ollama prerequisites, builds or updates
#          containers, initializes state permissions, and performs health check.
# Usage: bash deploy/aws/deploy.sh
# ==============================================================================

set -euo pipefail

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [DEPLOY] $*"
}

log_err() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [DEPLOY-ERROR] $*" >&2
}

# 1. Determine script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"
log "Working from repository root: ${REPO_ROOT}"

# 2. Check essential tool dependencies
for cmd in docker curl jq; do
    if ! command -v "${cmd}" &>/dev/null; then
        log_err "Missing required command: ${cmd}. Please run setup_host.sh first."
        exit 1
    fi
done

# Detect Docker Compose command
if docker compose version &>/dev/null; then
    COMPOSE_BIN=(docker compose)
elif command -v docker-compose &>/dev/null; then
    COMPOSE_BIN=(docker-compose)
else
    log_err "Neither 'docker compose' nor 'docker-compose' found. Please install the Docker Compose plugin."
    exit 1
fi

PROJECT_NAME="reckon"
COMPOSE_BASE="compose.yaml"
COMPOSE_OVERRIDE="deploy/compose.aws.yaml"
COMPOSE_CMD=("${COMPOSE_BIN[@]}" -p "${PROJECT_NAME}" -f "${COMPOSE_BASE}" -f "${COMPOSE_OVERRIDE}")

log "Using Compose command: ${COMPOSE_CMD[*]}"

# 3. Check Ollama host service prerequisite
log "Verifying host Ollama connectivity..."
if ! curl -fsS "http://127.0.0.1:11434/api/version" &>/dev/null; then
    log_err "Host Ollama is not responding on http://127.0.0.1:11434. Run install_ollama.sh first."
    exit 1
fi

MODELS_JSON="$(curl -fsS "http://127.0.0.1:11434/api/tags")"
if ! echo "${MODELS_JSON}" | jq -e '.models[] | select(.name | test("qwen3:4b-q4_K_M"))' &>/dev/null; then
    log_err "Required model 'qwen3:4b-q4_K_M' not found in Ollama tags."
    exit 1
fi
if ! echo "${MODELS_JSON}" | jq -e '.models[] | select(.name | test("all-minilm:22m"))' &>/dev/null; then
    log_err "Required model 'all-minilm:22m' not found in Ollama tags."
    exit 1
fi
log "Ollama host service and models verified."

# 4. Check configuration files
if [[ ! -f "${COMPOSE_BASE}" ]]; then
    log_err "Base compose file '${COMPOSE_BASE}' not found."
    exit 1
fi
if [[ ! -f "${COMPOSE_OVERRIDE}" ]]; then
    log_err "AWS compose override '${COMPOSE_OVERRIDE}' not found."
    exit 1
fi

# 5. Initialize Docker named state volume and directory permissions
VOLUME_NAME="${PROJECT_NAME}_state"
log "Ensuring Docker named volume '${VOLUME_NAME}' exists..."
docker volume create "${VOLUME_NAME}" > /dev/null

# Fix volume directory ownership for non-root container backend (UID 10001, GID 10001)
log "Verifying state volume ownership for non-root container user (UID 10001)..."
docker run --rm -v "${VOLUME_NAME}:/state" alpine:3.20 chown -R 10001:10001 /state

# 6. Build container images
log "Building or updating Reckon container images..."
"${COMPOSE_CMD[@]}" build

# 7. Start application services
log "Launching Reckon services with AWS override..."
"${COMPOSE_CMD[@]}" up -d --remove-orphans

# 8. Wait for container health checks (per-service timer reset)
log "Waiting for containers to report healthy status..."
SERVICES=("backend" "frontend" "gateway")
PER_SERVICE_WAIT=120

for svc in "${SERVICES[@]}"; do
    log "Checking health of service '${svc}' (timeout: ${PER_SERVICE_WAIT}s)..."
    ELAPSED=0
    while true; do
        STATUS="$("${COMPOSE_CMD[@]}" ps "${svc}" --format '{{.Health}}' 2>/dev/null || echo "")"
        if [[ "${STATUS}" == *"healthy"* ]]; then
            log "Service '${svc}' is healthy (took ${ELAPSED}s)."
            break
        fi

        STATE="$("${COMPOSE_CMD[@]}" ps "${svc}" --format '{{.State}}' 2>/dev/null || echo "")"
        if [[ "${STATE}" == "exited" || "${STATE}" == "dead" ]]; then
            log_err "Service '${svc}' exited prematurely. Recent logs:"
            "${COMPOSE_CMD[@]}" logs "${svc}" --tail 50 || true
            exit 1
        fi

        if [[ ${ELAPSED} -ge ${PER_SERVICE_WAIT} ]]; then
            log_err "Timeout waiting for service '${svc}' to become healthy (${PER_SERVICE_WAIT}s)."
            "${COMPOSE_CMD[@]}" ps
            "${COMPOSE_CMD[@]}" logs "${svc}" --tail 50 || true
            exit 1
        fi

        sleep 3
        ELAPSED=$((ELAPSED + 3))
    done
done

# 9. Perform initial smoke check against loopback gateway
log "Performing smoke check against loopback gateway on http://127.0.0.1:3000/api/v1/health..."
HEALTH_RESP="$(curl -fsS --max-time 10 "http://127.0.0.1:3000/api/v1/health" || echo "")"
if [[ -z "${HEALTH_RESP}" ]]; then
    log_err "Health check endpoint returned empty response."
    exit 1
fi

log "Health check returned: ${HEALTH_RESP}"
log "=========================================================================="
log "RECKON DEPLOYMENT SUCCESSFUL!"
log "Application is running securely on loopback (127.0.0.1:3000)."
log "To access from your local machine, open an SSH tunnel:"
log "  ssh -i ~/.ssh/reckon-ec2.pem -N -L 3000:127.0.0.1:3000 ubuntu@<EC2_IP>"
log "Then browse to: http://localhost:3000"
log "=========================================================================="
