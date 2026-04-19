# Cross-App Auth And Session Foundation Design

Date: 2026-04-19
Owner: Codex
Status: Drafted after design approval

## Goal

Replace the suite's mixed bootstrap patterns with one public-release-ready auth and session model.

This slice is not about redesigning Korsenex identity itself. It is about making every app in the suite enter, restore, refresh, recover, and sign out in a way that matches how the product is actually used.

When this slice is complete:

- `owner-web` and `platform-admin` should use real Korsenex web sign-in rather than manual token paste
- `store-desktop` should keep device-bound activation and local unlock, but present a fully product-grade session lifecycle
- `store-mobile` should move from in-memory pairing/session posture to durable pairing and runtime-session recovery
- the app suite should share one session-lifecycle contract even though entry differs by surface

## Problem Statement

The suite is now productized visually, but auth and entry posture are still inconsistent.

Today:

- [OwnerWorkspace.tsx](/d:/codes/projects/store/apps/owner-web/src/control-plane/OwnerWorkspace.tsx) still starts from manual `Korsenex token` input
- [PlatformAdminWorkspace.tsx](/d:/codes/projects/store/apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx) still starts from manual `Korsenex token` input
- `packages/auth` is still mostly a local-dev bootstrap helper rather than a real shared auth/session foundation
- `store-desktop` already has stronger activation/unlock behavior, but its product-grade recovery, session restore, and signed-out posture still need to be treated as part of one deliberate system
- `store-mobile` still uses in-memory pairing/session repositories and a fake hub client posture in [StoreMobileApp.kt](/d:/codes/projects/store/apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt) and [StoreMobileHubClient.kt](/d:/codes/projects/store/apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileHubClient.kt)

The suite therefore has enterprise-looking shells on top of non-uniform entry behavior. That is not release-safe.

## Chosen Model

The accepted model is:

- one shared auth and session foundation
- two surface-specific entry classes
- one common session lifecycle across all apps

The two entry classes are:

### 1. Web Control Surfaces

- `owner-web`
- `platform-admin`

These use:

- Korsenex redirect-based sign-in
- redirect callback parsing
- control-plane token exchange
- browser session restore
- token refresh
- explicit sign-out

### 2. Device-Bound Runtimes

- `store-desktop`
- `store-mobile`

These use:

- approved activation or pairing
- persisted runtime session state
- local unlock where appropriate
- expiry-aware refresh
- explicit sign-out and recovery

This keeps the suite coherent without forcing browser-style login onto physical runtime devices.

## Scope

### In Scope

- shared auth/session foundation for web apps
- replacement of manual token entry in:
  - `owner-web`
  - `platform-admin`
- session restore, refresh, sign-out, and expired-session recovery for:
  - `owner-web`
  - `platform-admin`
  - `store-desktop`
  - `store-mobile`
- production-grade entry surfaces for signed-out and recovery states
- durable mobile pairing/session persistence
- suite-wide session-contract cleanup so productized shells can trust a consistent entry and recovery model

### Out Of Scope

- redesigning the Korsenex identity provider itself
- changing the core JWT/JWKS validation model in the backend beyond what entry flows need
- customer-facing authentication
- social login, MFA UX, or tenant self-service auth administration
- broad RBAC redesign
- non-auth product redesign work unrelated to session entry and lifecycle

## Product Principles

The implementation should follow these principles:

1. `Respect the surface`
   - control surfaces authenticate like web products
   - device runtimes authenticate like device runtimes
2. `One lifecycle, different entry points`
   - restore, refresh, expiry, recovery, and sign-out should feel like one system across the suite
3. `No manual token paste in public-release product flows`
   - local-dev bootstrap remains a developer-only path
4. `Recovery must be first-class`
   - expired, revoked, detached, and locked states should be intentional product states, not edge-case failures
5. `Durability matters`
   - mobile and runtime sessions must survive app restarts using proper local persistence

## Shared Lifecycle Model

Every surface should follow the same high-level lifecycle:

### 1. Not Authenticated

The user or device is at a signed-out or not-yet-activated state.

Entry differs by surface:

- web: `Sign in with Korsenex`
- desktop: `Activate device` or `Unlock terminal`
- mobile: `Pair device` or `Resume paired runtime`

### 2. Session Bootstrapping

After successful entry:

- exchange or redeem into a live session
- load actor and required scope posture
- persist the session record locally
- transition into the appropriate product shell

### 3. Live Session

While active:

- `expires_at` is tracked
- refresh occurs before hard expiry where possible
- shell state reflects live session posture
- actor/scope remain bound to the stored session

### 4. Recovery

If refresh or validation fails:

- web surfaces return to signed-out state with a clear reason
- desktop falls back to unlock, reactivation, or signed-out runtime state depending on failure
- mobile falls back to restore, re-pair, or signed-out paired-device recovery depending on failure

### 5. Sign-Out Or Detach

Surface-specific semantics:

- web: sign out operator session
- desktop: sign out live session while preserving approved device identity
- mobile: sign out runtime session, with explicit unpair available as a stronger detach action

## App-Specific Design

### Owner Web

Replace manual token entry with:

- signed-out owner entry surface
- `Sign in with Korsenex` CTA
- redirect-return handling
- session restore on reload
- refresh before expiry
- explicit sign-out
- expired or revoked session recovery

The current manual bootstrap in [OwnerWorkspace.tsx](/d:/codes/projects/store/apps/owner-web/src/control-plane/OwnerWorkspace.tsx) should no longer appear in production entry posture.

### Platform Admin

Apply the same web control-surface model:

- platform-branded sign-in screen
- redirect return and exchange
- session restore and refresh
- explicit sign-out
- clear platform-safe recovery messaging

The current manual bootstrap in [PlatformAdminWorkspace.tsx](/d:/codes/projects/store/apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx) should no longer be the product entry path.

### Store Desktop

Preserve the approved runtime model already present in:

- [client.ts](/d:/codes/projects/store/apps/store-desktop/src/control-plane/client.ts)
- [useStoreRuntimeWorkspace.ts](/d:/codes/projects/store/apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts)

But finish the lifecycle as a product surface:

- clearer signed-out activation posture
- clearer unlock posture
- reliable session restore
- refresh before expiry
- clear sign-out
- explicit recovery when device/session is revoked
- browser-preview posture should remain visibly non-production and should not expose public token-entry flows outside developer mode

### Store Mobile

Move mobile from transitional demo posture to durable runtime behavior.

The current mobile composition uses:

- fake hub client behavior in [StoreMobileHubClient.kt](/d:/codes/projects/store/apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileHubClient.kt)
- in-memory session persistence in [StoreMobileSessionRepository.kt](/d:/codes/projects/store/apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileSessionRepository.kt)

This slice should replace that with:

- durable paired-device persistence
- durable runtime-session persistence
- restore-on-reopen
- expiry-aware session recovery
- explicit sign-out and unpair actions
- shell selection after restore based on runtime profile

The pairing UI in [PairingScreen.kt](/d:/codes/projects/store/apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingScreen.kt) remains the correct product model, but its backing persistence and lifecycle must become release-grade.

## Implementation Boundary

### Backend

The backend should remain mostly intact.

Expected backend adjustments, if needed, are limited to:

- redirect callback exchange compatibility for web entry
- consistent refresh and sign-out behavior
- runtime activation parity where mobile needs the same class of redeem flow as desktop
- clearer failure payloads for revoked/expired/recovery states

This is primarily a suite integration and runtime-auth slice, not a new backend auth platform.

### Shared Web Auth Foundation

`packages/auth` should evolve from dev-bootstrap utilities into a real shared web auth layer for:

- redirect initiation helpers
- redirect callback parsing
- session persistence and restore
- refresh scheduling
- sign-out
- expired-session handling

In this slice, `shared auth/session foundation` means:

- shared web-facing code for `owner-web` and `platform-admin`
- shared session-lifecycle terminology and state transitions across every surface
- shared recovery semantics, even where implementation remains platform-specific

It does **not** mean forcing desktop and mobile runtimes to literally reuse the same persistence or unlock implementation as web surfaces.

Local-dev bootstrap support can remain, but only as a developer-only utility behind explicit non-production behavior.

### Desktop Runtime Auth Foundation

Desktop should keep its existing device-bound model and refine it, not replace it.

### Mobile Runtime Auth Foundation

Mobile should gain durable repositories and runtime-safe restore behavior rather than continuing to rely on in-memory session state.

## Minimum Backend Contract Adjustments

The planning baseline should assume frontend-first work unless these backend gaps are confirmed:

- named web exchange contract remains `POST /v1/auth/oidc/exchange`
- session refresh remains `POST /v1/auth/refresh`
- sign-out remains `POST /v1/auth/sign-out`
- desktop activation remains `POST /v1/auth/store-desktop/activate`
- desktop unlock remains `POST /v1/auth/store-desktop/unlock`
- mobile runtime activation should use the existing runtime contract at `POST /v1/auth/runtime/activate` unless the current mobile pairing path proves incompatible

If implementation discovers missing recovery detail, the only backend work in scope is:

- clearer revoked/expired/detached failure payloads
- payload parity between desktop and mobile runtime activation responses
- any redirect-safe callback exchange helper strictly required for web sign-in completion

The plan should treat any broader backend auth redesign as out of scope.

## Recovery State Matrix

The planner should treat the following states as explicit product states rather than generic failures.

### Web Surfaces

#### Expired session

- attempt refresh
- if refresh succeeds, remain live
- if refresh fails, return to signed-out screen with an expiry explanation

#### Revoked session

- clear persisted session
- return to signed-out screen
- message should indicate access or session was revoked

### Store Desktop

#### Locked

- approved device remains known
- local unlock screen is shown
- successful unlock restores live runtime session or triggers remote refresh if needed

#### Expired session

- if refresh succeeds, restore runtime
- if refresh fails but device remains approved, fall back to unlock or signed-out runtime state depending on local-auth posture

#### Revoked session

- clear live session
- preserve device identity only if local policy still allows device recognition
- route to activation or blocked runtime posture with an explicit revocation explanation

#### Detached or invalid device approval

- clear live session and any activation-specific resume state
- require reactivation

### Store Mobile

#### Expired runtime session

- attempt runtime refresh or re-redeem through the paired runtime contract
- if unsuccessful, keep paired-device record but return to runtime-resume or sign-in-required posture

#### Revoked runtime session

- clear live runtime session
- preserve paired-device record unless the pair itself is revoked
- require a fresh runtime session

#### Unpaired or detached device

- clear paired-device and runtime-session state
- return to pairing screen

## Testing Strategy

Required coverage:

### Shared

- unit coverage for shared session utilities
- persistence, restore, expiry, and sign-out tests

### Owner Web

- signed-out entry render
- callback or bootstrap exchange success
- restore on reload
- refresh/recovery
- sign-out

### Platform Admin

- same lifecycle coverage as owner-web
- no production token-paste entry posture

### Store Desktop

- activation
- unlock
- restore
- expiry-aware refresh
- sign-out
- revoked-session and revoked-device recovery
- browser production posture

### Store Mobile

- pair
- restore paired runtime on reopen
- expired-session recovery
- sign-out
- unpair
- handheld/tablet shell selection after restore

## Deferred Public-Release Follow-Ons

These are intentionally deferred from this slice, but must remain tracked before public release quality is considered fully complete across the suite:

- polished tenant and operator branding across signed-out auth surfaces
- deeper native secure-storage hardening for mobile if the first durable storage pass is transitional
- richer auth lifecycle telemetry and audit visibility
- optional SSO convenience improvements
- final copy and empty/loading/error-state polish across every auth entry and recovery screen

These deferments are release-critical polish and hardening, not optional niceties, and should be carried explicitly into the post-foundation public-release backlog.

## Success Criteria

This slice is successful when:

- `owner-web` and `platform-admin` no longer depend on manual product-facing token entry
- `store-desktop` presents a deliberate device-bound auth lifecycle instead of mixed bootstrap behavior
- `store-mobile` can pair, persist, restore, recover, sign out, and unpair without in-memory session loss
- the suite has one coherent session lifecycle model even though entry differs by surface
- developer bootstrap remains available only as an explicit development path and not as the public product contract
