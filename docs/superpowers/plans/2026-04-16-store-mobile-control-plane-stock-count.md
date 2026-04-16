# Store Mobile Control-Plane Stock Count Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Android runtime's in-memory reviewed stock-count workflow with the first real control-plane-backed branch-operations slice, using paired runtime context instead of `DEMO_BRANCH_ID`.

**Architecture:** Extend mobile pairing/runtime context with `tenantId` and `branchId`, add a small HTTP control-plane client, and swap stock-count to a remote repository while keeping the existing view-model and screen contract mostly stable. Other operations remain local for now, but branch loading should stop using hardcoded constants.

**Tech Stack:** Kotlin, Android Compose, JDK `HttpURLConnection`, existing mobile runtime/session models, existing control-plane inventory routes, JUnit 4.

---

### Task 1: Extend Runtime Context

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileModels.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePairingRepository.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileHubClient.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingViewModel.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobilePairingRepositoryTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/pairing/PairingViewModelTest.kt`

- [ ] **Step 1: Write the failing tests**

Add assertions that paired-device persistence and redeemed runtime sessions carry `tenantId` and `branchId`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.runtime.StoreMobilePairingRepositoryTest --tests com.store.mobile.ui.pairing.PairingViewModelTest`

Expected: FAIL with missing constructor fields or missing persisted values.

- [ ] **Step 3: Write minimal implementation**

Add `tenantId` and `branchId` to:
- `StoreMobilePairedDevice`
- `StoreMobileRuntimeSession`

Persist them in `InMemoryStoreMobilePairingRepository`, return them from `FakeStoreMobileHubClient`, and wire them through `PairingViewModel`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.runtime.StoreMobilePairingRepositoryTest --tests com.store.mobile.ui.pairing.PairingViewModelTest`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileModels.kt apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePairingRepository.kt apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileHubClient.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingViewModel.kt apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobilePairingRepositoryTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/ui/pairing/PairingViewModelTest.kt
git commit -m "feat: add mobile runtime tenant and branch context"
```

### Task 2: Add Mobile Control-Plane Client

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneClient.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneModels.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneException.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/controlplane/StoreMobileControlPlaneClientTest.kt`

- [ ] **Step 1: Write the failing tests**

Add tests that verify:
- correct stock-count and inventory-snapshot paths
- bearer token header usage
- JSON payload parsing into typed client models

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

Expected: FAIL because the client and models do not exist.

- [ ] **Step 3: Write minimal implementation**

Implement a small client using JDK HTTP that can:
- `getInventorySnapshot`
- `getStockCountBoard`
- `createStockCountSession`
- `recordStockCountSession`
- `approveStockCountSession`
- `cancelStockCountSession`

Use exact control-plane route shapes already present in `services/control-plane-api/store_control_plane/routes/inventory.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/store-mobile/app/src/main/java/com/store/mobile/controlplane apps/store-mobile/app/src/test/java/com/store/mobile/controlplane/StoreMobileControlPlaneClientTest.kt
git commit -m "feat: add mobile control-plane stock-count client"
```

### Task 3: Add Remote Stock Count Repository

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/operations/StockCountRepository.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/operations/RemoteStockCountRepository.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/RemoteStockCountRepositoryTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/StockCountRepositoryTest.kt`

- [ ] **Step 1: Write the failing tests**

Add repository tests that verify:
- inventory snapshot maps into `StockCountContext`
- stock-count board maps into `StockCountBoard`
- create/record/approve/cancel lifecycle maps into existing mobile domain objects

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.RemoteStockCountRepositoryTest`

Expected: FAIL because the remote repository does not exist.

- [ ] **Step 3: Write minimal implementation**

Keep `StockCountRepository` as the boundary. Add `RemoteStockCountRepository` that takes:
- control-plane client
- runtime session
- runtime paired-device context

Map the remote models into the existing stock-count domain contract without changing the screen.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.RemoteStockCountRepositoryTest --tests com.store.mobile.operations.StockCountRepositoryTest`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/store-mobile/app/src/main/java/com/store/mobile/operations/StockCountRepository.kt apps/store-mobile/app/src/main/java/com/store/mobile/operations/RemoteStockCountRepository.kt apps/store-mobile/app/src/test/java/com/store/mobile/operations/RemoteStockCountRepositoryTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/operations/StockCountRepositoryTest.kt
git commit -m "feat: add remote mobile stock-count repository"
```

### Task 4: Switch App Wiring To Runtime Context

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/StockCountViewModel.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/StockCountScreen.kt` (only if contract changes are unavoidable)
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/operations/StockCountViewModelTest.kt`

- [ ] **Step 1: Write the failing tests**

Add or extend tests to prove stock-count loads from runtime `branchId` and no longer depends on `DEMO_BRANCH_ID`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.operations.StockCountViewModelTest`

Expected: FAIL because app wiring still uses in-memory repo or demo branch assumptions.

- [ ] **Step 3: Write minimal implementation**

In `StoreMobileApp.kt`:
- remove stock-count dependency on `DEMO_BRANCH_ID`
- build a remote stock-count repo from paired session + paired device
- load stock-count branch context from runtime `branchId`

For now, receiving/restock/expiry can still use local repositories, but their `loadBranch` calls should use runtime `branchId` too if available.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.operations.StockCountViewModelTest`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/StockCountViewModel.kt apps/store-mobile/app/src/test/java/com/store/mobile/ui/operations/StockCountViewModelTest.kt
git commit -m "feat: wire mobile stock count to control plane"
```

### Task 5: Verify And Record The Slice

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Run targeted tests**

Run:

```bash
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.runtime.StoreMobilePairingRepositoryTest --tests com.store.mobile.ui.pairing.PairingViewModelTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest --tests com.store.mobile.operations.RemoteStockCountRepositoryTest --tests com.store.mobile.ui.operations.StockCountViewModelTest
```

Expected: PASS.

- [ ] **Step 2: Run full Android verification**

Run:

```bash
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest
npm run ci:store-mobile
git -c core.safecrlf=false diff --check
```

Expected: PASS, PASS, and no diff-check output.

- [ ] **Step 3: Update worklog**

Record that `V2-004` now includes the first real control-plane-backed mobile/tablet workflow via reviewed stock-count execution.

- [ ] **Step 4: Commit**

```bash
git add docs/WORKLOG.md
git commit -m "docs: record mobile control-plane stock-count slice"
```
