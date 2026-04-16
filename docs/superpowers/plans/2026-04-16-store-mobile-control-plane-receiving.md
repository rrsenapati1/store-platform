# Store Mobile Control-Plane Receiving Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Android runtime's in-memory reviewed receiving flow with a real control-plane-backed receiving workflow, using paired runtime tenant/branch context and existing control-plane purchasing/inventory routes.

**Architecture:** Add a control-plane purchase-order detail route using the existing purchasing response shape, extend the Android control-plane client for receiving, add a remote receiving repository, and wire only the receiving workflow over to the remote path.

**Tech Stack:** Python/FastAPI, Kotlin, Android Compose, JDK `HttpURLConnection`, JUnit 4.

---

### Task 1: Add Purchase Order Detail Read

**Files:**
- Modify: `services/control-plane-api/store_control_plane/routes/purchasing.py`
- Modify: `services/control-plane-api/store_control_plane/services/purchasing.py`
- Test: `services/control-plane-api/tests/test_procurement_finance_flow.py`

- [ ] **Step 1: Write the failing backend test**

Add a test that reads a branch purchase order by id and asserts the response includes line detail in the existing `PurchaseOrderResponse` shape.

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `python -m pytest services/control-plane-api/tests/test_procurement_finance_flow.py -q`

- [ ] **Step 3: Write minimal backend implementation**

Add:
- `PurchasingService.get_purchase_order(...)`
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}`

Reuse `_purchase_order_response(...)`.

- [ ] **Step 4: Run the targeted backend test to verify it passes**

Run: `python -m pytest services/control-plane-api/tests/test_procurement_finance_flow.py -q`

### Task 2: Extend Mobile Control-Plane Client For Receiving

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneModels.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneClient.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/controlplane/StoreMobileControlPlaneClientTest.kt`

- [ ] **Step 1: Write the failing client tests**

Add tests for:
- receiving-board path mapping
- purchase-order detail path mapping
- goods-receipt create payload mapping

- [ ] **Step 2: Run targeted client tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

- [ ] **Step 3: Write minimal implementation**

Add receiving and purchasing models plus:
- `getReceivingBoard`
- `getPurchaseOrder`
- `listGoodsReceipts`
- `createGoodsReceipt`

- [ ] **Step 4: Run targeted client tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

### Task 3: Add Remote Receiving Repository

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/operations/RemoteReceivingRepository.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/operations/ReceivingRepository.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/RemoteReceivingRepositoryTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/ReceivingRepositoryTest.kt`

- [ ] **Step 1: Write the failing repository tests**

Add tests that verify:
- receiving board mapping
- approved purchase order detail mapping into `ReceivingDraft`
- goods receipt creation + latest receipt mapping

- [ ] **Step 2: Run targeted repository tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.RemoteReceivingRepositoryTest`

- [ ] **Step 3: Write minimal repository implementation**

Map control-plane models into the existing receiving domain contract without changing the screen contract.

- [ ] **Step 4: Run targeted repository tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.RemoteReceivingRepositoryTest --tests com.store.mobile.operations.ReceivingRepositoryTest`

### Task 4: Switch Receiving App Wiring

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/StoreMobileRuntimeContextTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/operations/ReceivingViewModelTest.kt`

- [ ] **Step 1: Write the failing wiring tests**

Add/extend tests to prove receiving repository selection uses runtime session/device context and no longer depends on in-memory receiving when paired context is present.

- [ ] **Step 2: Run targeted tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest --tests com.store.mobile.ui.operations.ReceivingViewModelTest`

- [ ] **Step 3: Write minimal app wiring**

Build remote receiving repository from paired device + session and switch only receiving to that remote path.

- [ ] **Step 4: Run targeted tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest --tests com.store.mobile.ui.operations.ReceivingViewModelTest`

### Task 5: Verify And Record

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Run targeted verification**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_procurement_finance_flow.py -q
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest --tests com.store.mobile.operations.RemoteReceivingRepositoryTest --tests com.store.mobile.operations.ReceivingRepositoryTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest --tests com.store.mobile.ui.operations.ReceivingViewModelTest
```

- [ ] **Step 2: Run full mobile verification**

Run:

```bash
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest
npm run ci:store-mobile
git -c core.safecrlf=false diff --check
```

- [ ] **Step 3: Update worklog**

Record that reviewed receiving is now the second real control-plane-backed Store Mobile / Inventory Tablet workflow.
