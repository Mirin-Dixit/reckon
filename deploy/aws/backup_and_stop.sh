#!/usr/bin/env bash
# ==============================================================================
# Script: deploy/aws/backup_and_stop.sh
# Purpose: Performs a SQLite-consistent snapshot and state archive from Docker volume,
#          verifies non-empty tables and integrity, generates SHA-256 checksum,
#          stops Docker Compose containers gracefully, and optionally stops host Ollama
#          to prepare EC2 for cost-saving stop state.
# Usage: bash deploy/aws/backup_and_stop.sh [/optional/backup/directory]
# ==============================================================================

set -euo pipefail

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [BACKUP-STOP] $*"
}

log_err() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [BACKUP-STOP-ERROR] $*" >&2
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
    log_err "Neither 'docker compose' nor 'docker-compose' found."
    exit 1
fi

PROJECT_NAME="reckon"
COMPOSE_CMD=("${COMPOSE_BIN[@]}" -p "${PROJECT_NAME}" -f compose.yaml -f deploy/compose.aws.yaml)

BACKUP_DIR="${1:-/opt/reckon/backups}"
mkdir -p "${BACKUP_DIR}"

TIMESTAMP="$(date -u +'%Y%m%d_%H%M%SZ')"
ARCHIVE_NAME="reckon_state_backup_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"
VOLUME_NAME="${PROJECT_NAME}_state"

log "Initiating state volume backup for project '${PROJECT_NAME}' (volume: ${VOLUME_NAME})..."

# 1. Verify Docker named volume existence
if ! docker volume inspect "${VOLUME_NAME}" &>/dev/null; then
    log_err "CRITICAL: Docker volume '${VOLUME_NAME}' does not exist. Cannot perform backup."
    exit 1
fi

# 2. Select available image with Python/SQLite support for consistent snapshot
BACKUP_IMAGE=""
for img in "reckon-backend" "reckon-backend:latest" "reckon_backend" "python:3.13-slim-bookworm" "python:3.13-slim"; do
    if docker image inspect "${img}" &>/dev/null; then
        BACKUP_IMAGE="${img}"
        break
    fi
done

if [[ -z "${BACKUP_IMAGE}" ]]; then
    log "Custom Python image not found in cache; falling back to alpine:3.20 with runtime sqlite3..."
    BACKUP_IMAGE="alpine:3.20"
fi
log "Using container image '${BACKUP_IMAGE}' for transactional snapshot..."

TEMP_STAGING="$(mktemp -d /tmp/reckon_backup_staging_XXXXXX)"
trap 'rm -rf "${TEMP_STAGING}"' EXIT

mkdir -p "${TEMP_STAGING}/state_snapshot"

# 3. Perform SQLite-consistent online backup (ACID consistent, WAL-safe)
log "Executing SQLite online backup via container..."

if [[ "${BACKUP_IMAGE}" == *"python"* || "${BACKUP_IMAGE}" == *"backend"* ]]; then
    # Use Python sqlite3 backup API
    docker run --rm \
        -v "${VOLUME_NAME}:/state:ro" \
        -v "${TEMP_STAGING}:/staging" \
        "${BACKUP_IMAGE}" python -c '
import os, sys, sqlite3

src_path = "/state/experiments.sqlite3"
dst_path = "/staging/state_snapshot/experiments.sqlite3"

if not os.path.exists(src_path):
    sys.exit(f"ERROR: SQLite database file not found in volume: {src_path}")

file_size = os.path.getsize(src_path)
if file_size == 0:
    sys.exit(f"ERROR: SQLite database file is empty (0 bytes): {src_path}")

print(f"Connecting to source database ({file_size} bytes)...")
src = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True)
dst = sqlite3.connect(dst_path)

print("Executing atomic online backup...")
with dst:
    src.backup(dst)
dst.close()
src.close()

# Verify integrity of snapshot
check = sqlite3.connect(dst_path)
cur = check.cursor()
cur.execute("PRAGMA integrity_check;")
integrity = cur.fetchone()[0]
if integrity != "ok":
    sys.exit(f"ERROR: Backup integrity check failed: {integrity}")

cur.execute("SELECT count(*) FROM sqlite_master WHERE type=\"table\";")
table_count = cur.fetchone()[0]
if table_count < 1:
    sys.exit("ERROR: Backup contains 0 tables; incomplete database.")

check.close()
print(f"Consistent SQLite snapshot verified ({table_count} tables, integrity: ok).")
'
else
    # Fallback using Alpine + sqlite3 CLI
    docker run --rm \
        -v "${VOLUME_NAME}:/state:ro" \
        -v "${TEMP_STAGING}:/staging" \
        "${BACKUP_IMAGE}" sh -c '
            set -e
            apk add --no-cache sqlite >/dev/null 2>&1
            if [ ! -f /state/experiments.sqlite3 ]; then
                echo "ERROR: /state/experiments.sqlite3 missing" >&2
                exit 1
            fi
            if [ ! -s /state/experiments.sqlite3 ]; then
                echo "ERROR: /state/experiments.sqlite3 is 0 bytes" >&2
                exit 1
            fi
            sqlite3 /state/experiments.sqlite3 ".backup /staging/state_snapshot/experiments.sqlite3"
            INTEGRITY=$(sqlite3 /staging/state_snapshot/experiments.sqlite3 "PRAGMA integrity_check;")
            if [ "${INTEGRITY}" != "ok" ]; then
                echo "ERROR: Integrity check failed: ${INTEGRITY}" >&2
                exit 1
            fi
            TABLES=$(sqlite3 /staging/state_snapshot/experiments.sqlite3 "SELECT count(*) FROM sqlite_master WHERE type=\"table\";")
            if [ "${TABLES}" -lt 1 ]; then
                echo "ERROR: Zero tables in backup" >&2
                exit 1
            fi
            echo "Consistent SQLite snapshot verified (${TABLES} tables, integrity: ok)."
        '
fi

# 4. Copy pre-computed dense embeddings if present
docker run --rm \
    -v "${VOLUME_NAME}:/state:ro" \
    -v "${TEMP_STAGING}:/staging" \
    "${BACKUP_IMAGE}" sh -c '
        if [ -d /state/dense ]; then
            cp -a /state/dense /staging/state_snapshot/
            echo "Copied dense vector cache to backup staging."
        fi
    '

# 5. Compress and verify tarball
log "Compressing backup archive to ${ARCHIVE_PATH}..."
tar -czf "${ARCHIVE_PATH}" -C "${TEMP_STAGING}/state_snapshot" .

if [[ ! -s "${ARCHIVE_PATH}" ]]; then
    log_err "CRITICAL: Backup archive was created but is empty (0 bytes)."
    exit 1
fi

# Test tarball integrity
tar -tzf "${ARCHIVE_PATH}" > /dev/null
log "Tar archive integrity verified."

# Generate SHA-256 checksum
sha256sum "${ARCHIVE_PATH}" > "${ARCHIVE_PATH}.sha256"
CHECKSUM="$(cut -d ' ' -f 1 "${ARCHIVE_PATH}.sha256")"
log "Backup verified and saved: ${ARCHIVE_PATH} (SHA-256: ${CHECKSUM})"

# 6. Gracefully stop Docker Compose application containers
log "Stopping Reckon application containers for project '${PROJECT_NAME}'..."
"${COMPOSE_CMD[@]}" down --remove-orphans
log "Containers stopped."

# 7. Stop host Ollama service if systemctl is available and caller has permissions
if command -v systemctl &>/dev/null; then
    if [[ "${EUID}" -eq 0 ]] || sudo -n true 2>/dev/null; then
        log "Stopping host Ollama service to release memory and CPU resources..."
        sudo systemctl stop ollama || true
        log "Host Ollama service stopped."
    else
        log "Note: Run 'sudo systemctl stop ollama' to stop host Ollama before stopping EC2."
    fi
fi

log "=========================================================================="
log "SHUTDOWN AND BACKUP COMPLETED."
log "Backup archive: ${ARCHIVE_PATH}"
log "To download this backup to your local machine, run:"
log "  scp -i ~/.ssh/reckon-ec2.pem ubuntu@<EC2_IP>:${ARCHIVE_PATH} ./"
log "You can now safely stop the EC2 instance in AWS Console to avoid compute charges."
log "=========================================================================="
