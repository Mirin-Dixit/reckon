# Optional AWS architecture — not deployed

AWS is optional and is not part of the zero-cost local requirement. No account,
credentials, resources or cloud inference are required or provisioned here.
Compute, EBS storage/snapshots, network traffic and optional managed services can
incur charges. Do not assume a free tier covers this application. Consult current
[EC2 pricing](https://aws.amazon.com/ec2/pricing/on-demand/) and obtain a separate
budget/deployment authorization before doing any cloud work.

The smallest private research deployment would be one Linux EC2 instance with
encrypted EBS holding Docker-owned SQLite state. Run a single backend owner and
the same local gateway/frontend. Do not publish application ports in security
groups. Access via a separately configured, least-privilege
[Systems Manager port-forwarding session](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html)
to the loopback gateway; this requires IAM, SSM Agent and appropriate connectivity.
No SSM/AWS command is executed by this repository. Treat snapshots and downloaded
reports as research data with access controls and retention policy.

This simple design has downtime on upgrades and a single-instance failure domain.
SQLite is a single-owner local store, not a multi-instance shared filesystem
database. Never put the database on a shared mount to run multiple API owners.
Restore/recovery and backup verification require explicit operational approval.
Do not upload protected datasets/reviews, native experiment databases, environment
files or model artifacts without separate data-transfer approval.

A public service would require a new, reviewed access boundary: authentication,
authorization, TLS, trusted proxy/host configuration, CSRF/origin review, traffic
limits, monitoring, patching, backups and cost controls. An ALB/OIDC/private-subnet
design is one option, with additional cost and complexity. The current exact-origin
and loopback checks must not simply be disabled to make public routing work.
Existing trusted Python callbacks are not sandboxed. No mandatory paid provider,
managed vector database, RDS or cloud model service is introduced. Cloud inference
remains prohibited under the project's zero-spending constraint.

## Completion addendum: status and authorization gate

**Public EC2 deployment: BLOCKED.** Local Windows Docker runtime and user Chrome
acceptance passed in the synthetic-only scope documented in local.md. This is not
EC2 deployment or public security acceptance; image/OS-wide CVE scanning remains
unverified. No EC2, SSH, IAM, DNS, TLS,
billing-console or cloud-inference operation has been performed.

The steps below are an operator runbook, not authorization to execute them. Stop
before importing a key, provisioning resources, transferring project data or
exposing a service and obtain explicit approval. Local use remains independent of
AWS. A private SSH tunnel is the only currently compatible remote-access design;
public HTTPS requires the separate implementation/security gate below.

## Size the application, not a model server

For a first **synthetic application-only** trial, plan an x86-64 Ubuntu Server
24.04 LTS instance, for example `t3a.large` (2 vCPUs, 8 GiB RAM), where available.
Confirm specifications and regional availability in the
[EC2 instance reference](https://docs.aws.amazon.com/ec2/latest/instancetypes/gp.html)
before provisioning. This is an engineering starting estimate, not a benchmarked
capacity guarantee. Use standard CPU-credit mode for a burstable trial if you want
to avoid surplus-credit charges, accepting throttling; verify that option and its
pricing. A non-burstable instance is an alternative requiring a fresh cost estimate.

Budget at least 2 vCPUs, 8 GiB RAM and 40 GiB encrypted gp3 EBS; 60 GiB gives more
room for image/build caches and backups. Keep at least 1.5 GiB available host RAM;
build-time peaks and Docker overhead are additional to the 1792 MiB service limits.
Measure rather than assume capacity. Do not use a micro instance for builds based
on a free-tier label. Debian/Alpine userspace in these Linux images can run on an
Ubuntu Linux host; the pinned manifest digests, Linux package installation and
actual container startup passed on Windows Docker Desktop; EC2 still requires
its own runtime verification. Prefer amd64 initially;
ARM/Graviton needs its own image/build/runtime checks.

This does **not** size or authorize Qwen/Ollama execution. The Compose stack has
no model server, model volume or GPU service. Container loopback is not host
Ollama. Existing native model measurements cannot establish EC2 inference capacity.
Do not download models or relax the local-only embedding/provider adapters.

Choose a region by latency to users, data-residency constraints, available instance
types/quotas, EBS and network prices, not by an assumed cheapest/free region. For
an India-based operator, Mumbai may be convenient, but compare actual regional
costs. Use one explicitly recorded region/AZ for the trial and tag every resource.

## Budget before provisioning

1. In the account's Billing console, inspect the active plan, creation-date rules,
   credit expiry/balance, eligible services and current regional usage. The
   [current Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/) and the
   account's actual entitlement govern; do not apply an old "750 hours" assumption.
2. Create a [Pricing Calculator](https://calculator.aws/) estimate for the selected
   region: instance hours, EBS capacity/IOPS/throughput, snapshots, public IPv4,
   outbound bandwidth, and any DNS/domain, certificate automation, load-balancer,
   monitoring/log retention or NAT costs. The suggested instance is not claimed
   eligible for free compute. Avoid NAT gateways, ALBs and new domains for a private
   trial unless separately approved. Package/image transfers also use networking.
3. Review taxes/currency conversion and other resources already in the account.
   Record an approved maximum duration and spend estimate before clicking Launch.
4. Configure a low actual-and-forecast cost budget, notifications to a verified
   address and eligible Free Tier usage alerts; check Cost Explorer/Billing daily
   during the trial. Check the price of monitoring/budget features themselves.
   [Budget notifications](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
   can arrive after costs accumulate: alerts are not a hard spending cap.

Stopping EC2 stops normal instance compute billing once stopped, but retained
EBS, snapshots and retained networking resources may still incur charges. An
automatically assigned public IPv4 and an allocated Elastic IP have different
lifecycle behavior; inventory actual resources rather than assuming addresses were
released. See [EC2 lifecycle charges](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html).
No cost estimate or account eligibility was verified using credentials here.

## Private EC2 procedure, only after authorization

### 1. Key, instance and network

Create a dedicated passphrase-protected SSH key on the laptop, outside the repository:

```powershell
if (Test-Path "$env:USERPROFILE\.ssh\reckon-ec2") { throw 'Key already exists; do not overwrite it' }
ssh-keygen -t ed25519 -a 64 -f "$env:USERPROFILE\.ssh\reckon-ec2"
```

This creates a local private key and `.pub` public key; it allocates no AWS resource.
Keep the private key and passphrase off Git, chat and EC2. Import only the public
key into EC2 after approval. Check the displayed fingerprint; if interrupted,
inspect the files before retrying. Retain the key securely for recovery. Deleting
an AWS key-pair entry does not revoke keys already installed on a running host.

In the EC2 console, launch the recorded amd64 Ubuntu AMI/instance type, encrypted
EBS size and dedicated key. Record the instance/AMI/security-group/volume IDs,
region, creation time and intended teardown time. Use no embedded credentials,
user-data secrets or broad IAM role. Launching allocates billable resources;
terminate only through an approved cleanup after backing up any required data.

For the currently supported private trial:

| Direction | Rule and reason |
|---|---|
| Inbound | TCP 22 from the operator's current public IPv4 `/32` only, for SSH. No inbound 80, 443, 3000, 8000, 8080, 11434 or database port. Do not use `0.0.0.0/0` for SSH. An SSM-only design can instead avoid inbound SSH, but requires separately configured IAM/connectivity. |
| Outbound | HTTPS 443 for approved registries/OS repositories and necessary AWS endpoints; permit HTTP 80 only if the selected OS package mirrors require it. DNS must work through the approved VPC resolver. SGs are IP-based, not hostname allowlists. Further filtering needs its own design. Replies to allowed connections are stateful. |
| IPv6 | Do not add IPv6 ingress as an accidental bypass. Review any IPv6 routes/rules explicitly. |

A public subnet/Internet Gateway and public IPv4 can support operator-restricted
SSH without a NAT gateway; they do not authorize public application ports. Review
security groups, route tables and network ACLs together. The application's internal
Docker network stays isolated even while the host downloads build dependencies.

Verify the SSH **host** fingerprint through a trusted AWS console/system-log
channel before accepting the first connection. The server host key is distinct
from the user's login key. If it changes, stop and investigate; never bypass with
`StrictHostKeyChecking=no`. On the laptop:

```powershell
ssh -i "$env:USERPROFILE\.ssh\reckon-ec2" ubuntu@<INSTANCE_PUBLIC_IP>
```

This opens an encrypted remote shell, not an app deployment. Existing EC2/traffic
charges continue. Confirm `whoami` is `ubuntu`, `uname -m` is `x86_64`, and
`cat /etc/os-release` identifies the intended Ubuntu release. Exit with `exit`.

### 2. Install Docker on the approved Ubuntu host

Read [Docker's Ubuntu installation instructions](https://docs.docker.com/engine/install/ubuntu/)
and check for conflicting preinstalled packages first; do not blindly remove them.
For the specified Ubuntu 24.04 (`noble`) host, these commands add Docker's signed
repository and install Engine/Compose. They have **not** been executed here:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker version
sudo docker compose version
```

Verify the repository/signing-key instructions against the current official page.
These change OS packages, APT trust configuration and a root-capable system service;
downloads and running-host charges may apply. Use `sudo docker` deliberately rather
than granting general users Docker-group/root-equivalent access. Failure means stop
and inspect APT/service logs, not disable signature checks. Disabling Docker stops
its service; removing packages is a separate operator decision and must not remove
state volumes. No Docker socket is mounted into application containers.

### 3. Transfer only approved application code

Do not upload the dirty working directory. The current HEAD does **not** contain
the uncommitted P6 implementation. After a separately approved P6 checkpoint,
substitute its reviewed SHA below. Until then, this preparation step is blocked;
do not treat the P5 commit as a deployable P6 release.

```powershell
git archive --format=tar -o "$env:TEMP\reckon-release.tar" <REVIEWED_P6_SHA> -- compose.yaml .dockerignore backend/Dockerfile backend/app frontend deploy data/benchmark/documents.jsonl data/fixtures/p4_synthetic_v1 docs/deployment
tar -tf "$env:TEMP\reckon-release.tar"
scp -i "$env:USERPROFILE\.ssh\reckon-ec2" "$env:TEMP\reckon-release.tar" ubuntu@<INSTANCE_PUBLIC_IP>:~/reckon-release.tar
```

Archive creates an allowlisted local bundle from one commit, excluding untracked
environments, real benchmark questions, native SQLite and reviewer edits. Inspect the **actual** archive: tracked files
can still be sensitive. Only the accepted corpus documents and synthetic fixtures
needed by Compose should transfer; no held-out questions, review data, private
databases, `.env`, credentials or model artifacts without separate approval. If
the reviewed commit contains extra research data, prepare a reviewed deployment
bundle that excludes it while retaining relative paths; do not transfer first and
clean up later. `.dockerignore` restricts image context, not SCP transmission.
SCP sends data to AWS and can incur transfer/storage charges; inspect the destination
and obtain data-transfer authorization. A public Git repository at a pinned SHA is
another option only if publishing its contents was already authorized.

On the host, choose a new release directory, never overwrite an existing release:

```bash
mkdir -p ~/reckon/releases/<REVIEWED_P6_SHA>
tar -tf ~/reckon-release.tar
tar -xf ~/reckon-release.tar -C ~/reckon/releases/<REVIEWED_P6_SHA>
cd ~/reckon/releases/<REVIEWED_P6_SHA>
sudo docker compose -p reckon-private config --quiet
sudo docker compose -p reckon-private build
sudo docker compose -p reckon-private up -d --wait
sudo docker compose -p reckon-private ps
curl --fail http://127.0.0.1:3000/api/v1/health
```

Extraction writes only the new release directory; inspect trusted archive paths
for traversal before extraction. Build downloads pinned images/dependencies and
uses disk/CPU credits; inspect failures without changing security guards. `up`
starts services and creates the separate `reckon-private` state volume. Use that
same project name from every release so updates retain state. No native records
are imported. Only existing corpus/fixture paths are read-only bind mounts.

The Compose environment deliberately contains no secrets and selects local Ollama
with no running model server. Do not add paid-provider credentials, AWS keys or
`NEXT_PUBLIC` secrets. Health may report configuration without proving provider
connectivity. For future genuine secrets, use a reviewed root-readable host file
or secret store and documented file ownership; they must not enter builds, shell
history, image layers or Git. Enabling cloud services requires fresh authorization.

For private browser access, run on the laptop in a separate terminal:

```powershell
ssh -N -L 3000:127.0.0.1:3000 -i "$env:USERPROFILE\.ssh\reckon-ec2" ubuntu@<INSTANCE_PUBLIC_IP>
```

Open `http://127.0.0.1:3000`. This is an SSH-encrypted private connection, **not**
public HTTPS acceptance. The local port must be free. Close the SSH terminal to
remove the tunnel; the EC2 containers keep running and may incur charges.

## Public security review and HTTPS gate

| Area | Classification and evidence |
|---|---|
| Authentication/authorization | **Requires an implementation fix; public BLOCKED.** There are no user/session/role checks. `local_access` authenticates neither a person nor a request. Writes, exports, saved results and expensive analysis would need authenticated, authorized access. |
| Origin versus identity | **Verified for intended local operation only.** `experiment_jobs.local_access` checks loopback peers/hosts and exact origins. CORS/origin is not authentication and is spoofable by non-browser clients. A public proxy makes remote requests appear loopback. |
| Public ports | **Requires configuration before deployment.** Current Compose publishes only `127.0.0.1:3000`; SG must not expose API/database ports. Local Docker publication is verified; an actual AWS SG remains unverified. |
| TLS/reverse proxy | **Requires an implementation fix.** `deploy/nginx.conf` is HTTP-only, accepts the loopback Host and uses fixed loopback upstreams. No certificate, renewal or HTTPS redirect is implemented. Do not simply publish it on port 80. |
| Public IP/domain/browser URL | **Requires an implementation fix.** `frontend/lib/configuration.ts::localBackendOrigin` rejects public API origins; the baked-in loopback browser URL points to a remote visitor's own machine. Current CORS/Host rules also reject a public domain. A reviewed same-origin HTTPS/authenticated gateway integration is needed; never replace these checks with wildcards. |
| Research data | **Verified for intended local operation, including container settings.** Images exclude databases/reviews, mounts are read-only except Docker-owned state, and synthetic/held-out gates remain. Authenticated public access must still prohibit gold/Test disclosure and curation-service exposure. |
| Unauthorized execution/exhaustion | **Requires an implementation fix for public use.** One queued worker, request limits and one analysis slot bound work but do not provide per-user quotas or prevent unauthenticated repeated execution. |
| Uploads/errors/timeouts | **Verified by existing focused/native tests.** Byte limits, cumulative receive deadline, safe errors and loopback rejection are implemented. No document-upload endpoint is added; the unrelated reviewer service is not shipped. Gateway size/origin/error guards passed local HTTP checks. |
| Privileges/secrets | **Verified in local containers; requires EC2 verification.** Non-root users, read-only roots, dropped capabilities and no-new-privileges were inspected. No secrets belong in these images. Never mount the Docker socket or grant broad host privileges. |
| Volumes/backups/recovery | **Requires configuration and verification.** One owner and rollback-journal SQLite are required; encrypted EBS, backup access, restore rehearsal and retention need operator setup. Read-only analysis must not recover or migrate records. |
| Logging/response leakage | **Verified in focused tests and local container checks.** API errors are sanitized. Nginx access/error logs and Docker Uvicorn access logs are disabled, avoiding arbitrary URL query-string capture. Future public authentication needs separately reviewed redacted audit events. Never include secrets in URLs. |
| Dependency vulnerabilities | **Not yet verified.** Image digests/versions are pinned, not certified safe. Current npm audit found eight moderate development-tooling findings and zero production-only findings. No image/OS-wide or Python advisory scan is claimed. Scan all built images and review OS/npm/Python advisories before public release; scanning may need network access and must not upload private images to an unapproved service. |

For a future public release, keep the same gateway architecture but first implement
and test the authenticated trust boundary and same-origin browser routing. Only
then provision an approved domain/address, add restrictive 443 ingress, configure
Nginx TLS with securely mounted keys and renewal, and redirect HTTP to HTTPS (port
80 only if needed for redirects/ACME). Test unauthenticated denial **before** adding
research records. An IP address alone is not an accepted TLS/domain solution.
Do not create a DNS zone, register a domain, request certificates or open ports now.
This runbook intentionally supplies no unsafe "public override" Compose file.

## Operations, update/rollback and cleanup

Use `sudo docker compose -p reckon-private logs --tail 100` for bounded logs,
`ps` for health, and `sudo ss -lntp` for host listeners. Do not send raw logs to a
third party; review even sanitized logs before sharing. Access logs being disabled
reduces leakage but is not a complete public audit trail. Container liveness does
not prove model readiness, scientific validity or persisted data correctness.

Use the consistent SQLite backup commands in [local recovery](local.md), adding
`sudo` and `-p reckon-private` on EC2. Download backups only with approved access
and encryption. Verify integrity on a disposable copy and rehearse restoration
outside the live volume. Use one process owner; never solve a lock error by deleting
the database or lock. Restore only while stopped, with UID 10001 ownership. EBS
snapshots supplement, not replace, an application-consistent tested backup.

For an update: record the current image IDs, Compose configuration and release SHA;
take a consistent backup. Before building anything new, preserve the running images
under distinct local tags, from the current release directory:

```bash
stamp=$(date -u +%Y%m%dT%H%M%SZ)
for service in backend frontend app-proxy gateway; do
  image_id=$(sudo docker compose -p reckon-private images -q "$service")
  test -n "$image_id" || exit 1
  sudo docker image tag "$image_id" "reckon-rollback-$service:$stamp"
done
cat > "$HOME/rollback-$stamp.json" <<EOF
{"services":{"backend":{"image":"reckon-rollback-backend:$stamp","pull_policy":"never"},"frontend":{"image":"reckon-rollback-frontend:$stamp","pull_policy":"never"},"app-proxy":{"image":"reckon-rollback-app-proxy:$stamp","pull_policy":"never"},"gateway":{"image":"reckon-rollback-gateway:$stamp","pull_policy":"never"}}}
EOF
chmod 600 "$HOME/rollback-$stamp.json"
```

Tagging preserves references to old local images, not new registry uploads. The
override file changes only image selection and refuses pulling a missing rollback
image. Verify all four tags with `sudo docker image ls`; record the stamp and old
release directory outside Git. It consumes retained image disk space/paid EBS.
If tagging fails, do not proceed. Inspect/build the next approved release in a new directory;
stop the whole namespace-sharing stack with `sudo docker compose -p reckon-private stop -t 45`;
start the new release with the same project name/volume and run the checks below.
Keep old tagged images and release files until acceptance. Do not run image pruning.
If validation fails, stop the stack and start the old approved images/configuration
from the old release with the recorded stamp:

```bash
# Run in the OLD release directory, replacing RECORDED_STAMP with the saved value.
sudo docker compose -p reckon-private -f compose.yaml -f "$HOME/rollback-RECORDED_STAMP.json" up -d --no-build --wait
```

The preceding stop must finish first. This recreates containers using the saved
images and retained volume; it does not rebuild or silently fetch another version.
Verify health, the same job/receipt and report provenance. Keep the failed release
logs. Restore data only if a schema-incompatible change occurred,
using an explicitly approved backup procedure; rolling back code does not undo writes.
There is downtime. Never run both releases against the same SQLite volume.

For shutdown, `stop -t 45` stops containers but leaves the EC2 host billable.
`down` removes containers/network but retains the named volume. After approved
backups, stop the instance in EC2; confirm its actual stopped state and inspect
retained EBS/address charges. For final authorized teardown, terminate the instance,
verify which volumes were deleted by their delete-on-termination setting, release
unneeded Elastic IPs, and remove only approved leftover snapshots/volumes, DNS,
load balancers or NAT resources. Inventory every region and check Billing again.
Termination and backup deletion are destructive, separately authorized actions;
no cleanup is performed by this document. Keep security groups/keys needed by any
other host. Never assume closing an SSH window stops EC2 billing.

## Reproducible deployment acceptance checklist

Record actual IDs, timestamps, commands, exit codes/statuses and configuration
hashes in an external operator log. Do not put secrets or private host details in Git.

1. **Cost/approval:** reviewed estimate and account eligibility; explicit resource
   and data-transfer authorization; verified billing notifications.
2. **Host:** EC2 running, correct region/AMI/architecture/RAM/disk; verified SSH
   fingerprint and successful restricted SSH; `docker version` and `compose version`.
3. **Stack:** `compose config --quiet`, build, `up -d --wait`, `ps`; retain actual
   logs on failure. Verify all health checks and loopback publication with `port`
   and `ss`. Inspect SG rules; probes of 8000/8080/11434 must not expose services.
4. **Private data path:** through the SSH tunnel, run the isolated synthetic-job,
   read-only analysis, report-export and stop/restart/freeze checks in
   [local Docker verification](local.md#remaining-windows-docker-verification-isolated-from-native-records).
   Keep the same job ID and receipt SHA; do not use native research records.
5. **Negative checks:** foreign-origin query denied 403, malformed JSON 422,
   missing saved ID 404; no raw exceptions/secrets in responses/logs, and no
   execution error counted as intentional abstention. Verify no model was invoked.
6. **Recovery:** restore a disposable backup copy, rehearse old-image rollback and
   confirm sole volume ownership before accepting persistence/recovery.
7. **Public checks — blocked until implementation/security approval:** verify DNS
   resolves to the intended address; `curl --fail https://<APP_DOMAIN>/evaluation`
   works with a trusted certificate, HTTP redirects to HTTPS, and unauthenticated
   API reads/writes are denied. Under an authorized session, verify health through
   the same gateway, saved retrieval, read-only analysis and report export. Ensure
   no browser requests target the visitor's localhost or mixed-content HTTP, and
   confirm restricted backend ports externally. None of these checks has passed here.

The version/info/config/log checks only inspect state, but EC2 charges continue.
Build/up/update change local images, services and volumes and consume paid host
resources. Synthetic test POSTs alter only their isolated volume. Backups create
additional sensitive files/storage. Stop/down are reversible while state is retained;
instance termination and volume/snapshot deletion are not. Use the recorded old
release/backup for recovery, and stop at any failed gate rather than relaxing controls.
