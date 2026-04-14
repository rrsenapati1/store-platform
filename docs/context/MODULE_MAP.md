# Store Module Map

Updated: 2026-04-14

## Current Runtime Topology

### Legacy Retail API

- `services/api/store_api/`
  - current retail domain surface
  - broad route and domain coverage
  - oversized entrypoint and mixed-responsibility layout

### Current Apps

- `apps/platform-admin/`
  - current platform shell
- `apps/owner-web/`
  - current owner shell
- `apps/store-desktop/`
  - API-driven runtime checkout shell on the new control plane
  - cache-only runtime continuity boundary through a dedicated local adapter
- `apps/store-desktop/src-tauri/`
  - native packaged shell for store-desktop
  - SQLite-backed runtime-cache bridge through Tauri commands
  - packaged-runtime-only persistence, still non-authoritative

## Target Milestone 1 Topology

### New Control Plane

- `services/control-plane-api/`
  - enterprise control-plane backend

Implemented internal layout:

- `config/`
- `db/`
- `models/`
- `repositories/`
- `services/`
- `schemas/`
- `dependencies/`
- `routes/`
- `alembic/`

Current route ownership:

- `routes/auth.py`
  - OIDC exchange
  - current actor resolution
- `routes/system.py`
  - authority-boundary manifest
  - cutover contract publication
- `routes/platform.py`
  - platform tenant creation and listing
  - owner invite dispatch
- `routes/tenants.py`
  - tenant summary
  - branch creation and listing
  - tenant and branch membership assignment
  - tenant audit feed
- `routes/workforce.py`
  - staff profile create and list
  - branch device registration and list
  - packaged runtime claim list and approval
- `routes/catalog.py`
  - central catalog product create and list
  - branch catalog assignment create and list
- `routes/barcode.py`
  - catalog barcode allocation
  - branch scan lookup
  - branch barcode label preview
- `routes/purchasing.py`
  - supplier master create and list
  - purchase-order create and list
  - purchase-order approval submission and approval
  - purchase approval report
- `routes/inventory.py`
  - approved purchase-order receipt creation
  - receiving board
  - goods-receipt list
  - stock adjustment posting
  - stock count posting
  - branch transfer creation
  - transfer board
  - inventory ledger list
  - inventory snapshot list
- `routes/batches.py`
  - goods-receipt batch-lot intake
  - branch batch-expiry report
  - expiry write-off posting
- `routes/procurement_finance.py`
  - purchase-invoice creation and list
  - supplier-return creation
  - supplier-payment creation
  - supplier payables report
- `routes/billing.py`
  - branch sale creation
  - GST invoice generation
  - branch sale return creation
  - sale-return register reads
  - owner refund approval
  - branch sales register reads
- `routes/customers.py`
  - tenant customer directory reads
  - customer sales/returns/exchanges history reads
  - branch customer report reads
- `routes/compliance.py`
  - GST export job creation
  - GST export queue reads
  - IRN attachment posting
- `routes/exchanges.py`
  - cashier exchange creation
  - exchange settlement orchestration boundary
- `routes/runtime.py`
  - runtime device list
  - packaged runtime device-claim resolve
  - runtime device heartbeat
  - invoice print-job queue
  - credit-note print-job queue
  - device print-job list and completion

### New App Responsibilities

- `apps/platform-admin/`
  - live control-plane session bootstrap
  - tenant creation
  - onboarding status list
  - owner invite posture
- `apps/owner-web/`
  - live owner session bootstrap
  - current actor context
  - first-branch setup
  - initial membership assignment
  - onboarding audit visibility
  - catalog barcode allocation and label preview
  - batch lot intake and expiry write-off control
  - supplier billing and settlement visibility
  - refund approval posture
  - GST export queue and IRN attachment posture
  - customer directory and branch customer insights visibility
- `apps/store-desktop/`
  - live cashier session bootstrap
  - branch catalog-backed checkout
  - branch barcode scan lookup
  - branch batch expiry visibility and write-off handoff
  - GST invoice creation
  - runtime device heartbeat
  - invoice and credit-note print queue actions
  - customer sale returns
  - customer exchanges
  - branch customer insights visibility
  - sales register visibility
  - inventory snapshot refresh after sale
  - cache hydration before live control-plane refresh
  - cache status visibility and local-authority guardrails

- `apps/store-desktop/src/runtime-cache/`
  - cache snapshot contract for runtime continuity
  - browser-storage fallback adapter for the current web shell
  - native SQLite adapter selection for the packaged runtime
  - resolver that chooses packaged-native or web fallback without changing authority semantics

Current supporting service ownership:

- `services/idp.py`
  - Korsenex JWKS validation
  - stub identity fallback for tests
- `services/auth.py`
  - actor session issuance
  - actor context resolution
- `services/onboarding.py`
  - tenant, branch, membership, and audit orchestration
- `services/workforce.py`
  - staff directory orchestration
  - branch device registration orchestration
  - packaged runtime device-claim orchestration
- `services/catalog.py`
  - central catalog orchestration
  - branch catalog assignment orchestration
- `services/barcode.py`
  - catalog barcode allocation orchestration
  - branch scan lookup orchestration
  - branch label-preview orchestration
- `services/barcode_policy.py`
  - barcode normalization
  - tenant/SKU barcode allocation rules
  - barcode label payload derivation
- `services/purchasing.py`
  - supplier orchestration
  - purchase-order orchestration
  - approval-report orchestration
- `services/inventory.py`
  - approved purchase-order receipt orchestration
  - goods-receipt read models
  - stock adjustment, count, and transfer orchestration
  - append-only inventory ledger orchestration
  - inventory snapshot derivation
- `services/batches.py`
  - goods-receipt batch-lot intake orchestration
  - branch batch-expiry report derivation
  - expiry write-off orchestration
- `services/batches_policy.py`
  - goods-receipt batch-intake validation
  - batch expiry-report derivation
  - expiry write-off quantity guardrails
- `services/procurement_finance.py`
  - purchase-invoice orchestration
  - supplier-return orchestration
  - supplier-payment orchestration
  - supplier-payables read model
- `services/procurement_finance_policy.py`
  - purchase-invoice numbering
  - supplier credit-note numbering
  - supplier payment numbering
  - payable outstanding and duplication guardrails
- `services/billing.py`
  - branch sales orchestration
  - GST invoice and tax-line derivation
  - payment attachment
  - sale-return orchestration
  - credit-note derivation
  - exchange orchestration
  - owner refund approval orchestration
  - sales register read model
- `services/customer_reporting.py`
  - customer directory derivation
  - customer history read model
  - branch customer report derivation
- `services/compliance.py`
  - GST export job orchestration
  - IRN attachment orchestration
  - compliance queue read model
- `services/compliance_policy.py`
  - GST export eligibility guardrails
  - IRN attachment duplication guardrails
  - HSN or SAC export-summary derivation
- `services/exchange_policy.py`
  - exchange credit allocation
  - balance direction derivation
  - settlement payment split rules
- `services/runtime.py`
  - runtime device liveness orchestration
  - invoice and credit-note print payload derivation
  - branch print-queue ownership and completion
- `services/authority.py`
  - control-plane authority-boundary manifest builder
  - migrated-domain and legacy-domain cutover contract
- `store_control_plane/verification.py`
  - reusable control-plane smoke path for Postgres-backed verification
  - platform-admin, owner, cashier, runtime heartbeat, and print queue integration coverage
- `services/control-plane-api/scripts/verify_control_plane.py`
  - runbook-grade verification entrypoint
  - Alembic, backend pytest, app-flow tests, typecheck/build, and smoke orchestration
- `apps/store-desktop/src/runtime-cache/storeRuntimeCache.ts`
  - runtime-cache adapter resolver
  - packaged-native vs browser fallback selection
  - no token or backend-authority persistence
- `apps/store-desktop/src/runtime-shell/storeRuntimeShell.ts`
  - runtime-shell adapter resolver
  - packaged-native vs browser fallback shell-status selection
  - no backend-authority or device-registration mutation ownership
- `apps/store-desktop/src/control-plane/runtimeOutbox.ts`
  - replay-safe local runtime outbox builders
  - queueable-failure classification and replay orchestration for runtime heartbeats and print requests
- `apps/store-desktop/src/control-plane/StoreRuntimeOutboxSection.tsx`
  - queued runtime action visibility for branch staff
  - explicit replay trigger from a live runtime session
- `apps/store-desktop/src-tauri/src/runtime_cache.rs`
  - SQLite persistence for `store.runtime-cache.v1`
  - malformed-snapshot cleanup
  - packaged-runtime cache status, save, load, and clear commands
- `apps/store-desktop/src-tauri/src/runtime_shell.rs`
  - packaged-runtime shell identity and host metadata
  - stable installation fingerprint persistence
  - packaged-runtime claim-code derivation
  - read-only native shell-status command for the webview
- `apps/store-desktop/src-tauri/src/runtime_paths.rs`
  - packaged-runtime home and cache-db path resolution
  - runtime hostname lookup and shared directory creation helpers

## Deferred Until Later Milestones

- sync ownership beyond cache hydration, replay-safe runtime outbox continuity, and authoritative refresh
- broader store-desktop runtime migration beyond checkout, returns, exchanges, and print polling
- deeper native hardware and packaged-distribution hardening beyond the initial Tauri shell, shell-identity foundation, and runtime outbox continuity
- final retirement of the legacy retail API after operator cutover validation and residual read replacement
