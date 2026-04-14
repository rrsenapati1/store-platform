# Async Jobs And Orchestration Design (CP-019)

Date: 2026-04-14  
Owner: Codex  
Status: Approved for implementation

## Goal

Add a production-grade asynchronous job boundary to the Store control plane so compliance preparation, supplier-report snapshot refresh, retry handling, and scheduled maintenance no longer depend on inline API request execution.

The first slice must:

- stay inside the current Postgres-backed control-plane deployment
- avoid introducing Redis or a second queue system before production infrastructure is in place
- make retries, leasing, and dead-letter posture explicit
- expose operator-visible job status through API reads
- keep current domain models as the source of truth instead of inventing parallel shadow state

## Product Decision

`CP-019` will use a single Postgres-backed operations queue with a separate worker entrypoint.

This first slice will support:

- `GST_EXPORT_PREPARE`
- `SUPPLIER_REPORT_REFRESH`
- `MAINTENANCE_SWEEP`

This first slice will not support:

- generic DAG or workflow composition
- Redis-backed fan-out workers
- arbitrary user-created scheduled jobs
- external provider IRN delivery
- desktop-local background execution

## Current Context

Store already has:

- durable domain records for GST export jobs and IRN attachments
- durable supplier-report snapshot records with `is_dirty` and `refreshed_at`
- owner-web and store-desktop routes that currently read supplier reports directly
- synchronous request handlers that still create or refresh data inline

Store does not yet have:

- one canonical job queue table
- a worker lease model
- retry or dead-letter state
- operator-visible job status
- retention or maintenance sweeps outside request handlers

## Why Postgres First

The current system already depends on Postgres for all authoritative state. Adding Redis now would widen production infrastructure before `CP-024` and would create two durability systems before the repo has even established its final environment posture.

For this phase, Postgres is sufficient because:

- job volume is low and predictable
- the first job types are branch-scoped and not high-throughput
- queue semantics matter more than raw throughput
- one durable system is easier to reason about and verify

## Operations Queue Boundary

Add a new durable backend domain:

- `operations_jobs`

Each job record should include:

- `id`
- `tenant_id`
- `branch_id`
- `job_type`
- `status`
- `queue_key`
- `payload`
- `result_payload`
- `attempt_count`
- `max_attempts`
- `run_after`
- `leased_until`
- `lease_token`
- `last_error`
- `dead_lettered_at`
- `created_by_user_id`
- `created_at`
- `updated_at`

Recommended statuses:

- `QUEUED`
- `RUNNING`
- `SUCCEEDED`
- `RETRYABLE`
- `DEAD_LETTER`
- `CANCELLED`

## Worker Model

Add a separate worker entrypoint that:

- polls due jobs from Postgres
- leases a small batch atomically
- dispatches to one handler per `job_type`
- marks success, retry, or dead-letter
- performs periodic maintenance sweeps on a configured cadence

The worker does not need a distributed scheduler. A polling loop with deterministic leasing is enough for this phase.

## Job Types

### `GST_EXPORT_PREPARE`

This job prepares a GST export record asynchronously after the owner requests export for a sale.

Request path:

1. API validates actor, branch, and sale existence.
2. API creates or reuses a `GstExportJob` row with status `QUEUED`.
3. API enqueues an `operations_jobs` record for `GST_EXPORT_PREPARE`.
4. Worker computes the HSN summary and export metadata, then sets the export job to `IRN_PENDING`.

Important boundary:

- `attach-irn` remains a direct operator action for now.
- real provider delivery belongs to `CP-020`.

### `SUPPLIER_REPORT_REFRESH`

This job refreshes one supplier-report snapshot asynchronously.

Request path:

- if a snapshot exists and is clean, report routes return it immediately
- if a snapshot exists and is dirty, report routes return the stale snapshot and enqueue a refresh if none is already pending for that scope
- if a snapshot does not exist yet, the first request may still seed it inline as a compatibility bridge for this phase, but subsequent refreshes must be async

The job payload should include:

- `report_type`
- `report_date`
- optional `supplier_id`

The worker refreshes the snapshot payload and marks it clean.

### `MAINTENANCE_SWEEP`

This job performs backend queue maintenance:

- expire abandoned leases
- requeue expired `RUNNING` jobs
- delete or archive completed jobs older than retention
- optionally enqueue supplier-report refreshes for stale dirty snapshots

This is not a user-facing workflow job. It exists so maintenance stops depending on ad-hoc request paths.

## Queue Semantics

### Idempotency

Jobs must dedupe by scope where that matters.

Recommended `queue_key` examples:

- `gst-export:{tenant_id}:{branch_id}:{sale_id}`
- `supplier-report:{tenant_id}:{branch_id}:{report_type}:{report_date or 'none'}:{supplier_id or 'none'}`
- `maintenance:{date-hour-bucket}`

If the same job is already `QUEUED`, `RUNNING`, or `RETRYABLE`, producers should reuse that job rather than enqueueing duplicates.

### Leasing

The worker should lease jobs by:

- selecting due jobs whose `run_after <= now`
- skipping jobs with active `leased_until`
- setting `leased_until` and a random `lease_token`

Completion or retry updates must require the matching `lease_token` so a stale worker cannot overwrite a newer lease owner.

### Retry

Retryable failures should:

- increment `attempt_count`
- record `last_error`
- move to `RETRYABLE`
- set `run_after` with exponential backoff

When `attempt_count >= max_attempts`, the job must become `DEAD_LETTER`.

## API Visibility

Add operations routes so staff with the right capabilities can inspect queue posture.

Recommended branch-scoped routes:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/operations/jobs`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/operations/jobs/{job_id}/retry`

Returned job records should expose:

- id
- job type
- status
- attempt count
- last error
- created at
- updated at
- dead-letter timestamp

Supplier-report routes should also expose whether the returned snapshot is:

- `current`
- `stale_refresh_queued`
- `stale_refresh_running`

This metadata should be additive so existing consumers can adapt incrementally.

## UI Impact

### Owner Compliance

The owner compliance section should:

- show queued or preparing export jobs
- continue to list the export queue
- allow IRN attachment only once the job is `IRN_PENDING`

### Owner Supplier Reporting

The owner supplier reporting section should:

- show when snapshots are stale and a refresh is queued
- keep rendering the last available payload when stale
- avoid implying the current response was recomputed inline

No store-desktop UI changes are required in this slice unless shared types force compatibility adjustments.

## Settings

Add worker settings for:

- poll interval
- lease seconds
- default max attempts
- retry base seconds
- maintenance interval seconds
- completed-job retention days

These should live in the existing control-plane settings module and be configurable through environment variables.

## Testing Strategy

### Backend queue tests

- enqueue dedupes by queue key
- lease skips already leased jobs
- stale lease becomes available again
- retry moves job to `RETRYABLE`
- max attempts move job to `DEAD_LETTER`

### Compliance async tests

- create export enqueues queue work and returns a queued export job
- worker processing moves the export job to `IRN_PENDING`
- duplicate export requests reuse the queued job instead of enqueueing another

### Supplier report async tests

- first snapshot can still seed inline when absent
- dirty snapshot returns stale payload and enqueues refresh
- worker refresh clears `is_dirty` and updates `refreshed_at`
- duplicate refresh requests reuse the queued job

### Maintenance tests

- completed jobs older than retention are cleaned
- expired leases are requeued

## Exit Criteria

`CP-019` is complete when:

- GST export preparation is queue-backed
- supplier-report refresh is queue-backed after the initial seed
- a worker process can lease and execute jobs from Postgres
- retries and dead-letter state are durable
- operator-visible job status exists through API routes
- maintenance no longer depends on ad-hoc inline request execution
