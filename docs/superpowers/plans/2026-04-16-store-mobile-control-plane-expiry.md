# Store Mobile Control-Plane Expiry Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Android runtime's in-memory reviewed expiry flow with a real control-plane-backed batch-expiry workflow using paired runtime tenant/branch context and existing control-plane batch routes.

**Architecture:** Extend the Android control-plane client for batch-expiry report/board/session calls, add a remote expiry repository, and switch only expiry over to the remote path in the runtime app.

**Tech Stack:** Kotlin, Android Compose, JDK `HttpURLConnection`, existing batch control-plane routes, JUnit 4.

---

### Task 1: Extend Mobile Control-Plane Client For Expiry

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneModels.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneClient.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/controlplane/StoreMobileControlPlaneClientTest.kt`

- [ ] **Step 1: Write the failing client tests**

Add tests for:
- `batch-expiry-report` path and mapping
- `batch-expiry-board` path and mapping
- reviewed expiry review / approval request and response mapping

- [ ] **Step 2: Run targeted client tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

- [ ] **Step 3: Write minimal implementation**

Add batch-expiry models plus:
- `getBatchExpiryReport`
- `getBatchExpiryBoard`
- `createBatchExpirySession`
- `recordBatchExpirySessionReview`
- `approveBatchExpirySession`
- `cancelBatchExpirySession`

- [ ] **Step 4: Run targeted client tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

### Task 2: Add Remote Expiry Repository

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/operations/RemoteExpiryRepository.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/RemoteExpiryRepositoryTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/ExpiryRepositoryTest.kt`

- [ ] **Step 1: Write the failing repository tests**

Add tests that verify:
- expiry report mapping
- expiry board mapping
- reviewed expiry session lifecycle mapping

- [ ] **Step 2: Run targeted repository tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.RemoteExpiryRepositoryTest`

- [ ] **Step 3: Write minimal repository implementation**

Map control-plane batch-expiry models into the existing Android expiry domain contract without changing the screen contract.

- [ ] **Step 4: Run targeted repository tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.RemoteExpiryRepositoryTest --tests com.store.mobile.operations.ExpiryRepositoryTest`

### Task 3: Switch Expiry App Wiring

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/StoreMobileRuntimeContextTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/operations/ExpiryViewModelTest.kt`

- [ ] **Step 1: Write the failing wiring tests**

Add/extend tests to prove expiry repository selection uses runtime session/device context and no longer depends on in-memory expiry when paired context is present.

- [ ] **Step 2: Run targeted tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest --tests com.store.mobile.ui.operations.ExpiryViewModelTest`

- [ ] **Step 3: Write minimal app wiring**

Build remote expiry repository from paired device + session and switch only expiry to that remote path.

- [ ] **Step 4: Run targeted tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest --tests com.store.mobile.ui.operations.ExpiryViewModelTest`

### Task 4: Verify And Record

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Run targeted verification**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_batch_expiry_flow.py -q
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest --tests com.store.mobile.operations.RemoteExpiryRepositoryTest --tests com.store.mobile.operations.ExpiryRepositoryTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest --tests com.store.mobile.ui.operations.ExpiryViewModelTest
```

- [ ] **Step 2: Run full mobile verification**

Run:

```bash
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest
npm run ci:store-mobile
git -c core.safecrlf=false diff --check
```

- [ ] **Step 3: Update worklog**

Record that reviewed expiry is now the third real control-plane-backed Store Mobile / Inventory Tablet workflow.
