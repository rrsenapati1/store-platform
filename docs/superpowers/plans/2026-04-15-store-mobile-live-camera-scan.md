# Store Mobile Live Camera Scan Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real live camera-preview barcode scanning to the existing Android `store-mobile` app for both handheld and tablet shells while keeping manual lookup as fallback.

**Architecture:** Introduce a shared Android-native `CameraX + ML Kit` preview pipeline, keep scanner normalization/cooldown logic in a testable utility, and route all detections through the existing `ScanLookupViewModel` lookup path. Handheld and tablet keep different scan layouts, but share the same scanner state and lookup behavior.

**Tech Stack:** Android/Kotlin, Jetpack Compose, CameraX, ML Kit barcode scanning, existing `store-mobile` app modules

---

### Task 1: Add Scanner Utility Tests And Shared Camera State

**Files:**
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/CameraBarcodeScannerTest.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/CameraBarcodeScanner.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupViewModel.kt`

- [ ] **Step 1: Write the failing scanner utility tests**

Add tests for:

- barcode normalization
- duplicate cooldown rejection
- accepting a new barcode after cooldown expires

- [ ] **Step 2: Run the scanner test to verify it fails**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.CameraBarcodeScannerTest
```

Expected: FAIL because the utility behavior does not exist yet.

- [ ] **Step 3: Implement the minimal shared scanner utility and view-model state**

Add:

- scan cooldown tracking
- camera/session state in `ScanLookupViewModel`
- dedicated methods for permission result, preview start, preview error, and camera-detected barcode handling

- [ ] **Step 4: Re-run the scanner utility test**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.CameraBarcodeScannerTest
```

Expected: PASS

- [ ] **Step 5: Commit the scanner utility slice**

```powershell
git add apps/store-mobile/app/src/main/java/com/store/mobile/scan/CameraBarcodeScanner.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupViewModel.kt apps/store-mobile/app/src/test/java/com/store/mobile/scan/CameraBarcodeScannerTest.kt
git commit -m "feat: add mobile scanner session state"
```

### Task 2: Add CameraX And ML Kit Preview Binding

**Files:**
- Modify: `apps/store-mobile/app/build.gradle.kts`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/CameraBarcodePreview.kt`

- [ ] **Step 1: Write the failing view-model test for camera detections**

Extend `ScanLookupViewModelTest.kt` with a case proving a detected barcode updates the lookup result and camera state.

- [ ] **Step 2: Run the view-model test to verify it fails**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.ScanLookupViewModelTest
```

Expected: FAIL because the view-model does not yet handle live camera detections.

- [ ] **Step 3: Implement the minimal preview binding layer**

Add:

- CameraX/ML Kit dependencies
- Compose preview binding component
- analyzer hookup that forwards accepted detections into the view-model callback

- [ ] **Step 4: Re-run the view-model test**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.ScanLookupViewModelTest
```

Expected: PASS

- [ ] **Step 5: Commit the preview binding slice**

```powershell
git add apps/store-mobile/app/build.gradle.kts apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/CameraBarcodePreview.kt apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt
git commit -m "feat: add mobile camera preview binding"
```

### Task 3: Upgrade Scan UI For Handheld And Tablet

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsContent.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldStoreShell.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/tablet/InventoryTabletShell.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`

- [ ] **Step 1: Write the failing app-shell test if needed, otherwise extend the scan view-model test expectations**

Add an expectation proving the scan state can move into `SCANNING` and then `BARCODE_DETECTED`.

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.ScanLookupViewModelTest
```

Expected: FAIL because the UI state path is still incomplete.

- [ ] **Step 3: Implement the handheld/tablet scan UI**

Add:

- live preview surface in the scan screen
- shell-specific layout differences for handheld vs tablet
- manual entry fallback and status copy
- state wiring from `StoreMobileApp`

- [ ] **Step 4: Re-run the targeted test**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.ScanLookupViewModelTest
```

Expected: PASS

- [ ] **Step 5: Commit the scan UI slice**

```powershell
git add apps/store-mobile/app/src/main/java/com/store/mobile/ui
git commit -m "feat: add live camera scan UI"
```

### Task 4: Update Docs And Run Full Mobile Verification

**Files:**
- Modify: `apps/store-mobile/README.md`
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md` (only if wording needs progress detail)

- [ ] **Step 1: Update docs for the live camera-preview slice**

Document that live camera scan is now implemented and customer-display is no longer the next remaining `V2-001` runtime-surface gap.

- [ ] **Step 2: Run the full mobile verification stack**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest
Set-Location ..\..
npm run ci:store-mobile
git diff --check
```

Expected: PASS

- [ ] **Step 3: Commit the completed live camera slice**

```powershell
git add apps/store-mobile docs
git commit -m "feat: add store mobile live camera scanning"
```
