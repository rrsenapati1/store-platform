# Store Mobile Zebra DataWedge Provisioning Design

## Context

Store Mobile already supports:

- camera scanning
- manual entry
- generic external scanner broadcasts
- HID/USB wedge input
- rugged-scanner diagnostics

The next bounded `V2-002` slice is the first real vendor-specific integration beyond the generic broadcast path. Because the user wants to start with low setup cost but still support Zebra if it is available, the right slice is not a full OEM abstraction. It is a Zebra-specific DataWedge provisioning lane that makes Zebra devices easier to deploy without affecting generic Android phones/tablets.

Zebra’s official TechDocs say:

- DataWedge is pre-installed on Zebra Android devices
- DataWedge can be configured programmatically with the `SET_CONFIG` intent API
- result codes can be received through `com.symbol.datawedge.api.RESULT_ACTION` when `SEND_RESULT` and `COMMAND_IDENTIFIER` are set

Sources:
- [About DataWedge](https://techdocs.zebra.com/datawedge/latest/guide/about/)
- [SET_CONFIG](https://techdocs.zebra.com/datawedge/14-1/guide/api/setconfig)
- [Intent Result Codes](https://techdocs.zebra.com/datawedge/11-3/guide/api/resultinfo/)

## Product Decision

Add a Zebra-only provisioning path to the existing Android app:

- detect whether DataWedge is present
- offer one-tap configuration from Store Mobile
- configure a Store Mobile DataWedge profile for broadcast output
- disable DataWedge keystroke output in that managed profile to avoid duplicate scan paths
- listen for Zebra result intents and surface configuration success/failure in the UI

This slice remains optional and non-blocking:

- generic devices continue using camera/manual/HID paths
- Zebra devices gain a lower-friction setup path

## Goals

- zero subscription cost
- no backend changes
- easier Zebra deployment in India or elsewhere if those devices are used
- explicit Zebra setup status in scan/runtime UI
- no impact on generic Android devices

## Non-Goals

- Honeywell/Datalogic/Sunmi support in this slice
- full OEM abstraction layer
- deep scanner trigger APIs
- device fleet management

## Architecture

### Zebra configurator

Add a small pure Kotlin configurator module that:

- checks if the DataWedge package is installed
- builds a `SET_CONFIG` intent for Store Mobile’s package/activity
- builds the matching command identifier
- parses Zebra result intents into a bounded success/failure contract

The profile should:

- associate Store Mobile’s package/activity
- enable Intent Output using the app’s existing broadcast action
- set intent delivery to broadcast
- disable Keystroke Output in the Zebra-managed profile to avoid duplicate character injection

### Activity boundary

`MainActivity` should remain the Android integration point:

- register for `com.symbol.datawedge.api.RESULT_ACTION`
- send the provisioning intent when the UI requests Zebra setup
- emit Zebra configuration result events into the app-level bus

### Shared UI state

The scan/runtime layer should gain a Zebra-specific provisioning state:

- `UNAVAILABLE`
- `AVAILABLE`
- `APPLYING`
- `CONFIGURED`
- `ERROR`

This state is independent from the generic external-scanner diagnostics. Generic external-scanner status tells operators whether broadcast scans are arriving. Zebra provisioning state tells them whether the app has successfully configured the Zebra profile.

## UX

### Scan screen

When Zebra DataWedge is available:

- show a small Zebra setup card
- show one-tap `Configure Zebra DataWedge`
- if setup fails, show `Retry Zebra setup`
- if setup succeeds, show `Zebra DataWedge configured`

When Zebra is unavailable:

- do not show Zebra-specific setup controls

### Runtime status

Add Zebra setup posture:

- `Zebra scanner setup unavailable`
- `Zebra DataWedge available`
- `Zebra DataWedge setup in progress`
- `Zebra DataWedge configured`
- `Zebra DataWedge setup failed`

This makes support triage easier without exposing OEM-specific clutter on generic devices.

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

- configurator intent-builder tests
- configurator result-parser tests
- view-model tests for Zebra provisioning state transitions
- runtime-status tests for Zebra labels
- full mobile Gradle unit suite

## Exit Criteria

This slice is complete when:

- Store Mobile can detect Zebra/DataWedge availability
- the app can send a DataWedge `SET_CONFIG` intent for its own profile
- Zebra result intents update UI posture
- the scan screen and runtime status expose Zebra setup state
- generic devices remain unaffected
