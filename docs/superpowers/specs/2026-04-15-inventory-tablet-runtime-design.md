# Inventory Tablet Runtime Design

Date: 2026-04-15  
Owner: Codex  
Status: Draft

## Goal

Land the first `inventory_tablet_spoke` slice inside the existing Android app so `V2-001` expands from a handheld-only spoke into a second runtime profile with tablet-first layouts for inventory operations.

## Product Decision

The inventory tablet runtime will:

- stay inside `apps/store-mobile`
- reuse the existing Android/Kotlin stack
- pair through the same branch-hub activation model
- use `session_surface = inventory_tablet`
- resolve `runtime_profile = inventory_tablet_spoke`

This slice does not create a separate app package or a second authority model.

## Scope

Included:

- generic runtime activation support for `inventory_tablet`
- tablet-capable pairing flow in the Android app
- runtime-profile based shell resolution
- tablet-first shell for:
  - receiving
  - stock count
  - expiry
  - scan/lookup
  - runtime status
- shared repositories and session/pairing layers across handheld and tablet

Deferred:

- customer display runtime
- live camera preview wiring
- tablet-only offline authority
- billing/POS on tablet

## Architecture

The Android app keeps one shared codebase with two shell modes:

- `HANDHELD`
  - selected for `mobile_store_spoke`
- `TABLET`
  - selected for `inventory_tablet_spoke`

Shared modules remain shared:

- pairing
- session
- scan lookup
- receiving
- stock count
- expiry
- runtime status

Shell-specific UI stays separate:

- `ui/handheld/*`
- `ui/tablet/*`

## Backend Changes

Backend changes stay minimal:

- extend runtime-profile mapping to support `inventory_tablet`
- preserve the same generic non-desktop activation flow
- return `inventory_tablet_spoke` in runtime activation responses for approved tablet devices

No new authority boundary or offline rules are introduced.

## UX

Tablet UX is inventory-first:

- default to receiving instead of scan
- use a persistent navigation rail/tab model
- render wider master/detail style content where possible
- keep scan/lookup and runtime status available, but not as the home focus

This should feel like a backroom operations terminal, not a stretched phone screen.

## Testing

Required coverage:

- backend activation test for `inventory_tablet_spoke`
- Android pairing/view-model test for tablet selection
- Android shell-resolution test for handheld vs tablet mode
- existing handheld tests must remain green

## Exit Criteria

This slice is complete when:

- approved tablet devices can redeem runtime activation as `inventory_tablet_spoke`
- the Android app can pair into handheld or tablet mode
- tablet mode renders a distinct inventory-first shell
- the repo verification path covers the tablet slice without breaking the handheld slice
