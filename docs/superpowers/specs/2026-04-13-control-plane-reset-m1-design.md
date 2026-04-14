# Control-Plane Reset Milestone 1 Design

Date: 2026-04-13
Status: Approved in terminal

## 1. Goal

Reset the Store architecture by building a side-by-side enterprise control plane instead of continuing to grow the current oversized legacy API.

Milestone 1 delivers only the control-plane foundation:

- platform admin onboarding
- tenant creation
- owner invite or binding
- first-branch setup
- membership and RBAC foundation
- audit foundation
- Postgres and Alembic setup
- Korsenex IDP-backed actor resolution

Milestone 1 explicitly does not migrate retail business domains yet.

## 2. Why a Side-by-Side Reset

The current legacy retail API already contains a broad Wave 1 domain model, but its entrypoint shape and module boundaries are not acceptable as the foundation for a public-market enterprise product.

The reset will be built in parallel because:

- in-place rewrite would entangle onboarding reset work with retail-domain regression risk
- compatibility-preserving refactor would keep too much of the current oversized structure alive
- side-by-side delivery gives a clean cutover line between new control-plane ownership and legacy retail-domain ownership

## 3. Milestone 1 System Boundary

### New Ownership

Milestone 1 introduces:

- `services/control-plane-api/`
- control-plane routes for auth resolution, tenant creation, branch setup, memberships, and audit
- API-driven onboarding flows in `apps/platform-admin/` and `apps/owner-web/`

### Deferred Ownership

Milestone 1 does not migrate:

- purchasing
- inventory
- billing
- GST
- barcode
- print
- sync
- offline runtime continuity

Those remain in the current legacy retail API temporarily.

## 4. Authentication and Authorization Posture

### Authentication Authority

Korsenex IDP is the authentication authority.

Store will not build a second long-term identity source for owner and admin access.

The control plane should rely on Korsenex-authenticated identity and then enforce Store-local authorization.

### Store-Control Authorization Ownership

Store owns:

- tenants
- branches
- tenant memberships
- branch memberships
- RBAC role definitions and capability mapping
- control-plane audit events

### Runtime Convenience Rule

Later runtime conveniences such as branch PIN or device unlock may exist, but they are layered on top of the real identity model and do not replace it.

## 5. Data Model

Recommended Milestone 1 core tables:

- `tenants`
- `branches`
- `tenant_memberships`
- `branch_memberships`
- `role_definitions`
- `role_capabilities`
- `owner_invites`
- `audit_events`

Optional identity-link table only if required by integration shape:

- `external_identity_links`

The control plane should not own password storage as a primary auth system for owner and admin access.

## 6. Backend Architecture

Milestone 1 backend layout:

- `services/control-plane-api/`
  - `store_control_plane/`
    - `config/`
    - `db/`
    - `models/`
    - `repositories/`
    - `services/`
    - `schemas/`
    - `dependencies/`
    - `routes/`

Entrypoints must stay thin. No new mixed-responsibility `main.py` is acceptable.

## 7. API Surface

Recommended canonical Milestone 1 routes:

- `POST /v1/auth/oidc/exchange`
- `GET /v1/auth/me`
- `POST /v1/platform/tenants`
- `GET /v1/platform/tenants`
- `POST /v1/platform/tenants/{tenant_id}/owner-invites`
- `GET /v1/tenants/{tenant_id}`
- `POST /v1/tenants/{tenant_id}/branches`
- `GET /v1/tenants/{tenant_id}/branches`
- `POST /v1/tenants/{tenant_id}/memberships`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/memberships`
- `GET /v1/tenants/{tenant_id}/audit-events`

Legacy retail contracts are intentionally excluded from this milestone.

## 8. App Surfaces

### Platform Admin

Milestone 1 replaces the static shell with:

- tenant list
- create tenant
- onboarding state visibility
- owner invite or binding controls

### Owner Web

Milestone 1 replaces the static onboarding shell with:

- current actor context from `/v1/auth/me`
- create first branch
- list branches
- assign initial memberships

## 9. Docs and Governance

Milestone 1 begins by establishing canonical repo docs:

- `docs/DOCS_INDEX.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/STORE_CANONICAL_BLUEPRINT.md`
- `docs/API_CONTRACT_MATRIX.md`
- `docs/TASK_LEDGER.md`
- `docs/WORKLOG.md`
- `docs/HANDOFF_TEMPLATE.md`
- `docs/context/MODULE_MAP.md`
- `docs/runbooks/dev-workflow.md`

This is required so architecture and reset work stop living only in chat history.

## 10. Delivery Tracks

### Track A: Docs and Governance

- create docs spine
- record reset program
- update blueprint and context

### Track B: New Control-Plane Backend

- create new service
- add Postgres + Alembic
- add modular routes, services, and repositories
- add Korsenex IDP integration boundary

### Track C: Platform Admin Flow

- create tenant
- list tenants
- invite or bind owner

### Track D: Owner Web Flow

- resolve current actor
- create first branch
- assign initial memberships

### Track E: Verification

- backend service tests
- onboarding integration tests
- platform-admin and owner-web onboarding smoke coverage

## 11. Exit Criteria

Milestone 1 is complete when:

- docs spine exists and is in use
- the control-plane service runs independently
- Postgres and Alembic are wired
- Korsenex IDP-backed actor resolution works
- platform admin can create tenant
- tenant owner can complete first-branch setup
- memberships and audit events are persisted
- legacy retail API remains untouched except for later integration seams

## 12. Deferred Work

The following remain for later milestones:

- catalog
- staff and device runtime depth
- purchasing and inventory migration
- billing and GST migration
- print and sync runtime migration
- full legacy retail API cutover
