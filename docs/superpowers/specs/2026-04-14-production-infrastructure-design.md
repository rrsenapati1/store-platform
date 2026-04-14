# Production Infrastructure Design

Date: 2026-04-14
Task: `CP-024`
Status: Drafted after design approval

## Goal

Stand up production-grade infrastructure for the Store control plane with explicit environment separation, migration discipline, backup and restore posture, secrets handling, and desktop release artifact hosting suitable for public release.

This task does not attempt to solve all security, observability, or CI/CD automation concerns. It establishes the operational foundation those later tasks will rely on.

## Chosen Hosting Model

The accepted infrastructure model is:

- `staging`: two VMs
  - `app VM`
  - `db VM`
- `production`: two VMs
  - `app VM`
  - `db VM`
- managed object storage for:
  - Postgres backup artifacts
  - restore drill artifacts
  - Store Desktop release manifests and installers

This keeps cost and ownership aligned with a self-managed deployment while still giving better isolation than a single combined VM.

## Scope

### In Scope

- Environment contract for `dev`, `staging`, and `prod`
- App/worker deployment contract for the control plane
- Dedicated Postgres VM contract
- Secrets and environment configuration contract
- Backup policy and object-storage upload contract
- Restore drill workflow and operator runbook
- Migration discipline for staging and production deployments
- Environment-safe desktop release/update hosting contract
- Deployment and operations runbooks

### Out of Scope

- Full security hardening and alerting depth
- Hosted CI/CD automation
- Managed cloud platform migration
- Multi-region HA/failover
- Customer-facing support and public docs

Those belong primarily to `CP-025`, `CP-026`, and `CP-027`.

## Environment Layout

Each non-dev environment has the same shape:

### App VM

Runs:

- reverse proxy with TLS termination
- `control-plane-api` web process
- `operations-worker` process
- deployment scripts and migration entrypoint

Responsibilities:

- serve API traffic for platform-admin and owner-web
- serve auth/runtime APIs used by Store Desktop
- run async operations worker
- run schema migrations from approved releases
- publish health and deployment status

### DB VM

Runs:

- Postgres only

Responsibilities:

- hold authoritative control-plane data
- expose Postgres only on private network or restricted firewall rules
- store DB files on dedicated volume if available
- support backup and restore operations independently from app deploys

### Managed Object Storage

Stores:

- nightly or scheduled Postgres backup artifacts
- WAL/incremental archives if enabled later
- restore verification artifacts and metadata
- desktop release artifacts and update manifests

Storage must be separated by environment using either:

- separate buckets, or
- strict environment prefixes with isolated credentials

## Environment Separation

The repo must support and document three distinct environments:

- `dev`
- `staging`
- `prod`

Separation rules:

- separate VMs for `staging` and `prod`
- separate Postgres instances and data volumes
- separate secret sets
- separate object-storage prefixes/buckets
- separate Store Desktop update channels
- separate control-plane origins

No environment may share the same database or release channel.

## Service Boundary

The app VM should keep the web process and worker process distinct even though they run on the same host.

Required services:

- `store-control-plane-api`
- `store-control-plane-worker`
- `reverse-proxy`

Required DB-side service:

- `postgres`

This avoids a monolithic “one process does everything” deployment and keeps worker restarts separate from API traffic handling.

## Secrets and Configuration

### App VM Secrets

The app VM must receive environment-specific secrets for:

- database connection string
- Korsenex IDP JWKS/auth configuration
- Cashfree recurring billing credentials
- Razorpay recurring billing credentials
- IRP provider credentials and secret-encryption key
- object storage access for backups and release artifacts
- desktop updater/release channel origin values

These must not be committed in repo files.

Recommended contract:

- checked-in `.env.example` remains non-secret
- actual environment values are injected through secure host-local secret files or systemd environment files

### DB VM Secrets

The DB VM must keep:

- Postgres superuser/admin credentials
- app user credentials
- backup job credentials if separate

DB credentials must not be public and Postgres must not be internet-exposed.

## Network Posture

### Public Exposure

Expose publicly:

- `80/443` on the app VM only

Do not expose publicly:

- Postgres port on DB VM
- worker-only interfaces

### Access Control

- SSH restricted to operator/admin IPs
- DB VM access limited to app VM and operator/admin IPs
- TLS terminated at the reverse proxy

This is not the full security hardening task, but the network baseline must not be porous.

## Backup Policy

The first infrastructure slice must provide real backup posture, not only a statement that backups “should exist”.

Minimum backup policy:

- scheduled Postgres full backup at least daily
- upload backup artifact to managed object storage
- retention policy with short-term operational recovery plus longer-term disaster recovery
- metadata recording:
  - timestamp
  - environment
  - app release version
  - Alembic head
  - backup artifact path

The backup flow must be scriptable and runnable by the operator on the target VM.

Future WAL/incremental backup support can be added later, but the first slice must already support full restore drills reliably.

## Restore Drill

The repo must define an explicit restore drill, not just backup creation.

Restore drill flow:

1. Provision or reuse a clean staging restore target.
2. Download a backup artifact from object storage.
3. Restore Postgres from that artifact.
4. Point a control-plane app instance at the restored DB.
5. Confirm:
   - DB boots
   - Alembic state is coherent
   - control-plane health is up
   - basic auth flow works
   - owner-web billing/tenant flow works
   - runtime auth flow still works

This validates both artifact integrity and operational recovery steps.

The runbook should record target expectations such as:

- RPO
- RTO
- operator responsibilities

## Deployment Flow

The deployment model should be release-based and runbook-driven.

Expected production deployment flow:

1. Build release artifact from repo.
2. Upload backend release artifact to the app VM.
3. Upload desktop release/update artifacts to environment storage if needed.
4. Run pre-migration DB backup.
5. Run `alembic upgrade head` from the app release against the DB VM.
6. Restart/roll:
   - API service
   - worker service
7. Run post-deploy verification:
   - health route
   - auth exchange / me
   - owner-web critical flow
   - worker process alive
   - packaged runtime auth check against the environment

This task does not require blue/green or zero-downtime deployment sophistication yet, but it does require explicit and repeatable deployment steps.

## Migration Discipline

Production schema changes must be controlled.

Rules:

- staging migration must run before production migration
- every production schema deployment takes a pre-migration backup
- Alembic is the only normal schema change path
- manual SQL changes are emergency-only and must be documented
- deployed release version and Alembic head must be recorded for the environment

Rollback rule:

- app-only rollback is allowed only when schema remains backward-compatible
- otherwise the operator must use restore-forward or restore-from-backup procedure

This task should document those rules clearly in the runbook and scripts.

## Desktop Release Hosting Contract

Store Desktop already has packaging/update channel logic. `CP-024` must connect that to real environment infrastructure.

Per environment:

- one control-plane origin
- one updater manifest location
- one installer/artifact prefix in object storage

This ensures:

- staging desktops do not accidentally update from prod
- prod desktops do not point at localhost or ad hoc URLs
- release hosting and environment hosting are operationally aligned

## Deliverables

The first implementation slice for `CP-024` should produce:

- deployment config templates for app VM and DB VM
- production/staging environment contract in repo docs
- backup script(s)
- restore script(s) or restore helper(s)
- runbook for deployment
- runbook for backup/restore drill
- environment variable examples and required secret inventory
- verification script extension for staging/prod-style checks

It should not yet attempt:

- full hosted CI/CD
- full centralized observability stack
- advanced secrets manager integration if local secure files are the chosen host contract

## Verification Requirements

Before `CP-024` is marked done, operators must be able to prove:

- environment config is explicit for `dev`, `staging`, `prod`
- app and worker can start against a non-local Postgres target
- backup artifact uploads to managed object storage
- restore drill can boot a clean staging restore target
- Alembic migration discipline is documented and executable
- desktop updater/control-plane origin are environment-safe

## Risks To Control

The main risks in this task are:

- staging/prod configuration drift
- local-only assumptions baked into deploy scripts
- backups that exist but cannot be restored
- schema deploys without recovery posture
- release artifact hosting that mixes staging/prod channels

The implementation must bias toward explicit environment contracts and scripted operator workflows rather than clever but opaque automation.
