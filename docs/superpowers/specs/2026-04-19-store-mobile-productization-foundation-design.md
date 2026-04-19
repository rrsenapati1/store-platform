# Store Mobile Productization Foundation Design

Date: 2026-04-19
Owner: Codex
Status: Drafted after design approval

## Goal

Turn `store-mobile` into a product-quality handheld associate runtime with a strong primary workflow.

This slice is not about adding more backend authority. It is about making the Android runtime fast, modern, field-usable, and visually credible as part of the same enterprise suite as:

- `store-desktop`
- `owner-web`
- `platform-admin`

When this slice is complete:

- the handheld runtime should feel like a real associate tool instead of a compressed operations console
- `Scan` should become the dominant home and navigation anchor
- pairing and runtime session entry should feel intentional instead of technical
- the mobile UI should adopt the same light/dark semantic design language as the rest of the suite
- the resulting component and theme patterns should prepare the follow-on `inventory tablet` redesign

## Problem Statement

The current mobile app is functionally meaningful but structurally weak as a product.

Today:

- `StoreMobileApp.kt` orchestrates pairing, session state, shell selection, scanner integration, and multiple operations domains in one large root
- the handheld flow is section-driven rather than workflow-driven
- scan, receiving, stock count, restock, expiry, and runtime status compete as equal entry points
- the pairing/runtime entry posture is technically better after the auth/session foundation, but it still reads like a setup surface instead of a polished device runtime
- the handheld and tablet shells exist, but neither currently defines a strong product identity

This creates the same issue that previously existed in `store-desktop`: deep capability coverage without a clear primary flow.

## Chosen Model

The accepted model is:

- `store-mobile` productization starts with the `handheld associate runtime`
- the first mobile pass is `scan-first`
- secondary operations should be reached through contextual routing and a smaller flow model instead of equal-weight tabs
- mobile should adopt the suite-wide light/dark token system from the start
- `inventory tablet` is explicitly deferred but should inherit the same visual and component language later

This is a `handheld runtime redesign`, not a polish pass over the existing section switcher.

## Scope

### In Scope

- product-quality rewrite of the `handheld` mobile runtime
- improved pairing/session entry posture for:
  - signed out
  - paired but signed out
  - expired session
  - active runtime
- new handheld-first flow model with:
  - `Entry`
  - `Scan`
  - `Tasks`
  - `Runtime`
- `Scan` as the default post-entry home
- contextual routing from scan results into:
  - receiving
  - stock count
  - restock
  - expiry review
- stronger handheld runtime header, scan result panel, contextual action rail, and runtime status treatment
- shared mobile theme and UI foundation aligned with suite light/dark behavior

### Out Of Scope

- full `inventory tablet` redesign
- customer-facing or sales-driven mobile runtime
- advanced mobile reporting or analytics
- deep native secure-storage hardening beyond the current persistence boundary
- full redesign of every mobile error/empty state across all secondary flows
- cross-platform design-polish completion for every app in the suite

## Product Principles

The redesign should follow these rules:

1. `Scan is the primary workflow`
   - the handheld should feel live and useful immediately after a scan
2. `One screen, one job`
   - the screen should answer what was scanned, what it means, and what action comes next
3. `Associate speed over module completeness`
   - the handheld should optimize for field work, not for exposing every capability equally
4. `Touch-first clarity`
   - large targets, readable hierarchy, and strong one-handed action posture
5. `Suite consistency without web-admin imitation`
   - the app should share the suite language, but remain unmistakably mobile and tactile

## Information Architecture

`store-mobile` should become a handheld runtime with four top-level areas:

### 1. Entry

Purpose:

- move the device from pairing/session recovery into a ready runtime state

Contains:

- paired device identity
- hub/runtime identity
- session state
- session recovery
- activation redemption
- sign out
- unpair

This is not just a pairing form. It should feel like a runtime checkpoint for a field device.

### 2. Scan

Purpose:

- own the default handheld experience

This becomes the primary surface and should open by default whenever a live runtime session exists.

### 3. Tasks

Purpose:

- show queued or resumable operational work without displacing the scan flow

Contains:

- receiving work
- stock count work
- restock work
- expiry work

This should act as a task hub, not a generic tab switcher for the whole app.

### 4. Runtime

Purpose:

- surface device, scanner, hub, and runtime health

Contains:

- session expiry posture
- pairing posture
- scanner availability
- sync/runtime status

This keeps device diagnostics accessible without crowding the primary work loop.

## Scan Screen Composition

The `Scan` screen should be the centerpiece of the redesign.

### Primary Goal

The associate should be able to:

- scan an item
- identify it immediately
- understand its stock and operational posture
- take the next action without navigating a generic operations menu

### Handheld Layout

The recommended handheld structure is vertical and action-led.

#### A. Scan Command Header

Top area:

- branch/runtime context
- scan readiness state
- barcode/manual entry
- camera or hardware scanner posture

This should make the device feel active and ready, not like a form page.

#### B. Last Scanned Item Panel

Primary focal area.

Shows:

- product name
- barcode / SKU
- stock on hand
- reorder point / target stock where relevant
- batch or compliance hints when relevant
- compact posture badges

This panel should dominate the screen and be readable one-handed in the field.

#### C. Contextual Action Rail

Primary next actions derived from the scanned item:

- `Receive stock`
- `Count item`
- `Restock shelf`
- `Review expiry`
- `Scan another`

The key rule:

- one or two actions should dominate visually
- not every operation should appear as an equal button

#### D. Recent Task Context

Compact resume area for:

- active receiving session
- active count session
- active restock task
- active expiry review

This allows resumption without forcing the user to browse module tabs.

#### E. Task Queue Preview

A lower-priority preview of waiting work:

- low stock
- pending counts
- pending receipts
- expiry risk

This belongs below the scan flow, not above it.

## Visual Direction

### Visual Thesis

Fast, modern, field-usable handheld software.

The app should feel:

- high contrast
- tactile
- calm
- operationally serious
- visually modern without becoming decorative

It must not feel like a web admin panel compressed onto Android.

### Shared Suite Language

The app should clearly belong to the same product family as the other redesigned surfaces.

Shared characteristics:

- semantic light/dark theme tokens
- calm surfaces
- disciplined accent usage
- state-first color semantics
- restrained motion

Mobile-specific posture:

- larger touch targets
- stronger vertical rhythm
- faster-feeling transitions
- more obvious primary actions

### Theme Requirement

This slice should include both light and dark support from the start through shared semantic tokens:

- surface tiers
- text tiers
- border and divider tiers
- accent and primary action colors
- success / warning / error state colors
- motion and radius tokens where relevant

Dark mode should be deliberate, not an inverted fallback.

## Component Foundation

This slice should introduce or standardize stronger mobile primitives for:

- handheld runtime header
- scan result panel
- contextual action rail
- task preview list
- runtime status strip
- full-width action buttons
- item posture badges
- entry-state cards for paired, signed out, expired, and recovery posture

These should be built with reuse in mind so the later tablet redesign can inherit them instead of diverging into a second visual language.

## Entry Flow Design

The entry flow should be purposeful and productized.

Recommended sequence:

1. identify paired device posture
2. determine runtime session posture
3. recover expired or signed-out state if needed
4. redeem activation when required
5. enter the handheld runtime

Important lifecycle distinction:

- pairing says the device is allowed to participate
- live session says the associate runtime is currently active

This boundary must stay visible in the entry and runtime flows.

## Tasks Model

The handheld should not expose every operation as a top-level home.

Recommended behavior:

- `Scan` is the default
- `Tasks` is where queued and resumable work lives
- contextual actions from a scan should deep-link into the relevant task flow with the scanned item already selected

This means:

- scanned low-stock item -> restock flow
- scanned counted item -> stock count flow
- scanned incoming PO item -> receiving flow
- scanned expiring batch -> expiry flow

The user should rarely have to start from a blank task view.

## Implementation Boundary

This slice should prefer preserving current domain repositories and control-plane contracts while rewriting the mobile shell composition and flow hierarchy.

Likely implementation shape:

- split the current `StoreMobileApp.kt` orchestration into clearer runtime shell and entry composition units
- introduce handheld-specific shell primitives instead of treating handheld and tablet as equal first-class shells in the root
- preserve current repository and view-model boundaries where they are already sound
- refactor navigation into the new:
  - `Entry`
  - `Scan`
  - `Tasks`
  - `Runtime`
  model

This first slice should not attempt to redesign the entire tablet experience at the same time.

## Testing And Verification

The first mobile productization slice should be validated at three levels.

### UI And Interaction Tests

- entry-state transitions
- scan-first shell behavior
- contextual action routing
- task preview and task resume posture
- runtime status presentation

### Lifecycle Preservation

- persisted pairing still restores correctly
- session expiry still falls back to explicit recovery
- sign out preserves pairing where intended
- unpair clears both pairing and session state
- repository-backed operations continue working after the shell rewrite

### Build Verification

- Android unit tests
- Android app build / CI lane
- any affected Compose UI tests

## Success Criteria

This slice is successful when:

- the handheld app feels like a real associate runtime instead of a small operations menu
- `Scan` becomes the obvious primary home
- scanned items clearly drive the next recommended action
- pairing/session recovery feels intentional and modern
- the app visibly belongs to the same suite as desktop, owner, and platform admin
- the component/theme foundation is strong enough to support the later tablet redesign

## Release-Critical Deferred Work

The following tasks are deferred from this slice but must remain tracked before full public-release polish is considered complete across the suite:

- full `inventory tablet` productization using the same design system
- secure-storage hardening review for persisted mobile runtime state
- final mobile-wide empty/error/loading state polish pass
- final visual/system parity audit across:
  - `store-mobile`
  - `store-desktop`
  - `owner-web`
  - `platform-admin`

These are not optional nice-to-haves. They are deferred public-release tasks.

## Risks

### Risk: Polishing The Existing Switcher Instead Of Redesigning The Flow

If the work only adds better spacing and color while preserving equal-weight operations navigation, the product problem remains unsolved.

Mitigation:

- make `Scan` the structural default
- reduce equal-weight entry points

### Risk: Rebuilding Too Much In The Root File

`StoreMobileApp.kt` already carries a large orchestration burden.

Mitigation:

- split by shell and responsibility during implementation
- keep repository and view-model contracts intact where possible

### Risk: Neglecting Tablet Follow-On

If the handheld redesign introduces a visual system that cannot support the later tablet pass, the suite will fragment.

Mitigation:

- build reusable mobile primitives and theme rules now
- explicitly track tablet productization as the next mobile follow-up
