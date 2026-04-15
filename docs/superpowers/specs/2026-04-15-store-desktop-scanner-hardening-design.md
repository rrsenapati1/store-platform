# Store Desktop Scanner Hardening Design

## Context

Store Desktop already supports:

- packaged-runtime barcode lookup
- keyboard-wedge scanner capture in the React runtime shell
- native runtime hardware status for printers and basic scanner posture

The current scanner path works, but the operator posture is still thin:

- scanner readiness is implicit
- shell diagnostics do not explain much beyond the last scan timestamp
- barcode operators do not get an explicit setup/help state where they actually scan

That leaves `V2-002` uneven across surfaces. Mobile now has:

- live camera scan
- generic external scanner support
- rugged-scanner diagnostics
- optional Zebra DataWedge provisioning

Desktop should not lag behind on basic scanner trust and operator recovery just because it still uses a keyboard-wedge path.

## Product Decision

Add a bounded scanner-hardening slice to Store Desktop:

- keep the existing keyboard-wedge capture path
- extend the runtime hardware diagnostics contract with richer scanner posture
- surface scanner status, transport, last activity, and setup hints in the shell/runtime UI
- keep the scope away from low-level USB device enumeration and vendor SDK work

This remains a hardening slice, not a new device-driver stack.

## Goals

- make packaged desktop scanner posture explicit
- help operators understand whether the scanner path is ready, degraded, or browser-fallback
- show last scan activity and a small scan preview safely
- keep the current barcode lookup flow unchanged
- improve `V2-002` parity across desktop and mobile/tablet surfaces

## Non-Goals

- USB device enumeration
- Windows HID device identity discovery
- vendor-specific desktop scanner SDKs
- backend changes
- payment/printer hardware expansion

## Architecture

### Diagnostics model

Extend the runtime-hardware diagnostics contract with:

- `scanner_capture_state`
  - `ready`
  - `unavailable`
  - `browser_fallback`
  - `attention_required`
- `scanner_transport`
  - `keyboard_wedge`
  - `unknown`
- `last_scan_at`
- `last_scan_barcode_preview`
- `scanner_status_message`
- `scanner_setup_hint`

This remains an operator-facing diagnostics contract. It is not a scanner-device inventory model.

### Capture flow

Keep the existing `useStoreRuntimeBarcodeScanner` hook as the wedge-capture owner:

- when the packaged desktop is live and unlocked, it listens for fast keyboard input
- when a valid barcode is accepted, it still routes into the same barcode lookup path
- the same hook also publishes scanner diagnostics:
  - current capture posture
  - transport
  - last scan timestamp
  - a short barcode preview

### Native bridge

The existing runtime hardware bridge should persist the richer scanner diagnostics in the local hardware state file. That gives Store Desktop one local source of truth for scanner posture alongside printer posture.

This slice does not require native USB scanning. The native bridge only needs to store and return the richer diagnostics contract.

### UI surfaces

Use existing desktop surfaces:

1. `StoreRuntimeShellSection`
   - scanner capture state
   - scanner transport
   - last scan time
   - scanner message/hint

2. barcode lookup surface
   - compact scanner diagnostics card next to the lookup flow
   - scanner-ready / browser-fallback / attention-required posture

## State Rules

`ready`
- packaged desktop
- session live
- local unlock active
- scanner hook active

`browser_fallback`
- non-packaged/browser runtime

`unavailable`
- packaged runtime but scanner path not active because the session is not live or local unlock is missing

`attention_required`
- explicit invalid/unknown diagnostics contract
- explicit runtime scanner error or impossible posture

The first slice should not invent errors from weak heuristics. No scan activity alone is not a failure.

## UX

### Shell identity section

Add scanner diagnostics lines for:

- scanner capture state
- scanner transport
- last local scan
- last scan preview
- scanner status
- scanner setup hint

This is operator/support posture.

### Barcode lookup section

Add a compact diagnostics card near the scan controls:

- `Ready for scanner input`
- `Browser fallback`
- `Scanner unavailable`
- `Scanner attention required`

The card should also show:

- last scan timestamp
- setup hint for wedge scanners

## Files

Expected areas:

- `apps/store-desktop/src/control-plane/useStoreRuntimeBarcodeScanner.ts`
- `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareContract.ts`
- `apps/store-desktop/src/runtime-hardware/*`
- `apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx`
- `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`
- `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace*.test.tsx`
- `apps/store-desktop/src/runtime-hardware/*.test.ts`
- `apps/store-desktop/src-tauri/src/runtime_hardware.rs`
- `docs/WORKLOG.md`

## Testing

- hook tests for scanner diagnostics state and scan metadata
- hardware-contract tests for richer diagnostics parsing
- shell-section rendering tests
- barcode lookup diagnostics rendering tests
- native Rust tests for default diagnostics shape and persistence

## Exit Criteria

This slice is complete when:

- Store Desktop exposes richer scanner diagnostics through the hardware bridge
- the scanner hook publishes last-scan metadata and transport/setup posture
- shell and barcode lookup UI both render scanner posture clearly
- the current barcode lookup workflow remains unchanged
- packaged and browser runtimes remain explicitly distinguishable
