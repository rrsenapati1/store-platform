# Store Mobile Zebra DataWedge Provisioning Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Zebra DataWedge profile provisioning and result handling to Store Mobile so Zebra devices can be configured from the app without affecting generic Android devices.

**Architecture:** Keep the current generic scan pipeline. Add a small Zebra-only configurator that builds DataWedge `SET_CONFIG` intents and parses result intents, wire `MainActivity` to send those intents and receive results, then mirror Zebra setup posture into the existing scan/runtime UI state.

**Tech Stack:** Kotlin, Android `Intent`/`Bundle` APIs, `ComponentActivity`, Jetpack Compose, Gradle unit tests.

---

### Task 1: Add failing tests for the Zebra configurator and provisioning state

**Files:**
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ZebraDataWedgeConfiguratorTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/runtime/RuntimeStatusScreenTest.kt`

- [ ] **Step 1: Add configurator tests for package detection, intent building, and result parsing**
- [ ] **Step 2: Add view-model tests for Zebra provisioning state transitions**
- [ ] **Step 3: Add runtime-status tests for Zebra setup labels**
- [ ] **Step 4: Run the targeted Gradle tests and verify they fail**

### Task 2: Implement the Zebra configurator and result contract

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/ZebraDataWedgeConfigurator.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/ZebraDataWedgeResult.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/ExternalScannerEvent.kt` only if needed for shared command/result modeling

- [ ] **Step 1: Implement the pure configurator helpers**
- [ ] **Step 2: Implement the Zebra result parser**
- [ ] **Step 3: Re-run the targeted tests and make the pure-configurator tests pass**

### Task 3: Wire MainActivity and shared UI state

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/MainActivity.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/StoreMobileApplication.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupViewModel.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`

- [ ] **Step 1: Add Zebra DataWedge availability detection**
- [ ] **Step 2: Add an app-level result bus for Zebra setup results**
- [ ] **Step 3: Send the Zebra `SET_CONFIG` intent from `MainActivity`**
- [ ] **Step 4: Receive `RESULT_ACTION` and publish success/failure events**
- [ ] **Step 5: Mirror Zebra provisioning state into the scan view-model**
- [ ] **Step 6: Re-run the targeted tests and keep them green**

### Task 4: Surface Zebra setup in scan/runtime UI

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/runtime/RuntimeStatusScreen.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`

- [ ] **Step 1: Add Zebra setup card/button to the scan screen**
- [ ] **Step 2: Add Zebra setup posture to runtime status**
- [ ] **Step 3: Wire the configure/retry action from the UI into the activity host**
- [ ] **Step 4: Re-run the targeted tests and keep them green**

### Task 5: Update docs and run full verification

**Files:**
- Modify: `apps/store-mobile/README.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Add Zebra-specific setup notes to the mobile README**
- [ ] **Step 2: Record the slice in the worklog**
- [ ] **Step 3: Run `cd apps/store-mobile && .\\gradlew.bat testDebugUnitTest`**
- [ ] **Step 4: Run `npm run ci:store-mobile`**
- [ ] **Step 5: Run `git diff --check`**
- [ ] **Step 6: Commit docs/implementation separately and push**
