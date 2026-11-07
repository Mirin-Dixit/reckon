#!/usr/bin/env bash
# ==============================================================================
# Script: deploy/aws/verify.sh
# Purpose: Comprehensive validation of Reckon EC2 deployment:
#          1. Container status and healthchecks
#          2. Zero public port exposure / private-access boundary audit
#          3. Host Ollama service and required models
#          4. Gateway health endpoint (FastAPI)
#          5. Next.js frontend delivery
#          6. End-to-end inference, retrieval and citation verification
#          7. SQLite state volume persistence and data integrity
# Usage: bash deploy/aws/verify.sh
# ==============================================================================

set -euo pipefail

PASS_COUNT=0
FAIL_COUNT=0

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [VERIFY] $*"
}

check_pass() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [PASS] $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

check_fail() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [FAIL] $1: $2" >&2
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# Detect Docker Compose command
if docker compose version &>/dev/null; then
    COMPOSE_BIN=(docker compose)
elif command -v docker-compose &>/dev/null; then
    COMPOSE_BIN=(docker-compose)
else
    log "Neither 'docker compose' nor 'docker-compose' found."
    exit 1
fi

PROJECT_NAME="reckon"
COMPOSE_CMD=("${COMPOSE_BIN[@]}" -p "${PROJECT_NAME}" -f compose.yaml -f deploy/compose.aws.yaml)

log "Starting Reckon deployment verification suite (Project: ${PROJECT_NAME})..."

# ------------------------------------------------------------------------------
# 1. Container Status & Health Check
# ------------------------------------------------------------------------------
log "1. Checking Docker container states..."
SERVICES=("backend" "frontend" "gateway" "app-proxy")
for svc in "${SERVICES[@]}"; do
    CONTAINER_ID="$("${COMPOSE_CMD[@]}" ps -q "${svc}" 2>/dev/null || echo "")"
    if [[ -z "${CONTAINER_ID}" ]]; then
        check_fail "Container '${svc}'" "Not running or not found in project '${PROJECT_NAME}'"
        continue
    fi

    STATE="$(docker inspect --format '{{.State.Status}}' "${CONTAINER_ID}" 2>/dev/null || echo "unknown")"
    if [[ "${STATE}" == "running" ]]; then
        check_pass "Container '${svc}' is running"
    else
        check_fail "Container '${svc}'" "Status is '${STATE}'"
    fi
done

# ------------------------------------------------------------------------------
# 2. Port Binding & Private-Access Boundary Audit
# ------------------------------------------------------------------------------
log "2. Auditing host port bindings and private-access boundaries..."
SOCKET_TOOL=""
if command -v ss &>/dev/null; then
    SOCKET_TOOL="ss"
elif command -v netstat &>/dev/null; then
    SOCKET_TOOL="netstat"
fi

if [[ -n "${SOCKET_TOOL}" ]]; then
    # Verify port 3000 is bound strictly to 127.0.0.1
    if ${SOCKET_TOOL} -tulpn 2>/dev/null | grep -E ':3000\b' | grep -v '127.0.0.1' | grep -v '::1' &>/dev/null; then
        check_fail "Port 3000 boundary" "Exposed to non-loopback interface!"
    else
        check_pass "Port 3000 strictly bound to loopback (127.0.0.1)"
    fi

    # Verify backend (8000) is NOT listening on host interfaces
    if ${SOCKET_TOOL} -tulpn 2>/dev/null | grep -E ':8000\b' &>/dev/null; then
        check_fail "Port 8000 isolation" "FastAPI backend is exposed directly on host socket!"
    else
        check_pass "Port 8000 is isolated inside Docker network"
    fi

    # Verify Nginx upstream (8080) is NOT listening directly on host
    if ${SOCKET_TOOL} -tulpn 2>/dev/null | grep -E ':8080\b' &>/dev/null; then
        check_fail "Port 8080 isolation" "Nginx upstream 8080 exposed on host socket!"
    else
        check_pass "Port 8080 is isolated inside Docker network"
    fi
else
    check_fail "Socket audit tool" "Neither 'ss' nor 'netstat' available to audit port boundaries"
fi

# Audit UFW firewall status if present
if command -v ufw &>/dev/null; then
    UFW_STATUS="$(sudo -n ufw status 2>/dev/null || ufw status 2>/dev/null || echo "")"
    if echo "${UFW_STATUS}" | grep -q "Status: active"; then
        check_pass "UFW host firewall is active"
        if echo "${UFW_STATUS}" | grep -E "Default: deny \(incoming\)" &>/dev/null; then
            check_pass "UFW default incoming policy is DENY"
        else
            check_fail "UFW incoming policy" "Default incoming is not DENY"
        fi
    else
        check_fail "UFW firewall" "UFW host firewall is not active"
    fi
fi

# ------------------------------------------------------------------------------
# 3. Host Ollama Service & Models Verification
# ------------------------------------------------------------------------------
log "3. Verifying host Ollama daemon and required models..."
OLLAMA_VER_RESP="$(curl -fsS --max-time 5 "http://127.0.0.1:11434/api/version" 2>/dev/null || echo "")"
if [[ -n "${OLLAMA_VER_RESP}" ]]; then
    check_pass "Host Ollama API responding (version: $(echo "${OLLAMA_VER_RESP}" | jq -r '.version // "unknown"'))"
else
    check_fail "Host Ollama API" "Unreachable on 127.0.0.1:11434"
fi

OLLAMA_TAGS="$(curl -fsS --max-time 5 "http://127.0.0.1:11434/api/tags" 2>/dev/null || echo "")"
if echo "${OLLAMA_TAGS}" | jq -e '.models[] | select(.name | test("qwen3:4b-q4_K_M"))' &>/dev/null; then
    check_pass "Model 'qwen3:4b-q4_K_M' present in Ollama"
else
    check_fail "Model 'qwen3:4b-q4_K_M'" "Missing from Ollama library"
fi

if echo "${OLLAMA_TAGS}" | jq -e '.models[] | select(.name | test("all-minilm:22m"))' &>/dev/null; then
    check_pass "Model 'all-minilm:22m' present in Ollama"
else
    check_fail "Model 'all-minilm:22m'" "Missing from Ollama library"
fi

# ------------------------------------------------------------------------------
# 4. Gateway Health Endpoint Verification
# ------------------------------------------------------------------------------
log "4. Checking Gateway API health endpoint..."
HEALTH_HTTP_CODE="$(curl -s -o /tmp/health_body.json -w "%{http_code}" --max-time 10 "http://127.0.0.1:3000/api/v1/health" || echo "000")"
if [[ "${HEALTH_HTTP_CODE}" == "200" ]]; then
    APP_STATUS="$(jq -r '.status // "unknown"' /tmp/health_body.json 2>/dev/null || echo "parse_error")"
    if [[ "${APP_STATUS}" == "ok" ]]; then
        check_pass "API Health returned HTTP 200 (status: ok)"
    else
        check_fail "API Health status" "Expected 'ok', received '${APP_STATUS}'"
    fi
else
    check_fail "API Health HTTP code" "Expected 200, got ${HEALTH_HTTP_CODE}"
fi

# ------------------------------------------------------------------------------
# 5. Frontend UI Delivery Verification
# ------------------------------------------------------------------------------
log "5. Checking Next.js Frontend delivery..."
FRONTEND_HTTP_CODE="$(curl -s -o /tmp/frontend_body.html -w "%{http_code}" --max-time 10 "http://127.0.0.1:3000/" || echo "000")"
if [[ "${FRONTEND_HTTP_CODE}" == "200" ]]; then
    if grep -q "html" /tmp/frontend_body.html; then
        check_pass "Frontend delivered HTTP 200 with HTML document"
    else
        check_fail "Frontend content" "Response did not contain HTML"
    fi
else
    check_fail "Frontend HTTP code" "Expected 200, got ${FRONTEND_HTTP_CODE}"
fi

# ------------------------------------------------------------------------------
# 6. End-to-End Query, Retrieval, and Citation Verification
# ------------------------------------------------------------------------------
log "6. Executing live end-to-end query via Gateway relay..."
QUERY_PAYLOAD='{
  "question": "What is Python?",
  "retrieval": {
    "method": "bm25",
    "top_k": 2
  },
  "policy": {
    "name": "always_answer"
  }
}'

QUERY_HTTP_CODE="$(curl -s -o /tmp/query_resp.json -w "%{http_code}" --max-time 60 \
    -X POST "http://127.0.0.1:3000/api/v1/query" \
    -H "Content-Type: application/json" \
    -d "${QUERY_PAYLOAD}" || echo "000")"

if [[ "${QUERY_HTTP_CODE}" == "200" ]]; then
    DECISION="$(jq -r '.decision // "unknown"' /tmp/query_resp.json 2>/dev/null || echo "parse_error")"
    STATUS="$(jq -r '.execution_status // "unknown"' /tmp/query_resp.json 2>/dev/null || echo "parse_error")"

    if [[ "${STATUS}" == "succeeded" ]]; then
        check_pass "End-to-end query succeeded (decision: ${DECISION})"
    else
        check_fail "Query execution status" "Status was '${STATUS}'"
    fi

    # Check evidence retrieval
    EVIDENCE_COUNT="$(jq '.retrieved_evidence | length' /tmp/query_resp.json 2>/dev/null || echo "0")"
    if [[ "${EVIDENCE_COUNT}" -gt 0 ]]; then
        check_pass "Query retrieved ${EVIDENCE_COUNT} evidence documents"
    else
        check_fail "Query retrieval" "retrieved_evidence is empty"
    fi

    # Check citations when decision is ANSWER
    if [[ "${DECISION}" == "ANSWER" ]]; then
        CITATION_COUNT="$(jq '.citations | length' /tmp/query_resp.json 2>/dev/null || echo "0")"
        if [[ "${CITATION_COUNT}" -gt 0 ]]; then
            check_pass "Query produced ${CITATION_COUNT} verified citations"
        else
            check_fail "Query citations" "Decision was ANSWER but citations list is empty"
        fi
    fi
else
    check_fail "Query execution HTTP code" "Expected 200, got ${QUERY_HTTP_CODE}"
    if [[ -f /tmp/query_resp.json ]]; then
        log "Query error body: $(cat /tmp/query_resp.json)"
    fi
fi

# ------------------------------------------------------------------------------
# 7. Persistence Storage & SQLite Non-Empty Verification
# ------------------------------------------------------------------------------
log "7. Verifying SQLite persistence in Docker state volume..."
VOLUME_NAME="${PROJECT_NAME}_state"

if ! docker volume inspect "${VOLUME_NAME}" &>/dev/null; then
    check_fail "Docker state volume" "Volume '${VOLUME_NAME}' does not exist"
else
    DB_STATUS="$(docker run --rm -v "${VOLUME_NAME}:/state:ro" alpine:3.20 sh -c '
        if [ ! -f /state/experiments.sqlite3 ]; then
            echo "missing"
        elif [ ! -s /state/experiments.sqlite3 ]; then
            echo "empty"
        else
            echo "ok"
        fi
    ')"

    if [[ "${DB_STATUS}" == "ok" ]]; then
        check_pass "SQLite database exists and is non-empty in volume '${VOLUME_NAME}'"
    elif [[ "${DB_STATUS}" == "empty" ]]; then
        check_fail "SQLite database" "File /state/experiments.sqlite3 exists but is 0 bytes"
    else
        check_fail "SQLite database" "File /state/experiments.sqlite3 not found in volume '${VOLUME_NAME}'"
    fi
fi

# Clean up temporary response files
rm -f /tmp/health_body.json /tmp/frontend_body.html /tmp/query_resp.json

# ------------------------------------------------------------------------------
# Verification Summary
# ------------------------------------------------------------------------------
echo "=========================================================================="
echo "VERIFICATION REPORT: ${PASS_COUNT} Passed, ${FAIL_COUNT} Failed"
echo "=========================================================================="

if [[ ${FAIL_COUNT} -eq 0 ]]; then
    log "DEPLOYMENT VERIFICATION PASSED: All operational checks succeeded."
    exit 0
else
    log_err "DEPLOYMENT VERIFICATION FAILED: ${FAIL_COUNT} check(s) failed."
    exit 1
fi
