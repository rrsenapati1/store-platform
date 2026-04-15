# Store Mobile External Scanner Design

## Context

`V2-002` is now the active task family. The first camera barcode slice is already live in the shared Android app, but the mobile runtime still lacks a serious external scanner path. In practice that means two common enterprise scanning modes remain uncovered:

- rugged Android handhelds that deliver scans through a broadcast intent path such as Zebra DataWedge
- generic HID/USB or Bluetooth scanners that behave like keyboard wedges

Desktop already has packaged-runtime keyboard-wedge capture, so the next bounded value is Android-first external scanner support rather than more desktop work.

## Product Decision

The next scanner-input slice should stay inside `apps/store-mobile` and add two Android-first paths:

1. `DataWedge-style broadcast scan input`
2. `HID/USB keyboard-wedge scan input on the live scan screen`

Both paths must reuse the same `ScanLookupViewModel` and scan result UI already used by camera and manual entry.

This slice does not add backend changes, new runtime authority, or vendor-specific payment/printer SDK work.

## Goals

- support rugged Android scanners that emit broadcast barcode payloads
- support generic keyboard-wedge scanners while the handheld/tablet scan screen is active
- keep one shared scan pipeline across manual, camera, and external scanner input
- keep manual entry as a fallback path
- expose enough UI posture that operators understand that external scanner input is ready

## Non-Goals

- vendor-specific deep device management or trigger APIs
- full OEM scanner SDKs beyond a broadcast contract
- background or bulk continuous scanning workflows
- backend or control-plane changes
- desktop hardware work

## Architecture

### Shared lookup pipeline

`ScanLookupViewModel` remains the single place that resolves a normalized barcode into catalog lookup state.

The view model should gain a third input source:

- `MANUAL`
- `CAMERA`
- `EXTERNAL_SCANNER`

That keeps result rendering, errors, and source labeling consistent regardless of how the barcode entered the app.

### DataWedge-style broadcast input

Add an Android-side broadcast parser and lightweight app-level event bus:

- the app registers a receiver for one explicit action string owned by Store Mobile
- received broadcast payloads are normalized and emitted to the shared app runtime
- the composable app shell listens for external scanner events and forwards them into `ScanLookupViewModel`

This should remain vendor-light:

- accept the Store Mobile action
- read common payload keys such as `com.symbol.datawedge.data_string`
- optionally accept a fallback plain `barcode` extra

The app does not need to configure the device profile itself in this slice; it only needs to be ready to receive the payload and document the expected profile settings.

### HID/USB wedge input

The scan screen should become wedge-friendly without global key interception:

- keep the barcode field focus-ready with a `FocusRequester`
- request focus when the scan screen becomes active
- treat hardware `Enter` on the barcode field as a lookup submission

This is enough for typical USB/Bluetooth/HID wedge scanners because they inject the barcode as text followed by `Enter`.

The app should not try to globally hijack all keyboard events at the activity level in this slice. That would create too much risk around normal typing and focus behavior.

## UI/UX

Both handheld and tablet scan screens should:

- continue showing live camera preview when camera is available
- allow manual barcode entry
- auto-focus the barcode field for wedge scanning
- show a short hint that external scanners are supported
- show “External scanner” as the source when a lookup came from DataWedge or a wedge scanner

Tablet still gets the wider two-pane layout. Handheld remains vertical and scan-first.

## Files

Expected new or modified areas:

- `apps/store-mobile/app/src/main/java/com/store/mobile/StoreMobileApplication.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/MainActivity.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/scan/*`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/*`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- `apps/store-mobile/app/src/test/java/com/store/mobile/scan/*`
- `apps/store-mobile/README.md`
- `docs/WORKLOG.md`
- `docs/TASK_LEDGER.md`

## Testing

This slice should stay TDD-first and mostly unit-tested:

- broadcast payload parser tests
- wedge input buffer tests
- `ScanLookupViewModel` tests for external-scanner source routing
- mobile Gradle unit suite

No backend tests are required because the slice is Android-local only.

## Exit Criteria

This slice is complete when:

- the Android app can resolve external scanner input through a DataWedge-style broadcast path
- the scan screen supports keyboard-wedge barcode entry with `Enter` submission
- external scanner results flow through the same lookup state as camera/manual scans
- handheld and tablet scan screens both expose the new posture
- docs and ledger reflect the new `V2-002` progress
