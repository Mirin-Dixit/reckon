# Reckon — AWS EC2 Deployment Guide (ap-southeast-2 Sydney)

This document provides the complete, security-hardened operational runbook for deploying the **Reckon** selective-answering RAG platform on an Amazon Web Services (AWS) EC2 instance in the `ap-southeast-2` (Sydney) region.

---

## 1. Architecture & Network Topology

Reckon enforces a **zero-public-port architecture**. The application web UI, API routes, and Ollama inference endpoints are never exposed directly to the public internet. Access is strictly mediated via an encrypted **SSH Local Port Forwarding Tunnel**.

```
[ Local Workstation (User Browser) ]
               │
               │ SSH Local Port Forward (3000:127.0.0.1:3000)
               ▼ (Port 22 only via Security Group)
┌─── EC2 Host (Ubuntu 22.04/24.04 LTS — ap-southeast-2) ───────────────────────────┐
│                                                                                 │
│   UFW Firewall: Ingress Port 22 ALLOW; Ports 3000, 8000, 8080, 11434 DENY       │
│                                                                                 │
│   Host Loopback: 127.0.0.1:3000                                                 │
│        ▲                                                                        │
│        │ (Port map: 127.0.0.1:3000 -> 8080)                                     │
│   ┌────┴──────────────────────────┐                                             │
│   │ reckon-gateway (Nginx)        │                                             │
│   │ Network: ingress & local      │                                             │
│   └────┬──────────────────────────┘                                             │
│        │                                                                        │
│        ├──> http://backend:8080 (via app-proxy in shared network namespace)     │
│        │         ├──> /api/*  -> FastAPI backend (127.0.0.1:8000)               │
│        │         └──> /*      -> Next.js frontend (127.0.0.1:3000)             │
│        │                                                                        │
│        └──> Port 11434 Ollama Relay                                             │
│                  │                                                              │
│                  ▼ (extra_hosts: host.docker.internal:host-gateway)             │
│   ┌─────────────────────────────────────────────────────────────┐               │
│   │ Host Ollama Daemon (0.0.0.0:11434 — Bound to Bridge Gateway) │               │
│   │ Models: qwen3:4b-q4_K_M (LLM) & all-minilm:22m (Embeddings)  │               │
│   └─────────────────────────────────────────────────────────────┘               │
│                                                                                 │
│   Docker Named Volume: reckon_state                                             │
│   Mount: /state -> /state/experiments.sqlite3 & /state/dense/ vector cache      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Hardware Sizing & Memory Budget Matrix

The Reckon platform consists of four containerized services (`backend`, `frontend`, `gateway`, `app-proxy`) plus the host-native `ollama` model inference daemon running a 4B parameter quantized LLM and a 384-dimensional BERT embedding model.

### Working Memory Breakdown

| Component | Minimum Working RAM | Peak / Allocation Limit | Notes |
| :--- | :--- | :--- | :--- |
| **Ubuntu OS & Systemd Daemons** | 600 MB | 1,024 MB | Kernel, journald, ufw, sshd |
| **Docker Engine & Runtimes** | 200 MB | 300 MB | containerd daemon overhead |
| **FastAPI Backend (`backend`)** | 350 MB | 768 MB | Hard memory cap (`mem_limit: 768m`) |
| **Next.js Frontend (`frontend`)** | 280 MB | 768 MB | Hard memory cap (`mem_limit: 768m`) |
| **Nginx Gateway (`gateway`)** | 30 MB | 128 MB | Hard memory cap (`mem_limit: 128m`) |
| **Internal Proxy (`app-proxy`)** | 20 MB | 128 MB | Hard memory cap (`mem_limit: 128m`) |
| **Ollama Daemon Overhead** | 150 MB | 300 MB | Memory allocator & API process |
| **`all-minilm:22m` Embedding** | 120 MB | 200 MB | 384-dim BERT model in RAM |
| **`qwen3:4b-q4_K_M` Generation** | 2,450 MB | 3,200 MB | Model weights (~2.3 GB) + 8k context buffer |
| **Total Memory Required** | **~4.2 GB** | **~6.8 GB** | **Requires 8 GiB host RAM minimum** |

### Instance Recommendation Matrix

> [!WARNING]
> **UNVERIFIED ESTIMATES**: All pricing figures, hourly rates, and inference throughput numbers below are theoretical planning estimates based on published AWS list pricing and local prototype observations. They are **UNVERIFIED** until confirmed with actual live AWS account billing data and CPU benchmarking on a running EC2 instance. Actual rates may vary with currency conversion (AUD/USD), taxes (e.g. GST), CPU burst credit throttling, and account-specific credit terms.

| Instance Type | vCPU | RAM | Sydney On-Demand Rate [UNVERIFIED ESTIMATE] | Suitability / Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **`t3.large`** | 2 | 8.0 GiB | ~$0.1040 / hr (indicative AWS list) | **Minimum Viable**. Suitable for lightweight evaluation and demo runs. Slower inference throughput on 2 vCPUs (~5-8 tokens/sec, UNVERIFIED). Tight memory headroom. |
| **`t3.xlarge`** | 4 | 16.0 GiB | ~$0.2080 / hr (indicative AWS list) | **Recommended Practical Baseline**. 4 vCPUs provide estimated ~12-18 tokens/sec (UNVERIFIED). 16 GiB RAM guarantees zero OOM kill risk during concurrent retrieval and evaluation runs. |
| **`c6i.xlarge`** | 4 | 8.0 GiB | ~$0.2140 / hr (indicative AWS list) | Dedicated compute-optimized. Higher single-core CPU frequency; excellent for pure CPU LLM inference speed. |

---

## 3. AWS Free Tier & Credit Budget Analysis (Sydney: ap-southeast-2)

> [!WARNING]
> **UNVERIFIED ACCOUNT STATUS & PRICING ESTIMATES**:
> - The \$100 credit pool applicability, account expiration date, and Free Tier service coverage are **UNVERIFIED** until the AWS address verification support case is resolved and confirmed in the AWS Billing & Cost Management console.
> - The application compute requirements (`t3.large` or `t3.xlarge`) exceed the standard EC2 Free Tier (`t2.micro` / `t3.micro`, 1 GiB RAM). Compute hours will consume active promotional credits or incur standard charges.
> - Data transfer out allowances and storage discounts are subject to individual AWS account terms.

### Unit Cost Breakdown (`ap-southeast-2` — Sydney, AUD converted / USD base) [UNVERIFIED ESTIMATES]

- **EC2 Compute (`t3.xlarge` 4 vCPU, 16 GiB)**: **~$0.2080 / hour** (indicative on-demand rate)
- **EBS gp3 Storage (40 GiB provisioned)**: ~$0.096 / GB-month = **~$3.84 / month** (~$0.128 / day)
- **Public IPv4 Address**: ~$0.005 / hour = **~$0.12 / day** (AWS charge for in-use and idle public IPv4)
- **Data Transfer Out**: First 100 GB/month typically included, subject to account eligibility terms.

### Credit Burn Scenarios [UNVERIFIED PLANNING MODELS]

| Scenario | Active Run Hours | Total Cost [UNVERIFIED] | Credits Remaining ($100 base) [UNVERIFIED] |
| :--- | :--- | :--- | :--- |
| **Single Evaluation Run (2 hours on `t3.xlarge`)** | 2 hrs compute + 1 day EBS/IP | **~$0.67** | **~$99.33** |
| **Intensive Testing Week (25 active hours)** | 25 hrs compute + 7 days EBS/IP | **~$7.00** | **~$93.00** |
| **Full Month Development (40 active compute hours)**| 40 hrs compute + 30 days EBS/IP | **~$15.96** | **~$84.04** |

> [!TIP]
> **Cost Control Best Practice**:
> Always run `bash deploy/aws/backup_and_stop.sh` and stop the EC2 instance in the AWS Console when not running benchmarks. A stopped instance incurs **only EBS storage fees (~$0.13/day)**, preserving your \$100 credit pool for months of active testing.

---

## 4. Security Hardening & Zero-Public-Port Enforcement

Reckon implements multi-tier defense-in-depth:

1. **AWS EC2 Security Group**:
   - Inbound Rule: **Port 22 (SSH) ONLY**, restricted to `<OPERATOR_IP>/32`.
   - **Zero** inbound rules for ports 80, 443, 3000, 8000, 8080, or 11434.
2. **Host UFW Firewall**:
   - Default policy: `deny incoming`, `allow outgoing`.
   - Port 22 allowed.
   - Port 11434 allowed ONLY from `127.0.0.1` and Docker bridge subnets (`172.16.0.0/12`).
   - All external inbound traffic to ports 3000, 8000, 8080, 11434 explicitly blocked.
3. **Container Network Isolation**:
   - The Gateway container binds only to host loopback `127.0.0.1:3000:8080`.
   - The FastAPI backend is not accessible on any host port; it communicates exclusively through internal Docker networks (`local` and `ingress`).
   - All containers run as non-root users (`uid 10001` backend, `uid 1000` frontend) with `cap_drop: ALL`, `read_only: true`, and `no-new-privileges: true`.

---

## 5. Linux Docker vs. Local Host Differences & Resolutions

| Difference | Local Development (Windows) | AWS EC2 (Ubuntu Linux) | Resolution in Reckon |
| :--- | :--- | :--- | :--- |
| **Host Loopback from Container** | `host.docker.internal` is natively routed to Windows loopback by Docker Desktop. | `host.docker.internal` does not route to host loopback automatically. | Handled via `extra_hosts: ["host.docker.internal:host-gateway"]` in `compose.yaml` and `deploy/compose.aws.yaml`. |
| **Ollama Daemon Binding** | Listens on Windows loopback `127.0.0.1:11434`. | Host bridge packets arrive at `172.18.0.1`. If bound to `127.0.0.1`, Linux kernel drops the packets. | `install_ollama.sh` configures systemd override `OLLAMA_HOST=0.0.0.0:11434`. Host UFW restricts port 11434 strictly to Docker bridge and loopback. |
| **File Permissions on Mounted Volumes** | Windows NTFS transparently maps permissions to container users. | Linux enforces POSIX UID/GID checks. Containers with non-root UID 10001 cannot write if directory is owned by root. | `deploy.sh` initializes `reckon_state` volume with `chown -R 10001:10001` before mounting. |
| **Restart & Log Persistence** | Containers restarted manually; logs kept in ephemeral Docker Desktop cache. | Host may reboot or run unattended; unconstrained logs can fill EBS volume. | `deploy/compose.aws.yaml` specifies `restart: unless-stopped` and rotating json-file logging capped at 30 MB per container. |

---

## 6. Step-by-Step Operator Runbook

### Step 1: Security Group Creation
In the AWS Management Console (`ap-southeast-2` Sydney):
1. Navigate to **EC2 > Security Groups > Create Security Group**.
2. Name: `reckon-sg-private`.
3. Inbound Rules:
   - Type: `SSH` | Protocol: `TCP` | Port: `22` | Source: `My IP` (`<YOUR_IP>/32`).
4. Outbound Rules: Leave default (Allow all traffic).

### Step 2: EC2 Instance Provisioning
1. Launch Instance:
   - Name: `reckon-evaluation-host`
   - AMI: **Ubuntu Server 24.04 LTS (HVM), SSD Volume Type** (`ami-0...` x86_64)
   - Instance Type: **`t3.xlarge`** (4 vCPU, 16 GiB RAM)
   - Key Pair: Create or select key pair (e.g. `reckon-sydney.pem`)
   - Network Settings: Attach `reckon-sg-private`
   - Storage: 1 x **40 GiB gp3 EBS** (Encrypted)
2. Launch the instance and note its **Public IPv4 Address** (`<EC2_PUBLIC_IP>`).

### Step 3: Connect to Instance & Clone Codebase
```bash
# On your local workstation
chmod 400 ~/.ssh/reckon-sydney.pem
ssh -i ~/.ssh/reckon-sydney.pem ubuntu@<EC2_PUBLIC_IP>

# On the EC2 host: Clone the repository into /opt/reckon
sudo git clone https://github.com/Mirin-Dixit/reckon.git /opt/reckon
sudo chown -R ubuntu:ubuntu /opt/reckon
cd /opt/reckon
```

### Step 4: Host Preparation (Docker & Firewall)
```bash
# Run host setup (installs Docker, Compose plugin, UFW firewall)
sudo bash deploy/aws/setup_host.sh

# Apply new Docker group membership without logging out
newgrp docker
```

### Step 5: Install & Configure Ollama
```bash
# Installs Ollama, sets systemd override to 0.0.0.0:11434, pulls models
sudo bash deploy/aws/install_ollama.sh
```

### Step 6: Deploy Containers
```bash
# Builds images, sets permissions, starts containers with AWS override
bash deploy/aws/deploy.sh
```

### Step 7: Run Automated Verification Suite
```bash
# Executes comprehensive health, inference, security, and persistence tests
bash deploy/aws/verify.sh
```

### Step 8: Access the Application via SSH Tunnel
From your **local workstation** (in a separate terminal window):
```bash
ssh -i ~/.ssh/reckon-sydney.pem -N -L 3000:127.0.0.1:3000 ubuntu@<EC2_PUBLIC_IP>
```
Open your local web browser and navigate to:
**`http://localhost:3000`**

The full Reckon Query Lab, Evaluation Dashboard, Risk–Coverage Visualizations, and Evidence Ledger will load securely.

---

## 7. Disaster Recovery & SQLite Backup/Restore

### Creating a Snapshot & Safe Shutdown
Before stopping your EC2 instance to preserve AWS credits:
```bash
# On the EC2 host
bash deploy/aws/backup_and_stop.sh
```
This executes an online SQLite-consistent backup via Python/SQLite backup API, verifies database integrity (`PRAGMA integrity_check`) and table counts, verifies the snapshot is non-empty, computes a SHA-256 checksum, archives precomputed dense vectors if present, and stops the Compose project (`reckon`) cleanly.

Download the verified backup to your local machine:
```bash
# On your local workstation
scp -i ~/.ssh/reckon-sydney.pem ubuntu@<EC2_PUBLIC_IP>:/opt/reckon/backups/reckon_state_backup_*.tar.gz ./backups/
```

### Restoring State from Backup
To restore state into a fresh deployment:
```bash
# On the EC2 host
docker volume create reckon_state
docker run --rm -v reckon_state:/state -v /opt/reckon/backups:/backups alpine:3.20 sh -c '
    tar -xzf /backups/reckon_state_backup_<TIMESTAMP>.tar.gz -C /state &&
    chown -R 10001:10001 /state
'
bash deploy/aws/deploy.sh
```

---

## 8. Troubleshooting FAQ

### 1. `Local Ollama service is unavailable (HTTP 503)`
- **Cause**: Ollama daemon is not listening on `0.0.0.0` or UFW is blocking container bridge traffic.
- **Fix**: Check `systemctl status ollama`. Verify `/etc/systemd/system/ollama.service.d/override.conf` contains `Environment="OLLAMA_HOST=0.0.0.0:11434"`. Ensure UFW allows Docker bridge: `sudo ufw allow from 172.16.0.0/12 to any port 11434 proto tcp`.

### 2. `Permission denied on /state/experiments.sqlite3`
- **Cause**: Docker volume files were created as root (`uid 0`), but the backend runs as `uid 10001`.
- **Fix**: Run `docker run --rm -v reckon_state:/state alpine:3.20 chown -R 10001:10001 /state`.

### 3. High CPU Usage or Slow Responses During Evaluation
- **Cause**: CPU inference on quantized models (`qwen3:4b-q4_K_M`) consumes 100% of available vCPUs while generating.
- **Fix**: This is expected CPU behavior. On `t3.xlarge` (4 vCPUs), generation operates at ~12-16 tokens/second. Ensure `OLLAMA_NUM_PARALLEL=1` and `OLLAMA_KEEP_ALIVE=24h` are set so models remain memory-resident.
