# GST IRP Integration Design

## Context

`CP-020` replaces the current compliance placeholder flow in the control plane. Today the backend can queue a GST export job and the owner web can manually attach an IRN, but there is no real provider-backed submission path, no branch-scoped provider credential model, and no explicit operator retry or failure posture suitable for a public multi-tenant release.

The current sales model already provides the invoice tax totals, HSN-linked line items, and B2B-vs-B2C posture. What it does not provide is a durable provider integration boundary. Branch records only carry GSTIN, and sales only carry customer name plus GSTIN. To keep the task bounded without inventing a second customer master, the compliance integration will derive taxpayer legal and address details from the provider’s GSTIN details API for both seller and buyer GSTINs.

## External Constraints

- IRIS IRP core APIs require taxpayer authorization, auth-token based access, and solution-provider client credentials.
- IRIS IRP validation guidance says the core auth token is valid for 6 hours, duplicate IRN requests must be handled without re-registering the same document, and auth payloads require provider public-key encryption for password and app key exchange.
- IRIS IRP’s core API catalogue includes Authentication, Generate IRN, Get IRN by Document Details, and Get GSTIN Details.
- IRIS IRP announced that, effective April 1, 2025, taxpayers with AATO of Rs.10 crore and above cannot report invoices older than 30 days.

Primary sources used for this design:
- IRIS IRP Core APIs wiki: <https://einvoice6.gst.gov.in/content/core-apis-wiki/>
- IRIS IRP validation rules: <https://einvoice6.gst.gov.in/content/validation-rules/>
- IRIS IRP user onboarding and API onboarding overview: <https://einvoice6.gst.gov.in/content/kb/user-onboarding/>
- IRIS IRP production advisory for the 30-day restriction: <https://einvoice6.gst.gov.in/content/revised-time-limit-for-e-invoice-reporting-for-businesses-with-aato-of-%E2%82%B910-crores-above/>

## Chosen Approach

Use a branch-scoped provider profile plus a provider adapter boundary, with one concrete IRIS-direct adapter now and a stub adapter for tests.

The control plane will keep global solution-provider client credentials in environment settings and persist branch-specific taxpayer IRP credentials in encrypted form. GST export jobs will be prepared and submitted asynchronously by the existing operations worker. The worker will resolve seller and buyer taxpayer details by GSTIN through the provider adapter, build a real IRN payload, submit it, and either:

- attach the returned IRN data on success,
- recover an already-generated IRN via document lookup for duplicate requests, or
- move the job into explicit operator-action posture with provider error details.

This keeps the provider lane real without hard-coding one tenant’s credentials or blocking request paths on remote provider I/O.

## Scope

Included in `CP-020`:

- Branch-scoped IRP credential storage with encrypted-at-rest taxpayer password.
- Global provider settings for solution-provider credentials and endpoint URLs.
- A provider adapter boundary with:
  - `disabled`
  - `stub`
  - `iris_direct`
- Async worker submission for GST export jobs.
- Prepared IRN payload persistence on the export job.
- Success, duplicate, retryable, and action-required compliance statuses.
- Owner-web visibility for provider readiness, submission status, provider errors, and retry.
- Explicit retry route for failed or action-required GST export jobs.

Out of scope for this slice:

- Full IRP onboarding APIs from inside Store.
- Credit-note or debit-note IRN generation.
- E-way bill generation or cancellation.
- Rich customer master maintenance for B2B compliance addresses.
- Multi-provider failover beyond one concrete adapter.

## Architecture

### 1. Branch IRP Profile

Add a new branch-scoped compliance profile model:

- `tenant_id`
- `branch_id`
- `provider_name`
- `api_username`
- `encrypted_api_password`
- `status`
- `last_validated_at`
- `last_error_message`

The GSTIN remains on the branch record and is the seller GSTIN for provider calls. The password is encrypted with an application master key from settings. The API username is not treated as secret and may be returned to the UI. The API password is never returned after write.

### 2. Provider Settings

Add application settings for the global solution-provider posture:

- provider mode
- client id
- client secret
- auth URL
- generate IRN URL
- get-by-document URL
- GSTIN-details URL
- provider public key PEM
- HTTP timeout
- encryption master key for branch password storage

The URLs are configured explicitly so the repo does not guess provider endpoints from incomplete public docs. Production deploys can point the same code to sandbox or production endpoints safely.

### 3. Provider Adapter Boundary

Introduce a small provider interface:

- `lookup_taxpayer(gstin)`
- `submit_irn(request)`
- `get_irn_by_document(document_number, document_type, document_date)`

`StubIrpProvider` returns deterministic data for tests.

`IrisDirectIrpProvider`:

- authenticates with solution-provider credentials plus the branch’s taxpayer credentials,
- caches the auth token in-process until expiry,
- encrypts auth inputs with the configured provider public key,
- calls GSTIN details lookup for seller and buyer,
- posts the generate-IRN payload,
- maps provider success and failure responses into internal result objects.

The adapter will normalize multiple likely provider field names where the public docs are descriptive but not strongly typed.

### 4. GST Export Job Lifecycle

Extend `GstExportJob` with:

- `provider_name`
- `provider_status`
- `prepared_payload`
- `submission_attempt_count`
- `last_submitted_at`
- `last_error_code`
- `last_error_message`

Revised statuses:

- `QUEUED`
- `PREPARING`
- `READY`
- `SUBMITTING`
- `IRN_ATTACHED`
- `ACTION_REQUIRED`
- `RETRY_QUEUED`

`ACTION_REQUIRED` is used for provider-business failures that need operator intervention, such as invalid GSTIN data or missing branch credentials. Transient HTTP or auth outages remain worker-retry failures at the operations-job level.

### 5. Payload Preparation

The worker prepares a single domestic B2B invoice payload using current repo boundaries:

- seller GSTIN from the branch
- buyer GSTIN from the sale
- seller and buyer legal or trade details resolved via GSTIN lookup
- place of supply derived from buyer GSTIN state code
- line descriptions from catalog product name
- HSN from catalog product
- UQC defaulted to `NOS`
- tax values from the persisted sale or invoice totals
- document details from the sales invoice

If the sale is not B2B, has no buyer GSTIN, or lacks a branch GSTIN, the job moves to `ACTION_REQUIRED` with a clear reason.

### 6. Submission and Duplicate Recovery

Submission flow:

1. Load or prepare the payload.
2. Submit to provider.
3. On success:
   - persist IRN attachment
   - update sale `irn_status`
   - mark job `IRN_ATTACHED`
4. On duplicate-document result:
   - fetch existing IRN via document lookup
   - persist attachment
   - mark job `IRN_ATTACHED`
5. On provider validation or configuration errors:
   - mark job `ACTION_REQUIRED`
   - persist provider error code and message
6. On transient transport or auth issues:
   - raise for worker retry

### 7. Operator Surface

Owner web gets one coherent compliance surface:

- branch provider profile form:
  - provider
  - API username
  - API password set or rotate
  - readiness badge
- GST export queue:
  - invoice
  - status
  - provider status
  - last error
  - IRN or ack when attached
- actions:
  - queue export
  - retry failed submission
  - refresh queue

The manual IRN attach UI is removed. Operator posture becomes real submission state, not simulated success entry.

## Error Handling

Terminal business or configuration failures are not hidden inside generic worker dead letters. They become compliance-job `ACTION_REQUIRED` records visible to operators. Examples:

- missing branch provider profile
- sale missing buyer GSTIN
- provider rejects invoice validation
- provider rejects stale invoice based on its reporting window rules

Transient failures continue to use the operations queue retry and dead-letter posture:

- network timeout
- provider 5xx
- token acquisition outage

## Security

- Branch taxpayer passwords are encrypted at rest with an application master key.
- Global solution-provider client credentials remain in environment settings only.
- The UI never reads back the taxpayer password.
- Provider errors are stored as operator-visible text, but raw credentials are never logged or persisted in audit payloads.

## Testing Strategy

Backend:

- branch provider profile create and read behavior
- encryption and decryption round-trip
- GST export worker success with stub provider
- duplicate-document recovery path
- action-required posture for missing configuration and invalid business inputs
- retry route re-enqueues eligible jobs

Owner web:

- profile save flow
- queue rendering for real provider statuses
- retry action for failed jobs
- removal of manual IRN attach controls

Verification:

- targeted backend suite for compliance and worker behavior
- owner-web tests for the compliance section
- full backend test suite to ensure the new provider and settings paths do not regress existing flows

## Rollout Notes

- Production environments must configure the global provider URLs, solution-provider credentials, provider public key, and secret-encryption key before enabling `iris_direct`.
- Existing queued jobs created before this migration can be retried through the new queue path after a branch provider profile is configured.
