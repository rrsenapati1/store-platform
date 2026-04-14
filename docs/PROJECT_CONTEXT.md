# Store Project Context

Updated: 2026-04-15

## Product Intent

Store is a multi-tenant retail platform for public-market deployment. The active target is now a broader `V2 launch` for an enterprise physical-retail suite: India-first operational depth, GST-compliant billing, branch-aware inventory, offline-capable runtime surfaces, richer retail hardware, and modern in-store commercial/management capabilities.

## Current Repo Reality

- `services/api/store_api/` is the current legacy retail API.
- The legacy API already models a broad Wave 1 retail domain, but its entrypoint is oversized and not acceptable as the long-term architecture.
- `apps/platform-admin/`, `apps/owner-web/`, and `apps/store-desktop/` exist, but the current app shells are still early-stage surfaces rather than the final enterprise control plane and runtime product.

## Reset Direction

The repo is moving to a side-by-side enterprise reset instead of continued incremental growth on the legacy API.

Milestone 1 introduces a new control plane in parallel to the legacy retail API:

- `services/control-plane-api/`
  - tenant onboarding
  - branch setup
  - RBAC membership foundation
  - audit foundation
  - Korsenex IDP-backed actor resolution through JWKS validation
- `apps/platform-admin/`
  - platform-admin onboarding and tenant controls
- `apps/owner-web/`
  - owner onboarding, first-branch setup, and initial membership flows

The legacy retail API remains temporarily in place until later milestones migrate business domains onto the new foundation.

## Active Launch Target

The repo no longer targets the smaller desktop-first public-release endgame as the final product boundary. The active launch target is now the `V2 launch` program for a broader physical-retail suite.

V2 launch includes:

- packaged Store Desktop as branch hub and desktop spoke foundation
- mobile store app, starting with an Android-first Kotlin handheld and inventory-tablet spoke slice
- inventory tablet workflows
- customer display
- camera barcode scanning and richer device-input support
- advanced hardware such as cash drawer, weighing scale, and payment terminal integration
- CRM/loyalty/promotions/gift/store credit and multi-price retail controls
- staff/shift/cashier governance and richer operator controls
- advanced reporting, dashboards, and decision-support capabilities
- regulated/vertical retail extensions such as pharmacy/prescription and serial-number/IMEI tracking

`Omnichannel` scope is explicitly deferred until after V2 launch. That means no e-commerce storefronts, online ordering, marketplace sync, customer app, or delivery orchestration on the current launch critical path.

## Authentication Authority

Store will not become its own long-term identity provider.

- Korsenex IDP is the authentication authority.
- Store control plane owns tenancy, branch scope, app-specific authorization, and audit.
- `stub` token mode exists only for tests and isolated development fallback.
- Branch-local fast-login patterns may exist later as runtime conveniences, but not as the system-of-record identity model.

## Delivery Program

The reset remains the foundation, but the active program endgame has changed.

Completed foundation program:

1. Milestone 1: control plane, onboarding, Postgres, migrations, auth integration
2. Milestone 2: catalog, staff, devices, and assignment foundations
3. Milestone 3: purchasing and inventory ledger migration
4. Milestone 4: billing, GST, print, sync, runtime migration
5. Milestone 5: reporting, compliance jobs, enterprise hardening

Active expansion program:

- V2 runtime/device expansion
- V2 store operations depth
- V2 customer/commercial features
- V2 staff/branch controls
- V2 reporting/decision support
- V2 vertical extensions
- V2 hardening/scale and final launch readiness

Milestone 2 now includes:

- control-plane-owned staff directory reads
- branch device registration
- central catalog product authority
- branch catalog assignment foundations
- live owner-web management for those three surfaces

Milestone 3 now includes:

- supplier master authority
- control-plane purchase-order creation
- branch purchase approval reporting
- approved purchase-order receipt foundations
- branch goods-receipt visibility
- append-only purchase-receipt inventory ledger foundations
- derived branch inventory snapshot reads
- stock adjustment foundations
- stock count foundations
- branch transfer foundations
- transfer-board visibility
- control-plane purchase invoice creation
- supplier return credit-note generation
- supplier payment recording
- supplier payables reporting

Milestone 4 has now started with:

- control-plane-owned branch sales
- GST invoice numbering and tax-line generation
- branch `SALE` ledger posting
- first API-driven `apps/store-desktop/` checkout flow against the new control plane
- control-plane-owned sale returns
- control-plane credit-note generation
- owner refund approval on the new backend
- branch `CUSTOMER_RETURN` ledger posting through the same inventory authority
- cashier exchange creation with replacement sale generation
- exchange credit allocation and exchange-order persistence on the new backend
- runtime device heartbeat on the new backend
- invoice and credit-note print-job ownership on the new backend
- store-desktop cache-only runtime continuity with explicit non-authoritative local persistence

The runtime continuity boundary is now explicit:

- branch-local persistence is cache-only
- control-plane Postgres remains authoritative
- the current web runtime uses a dedicated cache adapter with browser storage fallback
- the packaged desktop runtime now has a native Tauri shell with a SQLite-backed cache bridge under the same non-authoritative contract
- the packaged desktop runtime now also exposes read-only shell identity and host-health posture through a dedicated native bridge so packaged-vs-browser runtime facts stay visible without introducing local authority
- the packaged desktop runtime now uses an approved claim-and-bind flow:
  - packaged shells start unbound
  - they present a stable installation fingerprint and short claim code
  - owners approve that claim into a real branch device record
  - store-desktop auto-binds only after approval instead of trusting the first branch device
- the runtime shell now also has a replay-safe local outbox for non-authoritative runtime actions:
  - degraded heartbeats and invoice or credit-note print requests can be queued locally
  - queued runtime actions stay inside the runtime cache boundary
  - replay happens only against a live control-plane session and never grants local business authority

After the completed CP foundation and public-release tasks, the remaining runtime work now belongs to the V2 launch program:

- mobile store app runtime
  - Android/Kotlin first slices now exist with handheld and inventory-tablet spoke modes, pairing, scan/lookup, receiving, stock count, expiry, and runtime-status foundations
- inventory tablet runtime
- customer display runtime
- richer scanner/camera input
- broader retail hardware integration
- deeper branch/operator workflow polish and resilience

The current cutover contract is now explicit:

- the control plane is authoritative for onboarding, workforce, catalog, purchasing, procurement finance, inventory, billing, and runtime print
- the legacy retail API can run in `shadow` or `cutover` mode for those migrated writes
- the control plane is now also authoritative for barcode foundation flows:
  - catalog barcode allocation
  - branch scan lookup
  - branch label preview
- the control plane is now also authoritative for batch tracking flows:
  - goods-receipt batch-lot intake
  - branch batch expiry reporting
  - expiry write-off posting
- the control plane is now also authoritative for compliance export flows:
  - sales invoice GST export job creation
  - branch GST export queue reads
  - IRN attachment posting
- the control plane is now also authoritative for customer reporting flows:
  - tenant customer directory reads
  - customer history reads
  - branch customer report reads
- the control plane is now also authoritative for barcode print runtime flows:
  - barcode label queueing onto active runtime devices

## Post-V2 Future Work

The following are intentionally outside the active V2 launch boundary:

- omnichannel commerce
- e-commerce storefronts
- online ordering
- marketplace sync
- customer app/mobile commerce
- delivery orchestration
