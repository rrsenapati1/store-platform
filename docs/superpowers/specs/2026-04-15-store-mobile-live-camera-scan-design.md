# Store Mobile Live Camera Scan Design

Date: 2026-04-15  
Owner: Codex  
Status: Draft

## Goal

Replace the current manual-entry-only mobile scan posture with real live camera preview scanning in the existing Android `store-mobile` app for both handheld and inventory-tablet shells.

## Product Decision

The first live camera scan slice will:

- stay inside `apps/store-mobile`
- use `CameraX + ML Kit barcode scanning`
- support both `mobile_store_spoke` and `inventory_tablet_spoke`
- keep manual barcode entry as fallback
- reuse the existing lookup/result path instead of inventing a separate scan domain

This slice does not introduce rugged-device vendor scanner SDKs yet.

## Scope

Included:

- live camera preview in the scan section
- on-device barcode analysis with ML Kit
- scanner cooldown and duplicate-detection protection
- camera permission handling
- shared scanner session state for handheld and tablet
- shell-specific scan layouts over the same scanner pipeline
- manual-entry fallback when preview is unavailable or permission is denied

Deferred:

- Zebra/Sunmi/DataWedge-style vendor integrations
- background/bulk scanning workflows
- billing-specific scan authority changes
- any new backend contracts

## Architecture

The scanner pipeline should stay shared and Android-native.

### Shared scanner layer

`CameraBarcodeScanner` becomes the scanner session utility boundary.

It should own:

- barcode normalization
- duplicate detection cooldown
- scan acceptance rules for live preview

It should remain testable without requiring a camera device.

### Preview binding layer

A dedicated Compose/Android layer should bind:

- CameraX preview
- CameraX image analysis
- ML Kit barcode decoding

This layer should forward accepted barcode strings into the existing lookup/view-model path and should dispose cleanly when the scan screen is no longer visible.

### Shared lookup layer

`ScanLookupViewModel` stays the place that converts a detected barcode into lookup state.

The same business lookup path must be used for:

- camera detections
- manual text entry

That keeps scan behavior consistent regardless of input source.

### Shell/UI split

Handheld and tablet continue to share lookup/scanner state, but render different layouts:

- handheld: vertical scan-first layout
- tablet: wider preview and result panel arrangement

## UX

The scan section should expose a small, explicit state model:

- camera permission required
- camera preview loading
- scanning
- barcode detected
- lookup result
- lookup miss
- camera unavailable/fallback

The UI should keep manual barcode entry available in every state where the camera path is unavailable or undesirable.

## Files

Main Android files:

- `apps/store-mobile/app/build.gradle.kts`
- `apps/store-mobile/app/src/main/java/com/store/mobile/scan/CameraBarcodeScanner.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/CameraBarcodePreview.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupViewModel.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsContent.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldStoreShell.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/tablet/InventoryTabletShell.kt`
- `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`

Tests:

- `apps/store-mobile/app/src/test/java/com/store/mobile/scan/CameraBarcodeScannerTest.kt`
- `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt`

## Testing

Required coverage:

- scanner normalization and cooldown behavior
- view-model camera state transitions
- detected barcode flowing into lookup result state
- existing mobile/tablet unit tests remain green

Verification should use the existing Gradle unit-test path plus the repo `ci:store-mobile` entrypoint.

## Exit Criteria

This slice is complete when:

- both handheld and tablet scan sections show live camera preview
- detected barcodes populate the existing lookup state
- permission denial and camera-unavailable cases degrade cleanly to manual entry
- the Android app still passes its existing mobile runtime verification path
