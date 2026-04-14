# Store Mobile Runtime Design

Date: 2026-04-15  
Owner: Codex  
Status: Draft for review

## Goal

Define the first `store-mobile` product slice for the V2 launch program.

This app is an `Android-first`, `Kotlin-native`, `mobile_store_spoke` companion for branch operations. It is not a full mobile POS in the first slice. Its purpose is to extend Store's branch runtime into a fast handheld workflow for cashier assist and store operations without introducing a second billing authority.

## Product Decision

The first mobile runtime slice will be:

- Android only
- Kotlin native
- branch-hub paired as `mobile_store_spoke`
- cashier-assist + operations-first

This slice will not include:

- mobile invoice finalization
- payment capture on the device
- independent offline sale authority
- iOS

If mobile billing is needed later, it should be added as a later V2 or post-V2 slice after the operational/mobile spoke model is proven.

## Why Kotlin Instead Of Expo/React Native

The long-term mobile target for Store is an enterprise retail runtime, not a light companion app.

Kotlin-native is the chosen direction because it gives a safer foundation for:

- fast and responsive Android UI/UX
- tighter camera and scanning control
- stronger background/runtime behavior
- cleaner evolution toward richer enterprise device integration
- fewer bridge/plugin constraints as the app grows into deeper hardware and managed-device deployments

This repo remains TypeScript-heavy on the web/desktop side, but the mobile runtime should optimize for Android retail quality over frontend stack uniformity.

## Scope

Included in the first mobile slice:

- hub pairing as `mobile_store_spoke`
- staff sign-in/unlock on the paired device
- camera barcode scan
- product lookup
- price/stock lookup
- customer lookup
- receiving support
- stock count support
- expiry support
- basic branch runtime/sync posture visibility

Deferred from this slice:

- billing/POS on mobile
- payment capture
- printer integration on mobile
- independent offline sale authority
- iOS
- advanced vendor hardware SDKs unless required for the above flows

## Architectural Fit

The mobile app must fit the existing Store authority model:

- control-plane Postgres remains the system of record
- branch hub remains the local trust anchor
- mobile app acts as a `mobile_store_spoke`
- mobile app does not bypass the branch hub to become a second branch authority

The app is a new runtime surface, not a new backend or identity model.

## Runtime Role

The mobile app pairs as `mobile_store_spoke`.

That implies:

- it must register against the same branch-hub/spoke runtime model established in V2 planning
- it uses the hub-local manifest and spoke registration flow
- it receives a local spoke runtime session for branch-local relay activity
- it inherits the same tenant/branch/device scoping rules as other runtime devices

The app must not invent a parallel auth surface outside the approved Store device and staff model.

## Connectivity Model

### Preferred Path

The preferred runtime path is:

1. mobile app discovers/pairs with the approved branch hub
2. mobile app authenticates and registers as `mobile_store_spoke`
3. mobile app uses the hub relay boundary for runtime reads/writes

### First-Slice Rule

The first slice should stay `hub-first`, not cloud-first.

That keeps:

- branch-local runtime posture consistent
- device governance explicit
- offline/resilience posture aligned with the existing hub model
- future mobile runtime authority bounded by the same branch trust anchor

Cloud-direct read escape hatches may exist later for limited safe scenarios, but should not define the first slice.

## App Responsibilities

The first mobile app should be organized around these feature modules.

### 1. Pairing / Onboarding

Responsibilities:

- scan QR or use manual approval-code pairing
- read the hub manifest
- register the device as a spoke
- persist paired-device posture locally

The app should expose clear states:

- unpaired
- pairing pending
- paired
- registration expired
- disconnected from hub

### 2. Auth / Session

Responsibilities:

- device-bound staff sign-in/unlock
- local session posture for the paired mobile device
- sign-out and revalidation

This should reuse the shared desktop auth principles:

- no staff web/IDP login requirement
- no PIN-as-cloud-password model
- no unbounded local authority

### 3. Scan + Lookup

Responsibilities:

- camera barcode scan
- fast product lookup
- stock/price visibility
- customer lookup

This is one of the highest-value mobile workflows and should feel instant.

### 4. Receiving

Responsibilities:

- view receiving work
- inspect PO/GRN receiving context
- confirm or record receiving actions allowed by policy

This should improve operator mobility without creating a separate inventory truth.

### 5. Stock Count

Responsibilities:

- cycle count style workflows
- item/batch search and scan
- count entry and review

The app should optimize for fast handheld counting, not for desktop-like dense forms.

### 6. Expiry

Responsibilities:

- expiry lookup
- near-expiry action flow
- allowed write-off support where policy permits

### 7. Runtime / Sync Posture

Responsibilities:

- show branch hub connection state
- show local relay/runtime status
- expose actionable failure posture when disconnected or stale

This must remain visible because a handheld runtime is much more sensitive to intermittent branch connectivity than a fixed desktop.

## Codebase Structure

The mobile app should be a new app, not a subfolder of `store-desktop`.

Recommended root:

- `apps/store-mobile/`

Likely internal structure:

- `app/` or feature modules for screens/navigation
- `runtime/`
  - pairing
  - auth/session
  - hub manifest/relay client
  - local posture
- `features/`
  - scan_lookup
  - receiving
  - stock_count
  - expiry
  - customer_lookup
- `platform/`
  - camera scanner
  - Android storage/session helpers
  - Android network/connectivity posture

Shared repo packages should still be reused where appropriate:

- `packages/types`
- `packages/auth` for shared contract knowledge where useful
- `packages/barcode`

But mobile UI/state must stay mobile-native rather than trying to mirror desktop React code.

## UX Principles

The mobile runtime should feel like a handheld operations tool, not a desktop screen squeezed into a phone.

Principles:

- scan-first interactions
- minimal taps for lookup and count workflows
- large, touch-friendly controls
- fast load and return to scan state
- strong focus on operator flow under movement, interruptions, and unstable connectivity

This means:

- avoid dense desktop forms
- avoid routing operators through too many setup screens once paired
- keep core branch tasks accessible from a small number of primary entry points

## Security And Authority Rules

The mobile slice must preserve Store's existing security posture.

Required rules:

- device pairing is owner/hub-approved and bounded
- sessions are tenant/branch/device scoped
- mobile does not become billing authority
- mobile does not become inventory source of truth
- local persistence must remain bounded and policy-aware
- mobile actions must remain auditable

The V2 mobile slice is a new spoke runtime, not a new control-plane authority.

## Offline / Resilience Rules

First-slice mobile resilience should stay conservative.

Allowed:

- local UI continuity
- reconnect/retry posture
- bounded cached operational context where safe

Not allowed:

- independent offline sale authority
- silent local business finalization
- divergence from the hub as local trust anchor

If mobile offline authority is ever added later, it should be a separate task with explicit reconciliation design.

## Testing Strategy

### Backend / Contract

- pairing and registration contract tests for `mobile_store_spoke`
- branch/hub/runtime-profile validation
- relay authorization and rejection rules where mobile differs from desktop spoke posture

### Android App

- pairing/onboarding flows
- sign-in/unlock/session posture
- camera scan and lookup flows
- receiving/count/expiry workflows
- runtime disconnect/reconnect posture

### End-to-End

- pair mobile device to hub
- unlock as staff
- scan barcode via camera
- perform lookup
- execute a receiving/count/expiry flow
- confirm audit/runtime posture remains consistent

## Phased Breakdown

The mobile work should likely be decomposed into these implementation slices:

1. `store-mobile app foundation`
   - app skeleton
   - Android build/run path
   - navigation/state baseline

2. `mobile pairing + auth`
   - QR/manual pairing
   - mobile spoke registration
   - staff unlock/session lifecycle

3. `camera scan + lookup`
   - camera integration
   - barcode scan UX
   - product/stock/customer lookup

4. `mobile receiving/count/expiry workflows`
   - operational mobile features

5. `mobile runtime posture + hardening`
   - diagnostics
   - reconnect posture
   - production hardening for the first mobile slice

## Exit Criteria

This spec is complete when it defines a first mobile slice that is:

- Android-first
- Kotlin-native
- branch-hub paired as `mobile_store_spoke`
- useful for cashier-assist and store operations
- explicitly not a mobile billing/POS authority in the first slice

## Deferred Work

Deferred to later slices:

- mobile billing/POS
- payment capture on mobile
- iOS
- broader advanced mobile hardware SDK work
- independent mobile offline sale authority
