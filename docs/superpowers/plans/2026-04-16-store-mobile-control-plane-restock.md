# Store Mobile Control-Plane Restock Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Android runtime's in-memory assisted restock flow with a real control-plane-backed restock workflow using paired runtime tenant/branch context and existing control-plane restock routes.

**Architecture:** Extend the Android control-plane client for restock board/task calls, add a remote restock repository, and switch only restock over to the remote path in the runtime app.

**Tech Stack:** Kotlin, Android Compose, JDK `HttpURLConnection`, existing inventory control-plane routes, JUnit 4.

---

### Task 1: Extend Mobile Control-Plane Client For Restock

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneModels.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneClient.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/controlplane/StoreMobileControlPlaneClientTest.kt`

- [ ] **Step 1: Write the failing client tests**

Add tests for:
- `restock-board` path and mapping
- create/pick/complete/cancel request and response mapping

- [ ] **Step 2: Run targeted client tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

- [ ] **Step 3: Write minimal implementation**

Add restock models plus:
- `getRestockBoard`
- `createRestockTask`
- `pickRestockTask`
- `completeRestockTask`
- `cancelRestockTask`

- [ ] **Step 4: Run targeted client tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

### Task 2: Add Remote Restock Repository

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/operations/RemoteRestockRepository.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/RemoteRestockRepositoryTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/RestockRepositoryTest.kt`

- [ ] **Step 1: Write the failing repository tests**

Add tests that verify:
- restock board mapping
- create/pick/complete/cancel lifecycle mapping

- [ ] **Step 2: Run targeted repository tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.RemoteRestockRepositoryTest`

- [ ] **Step 3: Write minimal repository implementation**

Map control-plane restock models into the existing Android restock domain contract without changing the screen contract.

- [ ] **Step 4: Run targeted repository tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.RemoteRestockRepositoryTest --tests com.store.mobile.operations.RestockRepositoryTest`

### Task 3: Switch Restock App Wiring

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/StoreMobileRuntimeContextTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/operations/RestockViewModelTest.kt`

- [ ] **Step 1: Write the failing wiring tests**

Add/extend tests to prove restock repository selection uses runtime session/device context and no longer depends on in-memory restock when paired context is present.

- [ ] **Step 2: Run targeted tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest --tests com.store.mobile.ui.operations.RestockViewModelTest`

- [ ] **Step 3: Write minimal app wiring**

Build remote restock repository from paired device + session and switch only restock to that remote path.

- [ ] **Step 4: Run targeted tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest --tests com.store.mobile.ui.operations.RestockViewModelTest`

### Task 4: Verify And Record

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Run targeted verification**

Run:

```bash
C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_restock_flow.py -q
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest --tests com.store.mobile.operations.RemoteRestockRepositoryTest --tests com.store.mobile.operations.RestockRepositoryTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest --tests com.store.mobile.ui.operations.RestockViewModelTest
```

- [ ] **Step 2: Run full mobile verification**

Run:

```bash
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest
npm run ci:store-mobile
git -c core.safecrlf=false diff --check
```

- [ ] **Step 3: Update worklog**

Record that assisted restock is now the fourth real control-plane-backed Store Mobile / Inventory Tablet workflow.
