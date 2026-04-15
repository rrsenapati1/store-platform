# Store Mobile Rugged Scanner Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit rugged-scanner diagnostics and support visibility to the shared Android Store Mobile runtime without changing backend authority or introducing vendor SDK integrations.

**Architecture:** Keep one shared Android scan pipeline. Upgrade the external-scanner event boundary from plain barcode strings to typed success/error events, mirror rugged-scanner diagnostics into the existing scan/runtime UI state, and expose that posture in both the scan screen and the runtime status screen.

**Tech Stack:** Kotlin, Android `ComponentActivity`/`Application`, Jetpack Compose, existing mobile scan view-model, Gradle unit tests.

---

### Task 1: Add failing tests for rugged scanner diagnostics

**Files:**
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ExternalBarcodeScanParserTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/runtime/RuntimeStatusScreenTest.kt`

- [ ] **Step 1: Extend parser tests with malformed-payload coverage**
- [ ] **Step 2: Extend view-model tests for external-scanner status transitions**
- [ ] **Step 3: Extend runtime-status tests for scanner posture labels**
- [ ] **Step 4: Run the targeted Gradle tests and verify they fail for the missing diagnostics behavior**

### Task 2: Implement typed rugged-scanner events and diagnostics state

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/ExternalBarcodeScanParser.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/ExternalScannerEvent.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/StoreMobileApplication.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/MainActivity.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupViewModel.kt`

- [ ] **Step 1: Make the parser return typed success/error results instead of only strings**
- [ ] **Step 2: Add the shared rugged-scanner diagnostics model**
- [ ] **Step 3: Upgrade the app event bus to emit typed scanner events**
- [ ] **Step 4: Update the scan view-model to track rugged-scanner posture**
- [ ] **Step 5: Re-run the targeted tests and make them pass**

### Task 3: Surface rugged-scanner posture in scan/runtime UI

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/runtime/RuntimeStatusScreen.kt`

- [ ] **Step 1: Subscribe the app shell to typed scanner events and update both lookup and diagnostics state**
- [ ] **Step 2: Add a compact rugged-scanner status card to the scan screen**
- [ ] **Step 3: Extend runtime status to show rugged-scanner readiness, last scan, and latest warning**
- [ ] **Step 4: Re-run the targeted tests and keep them green**

### Task 4: Document the rugged-device setup and verify the full mobile suite

**Files:**
- Modify: `apps/store-mobile/README.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Document expected `DataWedge` setup in the mobile README**
- [ ] **Step 2: Record the rugged-scanner diagnostics slice in the worklog**
- [ ] **Step 3: Run `cd apps/store-mobile && .\\gradlew.bat testDebugUnitTest`**
- [ ] **Step 4: Run `npm run ci:store-mobile`**
- [ ] **Step 5: Run `git diff --check`**
- [ ] **Step 6: Commit docs/implementation separately and push**
