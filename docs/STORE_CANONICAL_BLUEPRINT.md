# Store Canonical Blueprint

Updated: 2026-04-14

## North Star

Store must look and behave like an enterprise retail suite, not a single-service prototype. The architecture should preserve clean service boundaries, durable data ownership, and explicit identity authority from the start.

## Architectural Principles

1. Authentication is external.
   - Korsenex IDP is the source of truth for user identity and login.
   - Store services validate Korsenex JWTs through JWKS and enforce product-specific authorization.
   - Stub identity mode is allowed only for tests and isolated local fallback.
2. Authorization is local to Store.
   - Tenant membership, branch membership, role mapping, and capability checks live in Store.
3. Tenancy is explicit.
   - Every control-plane write is tenant-scoped or platform-scoped by design.
4. Branch scope is explicit.
   - Branch-level access is modeled, not inferred from ad hoc request fields.
5. Legacy retail flows are temporary.
   - The current `services/api/store_api/` remains only until the new control plane and later domain migrations replace it.
6. New code must be modular.
   - Oversized mixed-responsibility files are not acceptable.
   - Entrypoints must stay thin and orchestration-focused.
7. Postgres is the backend system of record.
   - SQLite is acceptable only for branch-local runtime caches, never for backend authority.
   - The web shell may use browser storage fallback, and the packaged desktop shell may use native SQLite, but both must preserve the same non-authoritative cache contract.

## Milestone 1 System Boundary

Milestone 1 introduces a new side-by-side control plane:

- `services/control-plane-api/`
  - new enterprise control-plane backend
- `apps/platform-admin/`
  - platform-admin onboarding and tenant controls
- `apps/owner-web/`
  - owner onboarding and first-branch setup

Milestone 1 owns:

- platform admin actor resolution
- tenant creation
- owner invite or binding flow
- branch creation
- tenant-level and branch-level memberships
- RBAC role and capability foundation
- audit events
- Postgres and Alembic foundation

Milestone 1 does not yet own:

- purchasing
- inventory
- billing
- print jobs
- sync or runtime continuity

Milestone 2 is now complete for:

- staff profiles
- membership-linked staff directory reads
- branch device registration foundations
- central catalog product foundations
- branch catalog assignment foundations

Milestone 3 is now complete for:

- supplier master foundations
- purchase-order creation foundations
- purchase-order approval-report foundations
- approved purchase-order receipt foundations
- goods-receipt read models
- append-only inventory ledger foundations
- derived inventory snapshot reads
- stock adjustment foundations
- stock count foundations
- branch transfer foundations
- transfer-board visibility
- purchase-invoice generation from goods receipts
- supplier return credit-note generation
- supplier payment recording
- supplier payables reporting

Milestone 4 has started by extending the control plane into:

- branch sales
- GST invoice numbering and tax-line derivation
- payment attachment on checkout
- append-only `SALE` inventory ledger posting
- first cashier-facing store runtime checkout flow
- sale returns
- credit-note numbering and tax-line derivation
- owner refund approval
- append-only `CUSTOMER_RETURN` inventory ledger posting
- cashier exchanges
- replacement sale generation with exchange credit allocation
- persisted exchange orders on the new backend
- runtime device heartbeat
- invoice and credit-note print-job ownership on the new backend
- cache-only runtime continuity behind a dedicated local adapter boundary
- barcode foundation flows:
  - catalog barcode allocation
  - branch scan lookup
  - branch label preview
- batch tracking flows:
  - goods-receipt batch-lot intake
  - branch batch expiry reporting
  - expiry write-off inventory-ledger posting
- compliance export flows:
  - sales invoice GST export job creation
  - branch GST export queue visibility
  - IRN attachment posting and sale IRN-state updates
- customer reporting flows:
  - tenant customer directory visibility
  - customer sales/returns/exchanges history visibility
  - branch customer report visibility

The remaining runtime rule is explicit:

- local persistence may improve operator continuity
- local persistence may not become the system of record
- cache hydration must be followed by authoritative control-plane refresh
- native SQLite belongs behind the runtime-cache boundary inside the packaged desktop shell, not inside backend services
- packaged shell identity and host-health metadata may be exposed read-only to the webview, but that visibility does not grant local authority or replace device registration on the control plane
- packaged desktop device binding must use an approved claim-and-bind flow from the control plane, not blind self-registration or first-device auto-selection
- replay-safe local outboxes are allowed only for non-authoritative runtime actions such as heartbeats and print requests; business writes like sales, returns, exchanges, stock movement, and invoice authority remain control-plane-only

## Data Ownership

- Korsenex IDP:
  - global identity
  - sign-in
  - token issuance
- Store control plane:
  - tenants
  - branches
  - memberships
  - RBAC mapping
  - control-plane audit
- Legacy retail API:
  - temporary domain authority until migrated
  - once a migrated domain enters legacy `cutover` mode, the legacy service is no longer allowed to accept writes for that domain

## Code Organization Standard

New backend code should follow this shape:

- `config/`
- `db/`
- `models/`
- `repositories/`
- `services/`
- `schemas/`
- `dependencies/`
- `routes/`

No new mixed-responsibility `main.py` files are acceptable.

## Legacy Cutover Rule

- The control plane publishes the current authority contract at `GET /v1/system/authority-boundary`.
- The legacy retail API must emit deprecation headers for migrated domains while in `shadow` mode.
- The legacy retail API must reject migrated-domain writes while in `cutover` mode.
- The operational authority list is fully migrated; no legacy-only operational domains remain on the retail API.
- Barcode foundation, barcode label-print runtime, batch tracking, compliance export, customer reporting, supplier reporting, and hub sync-runtime orchestration are all migrated onto the control plane.
