# Store Mobile External Scanner Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Android external scanner support to the shared Store Mobile app through DataWedge-style broadcast input and HID/USB wedge-friendly scan-screen behavior.

**Architecture:** Keep one Android app and one lookup pipeline. Add a bounded external scanner integration layer that parses broadcast payloads and routes them into the existing `ScanLookupViewModel`, while the scan screen becomes focus-ready for HID/USB wedge scanners instead of introducing a second scanning stack.

**Tech Stack:** Kotlin, Android ComponentActivity/Application, Jetpack Compose, existing mobile scan view model, Gradle unit tests.

---

### Task 1: Add failing tests for external scanner parsing and routing

**Files:**
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ExternalBarcodeScanParserTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ExternalBarcodeScanParserTest.kt`

- [ ] **Step 1: Write the failing parser tests**
- [ ] **Step 2: Extend the view-model tests with an external-scanner source case**
- [ ] **Step 3: Run `testDebugUnitTest` for those tests and verify they fail for missing parser/source behavior**
- [ ] **Step 4: Commit the red tests once the failure is correct**

### Task 2: Implement the external scanner parser and app-level event bus

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/ExternalBarcodeScanParser.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/StoreMobileApplication.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/MainActivity.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupViewModel.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ExternalBarcodeScanParserTest.kt`

- [ ] **Step 1: Implement the minimal parser to satisfy the failing parser tests**
- [ ] **Step 2: Add an application-level listener/emit boundary for external barcode events**
- [ ] **Step 3: Wire `MainActivity` to receive scanner broadcasts and emit parsed barcodes**
- [ ] **Step 4: Extend `ScanLookupViewModel` with `EXTERNAL_SCANNER` routing**
- [ ] **Step 5: Re-run the targeted Gradle tests and make them pass**
- [ ] **Step 6: Commit the green parser/app-event changes**

### Task 3: Make the scan screen wedge-friendly and consume external scanner events

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsContent.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldStoreShell.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/tablet/InventoryTabletShell.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt`

- [ ] **Step 1: Subscribe the app shell to external scanner events and forward them into the shared view model**
- [ ] **Step 2: Add focus-ready HID/USB wedge handling to the scan field using hardware Enter submission**
- [ ] **Step 3: Expose scanner-support hints/source labeling in handheld and tablet scan layouts**
- [ ] **Step 4: Run the targeted Gradle tests again and keep them green**
- [ ] **Step 5: Commit the UI/runtime integration**

### Task 4: Update docs and run full mobile verification

**Files:**
- Modify: `apps/store-mobile/README.md`
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`

- [ ] **Step 1: Document the external scanner posture in the mobile README**
- [ ] **Step 2: Record the slice in the worklog**
- [ ] **Step 3: Keep the ledger on `V2-002` and note the new progress**
- [ ] **Step 4: Run `cd apps/store-mobile && .\\gradlew.bat testDebugUnitTest`**
- [ ] **Step 5: Run `npm run ci:store-mobile`**
- [ ] **Step 6: Run `git diff --check`**
- [ ] **Step 7: Commit docs and any final cleanup, then push**
