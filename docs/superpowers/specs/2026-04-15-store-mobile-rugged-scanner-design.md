# Store Mobile Rugged Scanner Diagnostics Design

## Context

`V2-002` is active. The shared Android runtime already supports:

- live camera preview scanning
- manual barcode entry
- generic external scanner intake through `DataWedge`-style broadcasts
- HID/USB wedge submission through the focused barcode field

What it still lacks is rugged-device scanner posture. Today external scanning is functional but mostly invisible: operators and support cannot easily tell whether the app is configured for rugged-device broadcasts, whether malformed payloads are arriving, or when the last external scan was seen.

This slice makes the mobile scanner path production-usable for rugged Android deployments without widening into deep OEM SDK work.

## Product Decision

The next bounded `V2-002` slice stays inside `apps/store-mobile` and adds:

- explicit external-scanner diagnostics state
- `DataWedge`-style payload error handling
- scan-screen status visibility
- runtime-status visibility
- README setup guidance for rugged device configuration

This is Android-local only. No backend changes and no desktop scanner expansion.

## Goals

- make rugged-scanner configuration posture visible
- distinguish between:
  - no known rugged-scanner configuration
  - valid external-scanner traffic
  - malformed scanner payloads
  - recent successful external scans
- keep camera/manual/external scans on one lookup pipeline
- give support enough information to diagnose a misconfigured handheld or tablet

## Non-Goals

- vendor SDK trigger APIs
- automatic device profile provisioning
- backend diagnostics storage
- desktop scanner changes

## Architecture

### External scanner event boundary

The app-level scanner bus should stop emitting plain strings and instead emit bounded scanner events:

- `BarcodeDetected(barcode, detectedAt)`
- `PayloadError(message, detectedAt)`

`MainActivity` remains the Android receiver boundary:

1. receive broadcast intent
2. parse intent extras
3. emit either a valid barcode event or payload-error event

Unknown actions remain ignored.

### Shared scanner diagnostics state

Add a small external-scanner diagnostics model in the mobile app. It should track:

- status
- last external scan time
- last payload error
- whether a valid rugged-scanner payload has ever been observed in the current session

Recommended state values:

- `UNCONFIGURED`
- `READY`
- `RECENT_SCAN`
- `PAYLOAD_ERROR`

Interpretation:

- `UNCONFIGURED`: no successful rugged-scanner payload has been observed in this session
- `RECENT_SCAN`: a recent valid external scan was received
- `PAYLOAD_ERROR`: a broadcast arrived but did not contain a usable barcode payload
- `READY`: a valid rugged-scanner path has been observed earlier in the session, and the app is now simply waiting for the next scan

This diagnostics state should be mirrored into the existing scan view-model state so both the scan screen and the runtime status screen can render it.

### Lookup boundary

`ScanLookupViewModel` stays the only place that performs catalog lookup behavior. It should continue to accept:

- `MANUAL`
- `CAMERA`
- `EXTERNAL_SCANNER`

The diagnostics layer must not become a second lookup system.

## UX

### Scan screen

Add a compact external-scanner status card near the existing camera/manual UI.

It should show:

- scanner state title
- helpful detail text
- last external scan timestamp when available
- last scanner source on the lookup result card

Examples:

- `External scanner not configured`
- `Ready for external scanner input`
- `Last external scan received at ...`
- `Scanner payload invalid`

### Runtime status screen

Extend the runtime posture to include rugged-scanner visibility:

- external scanner state label
- last external scan timestamp
- last scanner warning if present

This is for store operators and support staff, not for customers.

## Files

Expected areas:

- `apps/store-mobile/app/src/main/java/com/store/mobile/MainActivity.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/StoreMobileApplication.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/scan/*`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/*`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/runtime/RuntimeStatusScreen.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- `apps/store-mobile/app/src/test/java/com/store/mobile/scan/*`
- `apps/store-mobile/app/src/test/java/com/store/mobile/ui/runtime/RuntimeStatusScreenTest.kt`
- `apps/store-mobile/README.md`
- `docs/WORKLOG.md`

## Testing

This slice should stay unit-test heavy:

- parser tests for valid/invalid payloads
- view-model tests for rugged-scanner status transitions
- runtime-status builder tests for external scanner labels
- full mobile Gradle unit suite

## Exit Criteria

This slice is complete when:

- rugged-scanner payload success and failure are tracked explicitly
- handheld and tablet scan screens expose external-scanner posture
- runtime status exposes external-scanner posture
- README documents expected `DataWedge` action/payload setup
- verification is green through the normal mobile Gradle path
