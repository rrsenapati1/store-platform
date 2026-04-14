# CP-024 Production Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add self-managed staging and production infrastructure foundations for the Store control plane with two-VM deployment templates, managed secrets contract, Postgres backup and restore tooling, deployment discipline, and environment-safe verification.

**Architecture:** Keep runtime application behavior thin and move operational logic into a small `store_control_plane.ops` package plus explicit CLI entrypoints. The app VM and DB VM remain separate per environment, object storage is treated as an S3-compatible artifact and backup target, and deployment or recovery is driven by repo-owned scripts and runbooks instead of undocumented host-local steps.

**Tech Stack:** FastAPI, Pydantic settings, SQLAlchemy async stack, Python CLI scripts, pytest, managed object storage via boto3, systemd and nginx templates, Markdown runbooks

---

## Planned File Structure

### Settings and environment contract

- `services/control-plane-api/store_control_plane/config/settings.py`
  - expand the environment model so app runtime and ops scripts can resolve deployment environment, public origin, object-storage contract, and release metadata without hardcoded VM-local assumptions
- `services/control-plane-api/.env.example`
  - keep the generic local example aligned with new required settings
- `services/control-plane-api/ops/env/app.staging.env.example`
- `services/control-plane-api/ops/env/app.prod.env.example`
- `services/control-plane-api/ops/env/db.staging.env.example`
- `services/control-plane-api/ops/env/db.prod.env.example`
  - checked-in non-secret templates for host-local environment files on app and DB VMs

### Ops modules and CLI entrypoints

- `services/control-plane-api/store_control_plane/ops/__init__.py`
- `services/control-plane-api/store_control_plane/ops/object_storage.py`
- `services/control-plane-api/store_control_plane/ops/postgres_backup.py`
- `services/control-plane-api/store_control_plane/ops/postgres_restore.py`
- `services/control-plane-api/store_control_plane/ops/deployment.py`
  - testable Python modules for object-storage upload/download, backup metadata, restore orchestration, and deployment sequencing
- `services/control-plane-api/scripts/backup_postgres.py`
- `services/control-plane-api/scripts/restore_postgres.py`
- `services/control-plane-api/scripts/deploy_control_plane_release.py`
- `services/control-plane-api/scripts/verify_deployed_control_plane.py`
  - operator-facing CLI entrypoints that call the modules above

### Health and verification surface

- `services/control-plane-api/store_control_plane/routes/system.py`
- `services/control-plane-api/store_control_plane/schemas/system.py`
- `services/control-plane-api/store_control_plane/services/system_status.py`
  - add a production-safe system-health and deployment-status response for staging and prod smoke checks

### Tests

- `services/control-plane-api/tests/test_settings.py`
- `services/control-plane-api/tests/test_postgres_backup_ops.py`
- `services/control-plane-api/tests/test_postgres_restore_ops.py`
- `services/control-plane-api/tests/test_deployment_ops.py`
- `services/control-plane-api/tests/test_system_routes.py`
- `services/control-plane-api/tests/test_verify_deployed_control_plane.py`

### Ops templates and runbooks

- `services/control-plane-api/ops/systemd/store-control-plane-api.service.example`
- `services/control-plane-api/ops/systemd/store-control-plane-worker.service.example`
- `services/control-plane-api/ops/systemd/store-control-plane-backup.service.example`
- `services/control-plane-api/ops/systemd/store-control-plane-backup.timer.example`
- `services/control-plane-api/ops/nginx/store-control-plane.conf.example`
- `docs/runbooks/control-plane-production-deployment.md`
- `docs/runbooks/control-plane-backup-restore.md`
- `docs/runbooks/control-plane-verification.md`
- `docs/runbooks/store-desktop-packaging-distribution.md`
- `services/control-plane-api/README.md`

### Ledger and worklog

- `docs/TASK_LEDGER.md`
- `docs/WORKLOG.md`

### Dependencies

- `services/control-plane-api/requirements.txt`
  - add the minimal object-storage dependency required for scriptable backup and restore

---

### Task 1: Expand the deployment and secrets settings contract

**Files:**
- Modify: `services/control-plane-api/store_control_plane/config/settings.py`
- Modify: `services/control-plane-api/tests/test_settings.py`
- Modify: `services/control-plane-api/.env.example`
- Create: `services/control-plane-api/ops/env/app.staging.env.example`
- Create: `services/control-plane-api/ops/env/app.prod.env.example`
- Create: `services/control-plane-api/ops/env/db.staging.env.example`
- Create: `services/control-plane-api/ops/env/db.prod.env.example`
- Modify: `services/control-plane-api/README.md`

- [ ] **Step 1: Write failing settings tests for deployment environment, public origin, release metadata, and object-storage configuration**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_settings.py -q` and confirm red**
- [ ] **Step 3: Add new settings fields and normalization for environment name, public base URL, release version label, object-storage endpoint, bucket or prefix, backup retention, and desktop artifact path contract**
- [ ] **Step 4: Expand `.env.example` and add non-secret app or DB environment-file templates for staging and prod**
- [ ] **Step 5: Update the service README so local vs deployed environment variables are explicit instead of implied**
- [ ] **Step 6: Re-run `python -m pytest services/control-plane-api/tests/test_settings.py -q` and confirm green**
- [ ] **Step 7: Commit**

### Task 2: Add object-storage and Postgres backup tooling

**Files:**
- Modify: `services/control-plane-api/requirements.txt`
- Create: `services/control-plane-api/store_control_plane/ops/__init__.py`
- Create: `services/control-plane-api/store_control_plane/ops/object_storage.py`
- Create: `services/control-plane-api/store_control_plane/ops/postgres_backup.py`
- Create: `services/control-plane-api/scripts/backup_postgres.py`
- Create: `services/control-plane-api/tests/test_postgres_backup_ops.py`

- [ ] **Step 1: Write failing backup-operation tests for metadata generation, object-key layout, and upload invocation**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_postgres_backup_ops.py -q` and confirm red**
- [ ] **Step 3: Add the minimal object-storage dependency and implement a small S3-compatible storage client wrapper**
- [ ] **Step 4: Implement backup planning and execution helpers that produce deterministic artifact names, metadata manifests, and retention-friendly prefixes**
- [ ] **Step 5: Add the `backup_postgres.py` CLI with flags for environment, artifact path, bucket or prefix overrides, and dry-run posture**
- [ ] **Step 6: Re-run `python -m pytest services/control-plane-api/tests/test_postgres_backup_ops.py -q` and confirm green**
- [ ] **Step 7: Commit**

### Task 3: Add restore and release-deployment orchestration

**Files:**
- Create: `services/control-plane-api/store_control_plane/ops/postgres_restore.py`
- Create: `services/control-plane-api/store_control_plane/ops/deployment.py`
- Create: `services/control-plane-api/scripts/restore_postgres.py`
- Create: `services/control-plane-api/scripts/deploy_control_plane_release.py`
- Create: `services/control-plane-api/tests/test_postgres_restore_ops.py`
- Create: `services/control-plane-api/tests/test_deployment_ops.py`

- [ ] **Step 1: Write failing restore and deploy-orchestration tests for pre-migration backup ordering, Alembic execution, API or worker restart order, and rollback guardrails**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_postgres_restore_ops.py services/control-plane-api/tests/test_deployment_ops.py -q` and confirm red**
- [ ] **Step 3: Implement restore helpers for artifact download, metadata validation, target-database guardrails, and restore command planning**
- [ ] **Step 4: Implement deployment helpers that model the release bundle path, pre-migration backup, Alembic upgrade, and separate API or worker restarts**
- [ ] **Step 5: Add `restore_postgres.py` and `deploy_control_plane_release.py` CLIs with explicit destructive-action confirmations and dry-run support**
- [ ] **Step 6: Re-run `python -m pytest services/control-plane-api/tests/test_postgres_restore_ops.py services/control-plane-api/tests/test_deployment_ops.py -q` and confirm green**
- [ ] **Step 7: Commit**

### Task 4: Add deployed health and verification surfaces

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/system_status.py`
- Modify: `services/control-plane-api/store_control_plane/routes/system.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/system.py`
- Create: `services/control-plane-api/scripts/verify_deployed_control_plane.py`
- Create: `services/control-plane-api/tests/test_system_routes.py`
- Create: `services/control-plane-api/tests/test_verify_deployed_control_plane.py`

- [ ] **Step 1: Write failing tests for `GET /v1/system/health`, deployment-status payload, and the deployed-verifier CLI**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_system_routes.py services/control-plane-api/tests/test_verify_deployed_control_plane.py -q` and confirm red**
- [ ] **Step 3: Add a production-safe system-status service that reports environment, release version, worker expectations, and database connectivity posture without exposing secrets**
- [ ] **Step 4: Add `verify_deployed_control_plane.py` with staging vs prod-safe smoke modes and explicit health, auth, worker, and release checks**
- [ ] **Step 5: Re-run `python -m pytest services/control-plane-api/tests/test_system_routes.py services/control-plane-api/tests/test_verify_deployed_control_plane.py -q` and confirm green**
- [ ] **Step 6: Commit**

### Task 5: Add self-managed VM templates and operator runbooks

**Files:**
- Create: `services/control-plane-api/ops/systemd/store-control-plane-api.service.example`
- Create: `services/control-plane-api/ops/systemd/store-control-plane-worker.service.example`
- Create: `services/control-plane-api/ops/systemd/store-control-plane-backup.service.example`
- Create: `services/control-plane-api/ops/systemd/store-control-plane-backup.timer.example`
- Create: `services/control-plane-api/ops/nginx/store-control-plane.conf.example`
- Create: `docs/runbooks/control-plane-production-deployment.md`
- Create: `docs/runbooks/control-plane-backup-restore.md`
- Modify: `docs/runbooks/control-plane-verification.md`
- Modify: `docs/runbooks/store-desktop-packaging-distribution.md`
- Modify: `services/control-plane-api/README.md`

- [ ] **Step 1: Write down the exact service-template and runbook responsibilities in the patch so no template is a placeholder-only file**
- [ ] **Step 2: Add systemd and nginx example templates for the app VM, worker, and scheduled backup timer**
- [ ] **Step 3: Add the production deployment runbook covering staging-first rollout, pre-migration backup, Alembic, API or worker restart, and post-deploy checks**
- [ ] **Step 4: Add the backup and restore runbook covering artifact upload, retention expectations, restore drill, RPO, RTO, and operator ownership**
- [ ] **Step 5: Update the verification and desktop-packaging runbooks so staging/prod control-plane origins and update-channel hosting are aligned with the new two-VM environment model**
- [ ] **Step 6: Commit**

### Task 6: Verify the full infrastructure slice and publish

**Files:**
- Modify only if verification exposes gaps
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Run `python -m pytest services/control-plane-api/tests/test_settings.py services/control-plane-api/tests/test_postgres_backup_ops.py services/control-plane-api/tests/test_postgres_restore_ops.py services/control-plane-api/tests/test_deployment_ops.py services/control-plane-api/tests/test_system_routes.py services/control-plane-api/tests/test_verify_deployed_control_plane.py -q`**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests -q`**
- [ ] **Step 3: Run `python services/control-plane-api/scripts/backup_postgres.py --help`**
- [ ] **Step 4: Run `python services/control-plane-api/scripts/restore_postgres.py --help`**
- [ ] **Step 5: Run `python services/control-plane-api/scripts/deploy_control_plane_release.py --help`**
- [ ] **Step 6: Run `python services/control-plane-api/scripts/verify_deployed_control_plane.py --help`**
- [ ] **Step 7: Mark `CP-024` done in the ledger and add the worklog entry**
- [ ] **Step 8: Commit**
