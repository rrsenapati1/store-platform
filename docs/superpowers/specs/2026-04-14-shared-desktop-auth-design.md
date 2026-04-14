# Shared Desktop Auth Design

Date: 2026-04-14
Status: Approved in terminal

## 1. Goal

Define one shared desktop-auth model for RMS and Store that:

- keeps browser control-plane access owner-only for now
- preserves Korsenex IDP as the real web authentication authority
- allows approved branch devices to support fast staff desktop unlock without requiring full staff IDP login
- avoids PIN-only first trust
- fixes the current RMS auth gaps before Store ports the same model

This design covers:

- auth trust boundaries
- owner, staff, and device roles
- device approval and staff activation flows
- local PIN re-entry rules
- token and storage posture
- RMS hardening scope
- Store port sequence

## 2. Product Decision

The shared model will use:

- owner-approved device claim and bind
- owner-issued one-time staff activation for a specific approved device
- local PIN re-entry only after that first online activation

The design will not use:

- staff PIN login on web
- pure PIN-only first bootstrap
- branch staff full IDP login as the default desktop flow

This matches the product direction that owner web is the browser control plane while branch staff use desktop runtime surfaces.

## 3. Trust Boundary

### Web Control Plane

Owner web remains the only browser control-plane login surface for now.

- authentication authority: Korsenex IDP
- product-local authority: tenant, branch, role, capability, audit
- PIN is never accepted on web

Manager or cashier web access is deferred. If it is added later, it must be a separately scoped browser surface with real IDP login, not a relaxation of owner-only web and not a PIN-based web login.

### Desktop Runtime

Desktop runtime is a branch-operational surface.

- a device must be approved before staff auth is allowed
- staff auth is branch-scoped and device-aware
- local PIN is only a re-entry factor after an online bootstrap
- machine identity stays separate from human identity

### Backend Authority

The backend remains authoritative for:

- tenant and branch membership
- role and capability mapping
- device approval state
- staff activation state
- revocation
- audit trails

The device may cache runtime auth state locally, but that local state never replaces backend authority.

## 4. Actors and Credential Classes

### Owner

- signs into web with Korsenex IDP
- approves devices
- issues staff activations
- revokes device or staff runtime access

### Staff

- exists as a central app-managed staff identity
- belongs to an explicit tenant and branch
- may unlock approved desktop devices after activation
- does not use PIN for web login

### Device

- has its own machine identity and approval state
- may participate in machine-to-cloud or hub-to-spoke trust
- may not substitute for staff identity

### Credential Classes

The system keeps these separate:

- owner web session
- desktop online session
- device credential
- local desktop auth seed
- local PIN verifier

No credential may be reused across those classes.

## 5. End-to-End Flows

### 5.1 Device Provisioning

The packaged desktop starts untrusted.

- it shows a stable installation fingerprint and claim code
- the owner approves the claim in web
- the approval binds the installation to a specific tenant and branch device record

Until the device is approved, no staff activation is allowed.

### 5.2 First Staff Activation

After device approval:

- the owner selects a branch staff member in web
- the owner issues a short-lived, single-use activation for that staff member and that exact device
- the desktop redeems the activation online

The backend must verify:

- device is approved and branch-bound
- staff is active
- staff belongs to the same tenant and branch
- staff role is allowed on the desktop surface
- activation is single-use, unexpired, and bound to that device

If valid, the desktop receives:

- a short-lived online runtime session
- a device-bound local auth seed
- policy metadata such as offline-valid-until, lockout thresholds, and activation version

### 5.3 Local PIN Enrollment

Immediately after activation:

- the desktop enrolls a local PIN for that staff member on that device
- if a temporary PIN exists, the desktop forces rotation on first unlock

The local PIN is:

- stored only as a strong salted local hash
- never stored as a cloud password
- never valid on web

### 5.4 Repeat Online Unlock

For daily runtime use:

- the staff member unlocks the same device with PIN
- local verification gates the unlock
- when the backend is reachable, the desktop refreshes online session, policy, and revocation posture

### 5.5 Repeat Offline Unlock

Offline unlock is allowed only when all of these are true:

- the same staff member was previously activated on the same approved device
- offline access has not expired
- the local PIN matches
- lockout thresholds are not exceeded
- local device binding still matches the activation record

Offline unlock does not grant new authority. It only re-enters previously granted runtime posture within a bounded window.

### 5.6 Revocation and Rebind

The next online contact must invalidate or block runtime access when:

- device approval is revoked
- device is archived or moved
- staff activation is revoked
- staff is deactivated
- staff loses branch membership
- role loses desktop capability
- tenant or branch is suspended

## 6. Security Rules

### Mandatory Rules

- No staff PIN login on web.
- No PIN-only first trust.
- No cross-tenant or cross-branch auth fallback.
- No ambiguous identity resolution by “first matching PIN”.
- No renderer `localStorage` for runtime bearer tokens.
- No overlap between staff PIN material and web/cloud password material.
- No indefinite offline unlock; local auth must expire.
- No silent privilege carryover across reconnect; role and branch validity must be rechecked.
- Audit events are required for approval, activation, unlock failure, lockout, revoke, and rebind actions.

### Identity Resolution Rule

The backend must not authenticate staff by PIN alone.

The allowed patterns are:

- device-bound activation that already identifies the staff member before PIN verification
- explicit staff selection plus PIN on that device

The forbidden pattern is:

- scanning branch rows and accepting the first matching PIN hash

### Storage Rule

Desktop session and local auth state must live in native secure storage or native DB layers protected by the host OS where available.

Frontend renderer storage is not acceptable for long-lived runtime session secrets.

## 7. RMS Hardening Scope

RMS is the proving ground for this auth model because it already has:

- device approval behavior
- desktop runtime
- local PIN re-entry

Before Store ports the model, RMS must be hardened.

### 7.1 Tenant and Branch Safety

Replace staff login lookup rules with strict backend-scoped identity checks.

Required changes:

- remove branchless auth fallback during staff login
- remove login-time promotion or rewrite of legacy branchless rows
- require staff runtime auth to resolve only within the correct tenant and branch

### 7.2 Staff Identity Ambiguity

Eliminate PIN-only identity ambiguity.

Required changes:

- stop resolving staff login by first matching PIN
- bind runtime activation to a specific staff id
- optionally require explicit staff selection on desktop where multiple staff are activated locally

### 7.3 Credential Separation

Stop reusing staff PIN material as any cloud or web password.

Required changes:

- remove staff PIN coupling to `GlobalUser.hashed_password`
- remove or fully isolate legacy password routes so staff PIN cannot act as a web credential

### 7.4 Desktop Secret Storage

Replace renderer token storage with native secure storage.

Required changes:

- bearer tokens must not live in renderer `localStorage`
- local auth seeds must live in native secure storage or protected native DB storage

### 7.5 Lockout and Revocation

Add runtime lockout and revocation discipline.

Required changes:

- failed-attempt counters
- retry backoff and temporary lockout
- bounded offline-valid-until
- activation versioning
- reconnect-time revocation checks

### 7.6 RMS Deliverable

RMS Phase 1 is complete when:

- approved device + one-time activation + local PIN re-entry works
- no tenant or branch fallback login remains
- no PIN-as-password overlap remains
- no renderer token storage remains
- lockout and audit coverage exist

## 8. Shared Contract to Freeze After RMS Hardening

Once RMS hardening passes, freeze one shared auth contract for RMS and Store:

- owner-only web control-plane login through Korsenex IDP
- approved device claim and bind
- single-use staff activation bound to device, tenant, branch, and staff id
- local PIN re-entry only after activation
- distinct human and machine credentials
- explicit offline expiry, revocation, and audit semantics

This contract becomes the reference for Store `CP-016`.

## 9. Store Port Sequence

Store should not invent a second auth model.

Instead it should port the hardened shared contract:

- replace developer token paste in `apps/store-desktop/`
- add owner-issued staff activation bootstrap
- add native secure session handling
- add sign-out, refresh, and reconnect-time revocation
- keep owner web on Korsenex IDP
- keep branch staff off web for now

## 10. Manager Web Access Decision

Manager web login is not part of this design.

Reasoning:

- owner-only web keeps the public control-plane surface narrower
- current branch manager workflows can live on desktop runtime
- adding manager web access now would widen attack surface before the shared auth model is hardened

If manager browser access is needed later, it must be introduced as:

- a separate explicitly scoped browser surface
- real IDP-backed web login
- independent RBAC review
- independent surface-policy review

It must not be introduced by weakening owner-only web or by reusing staff PIN login.

## 11. Verification and Exit Criteria

### RMS Phase 1 Exit Criteria

- device approval is required before activation
- staff activation is single-use and device-bound
- local PIN is only a re-entry factor
- login no longer relies on branchless or cross-tenant fallback
- local and online unlock attempts are rate-limited and audited
- renderer storage no longer holds runtime bearer secrets

### Phase 2 Exit Criteria

- one shared written auth contract exists
- Store and RMS both reference the same runtime auth method
- Store `CP-016` is ready to implement against that contract

## 12. Deferred Work

The following are intentionally deferred:

- manager browser access
- staff browser access
- broader offline branch-authoritative business continuity
- spoke and hub-specific auth refinements beyond the shared contract
