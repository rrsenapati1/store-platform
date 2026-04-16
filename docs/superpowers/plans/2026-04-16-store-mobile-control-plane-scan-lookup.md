# Store Mobile Control-Plane Scan Lookup Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Android runtime's in-memory barcode scan lookup with a real control-plane-backed branch scan lookup that includes replenishment policy fields needed by mobile restock.

**Architecture:** Extend the existing control-plane barcode scan route to return branch policy data, add a remote Android scan lookup repository, and switch only scan lookup over to the remote path in the runtime app.

**Tech Stack:** Python/FastAPI, Pydantic, Kotlin, Android Compose, JDK `HttpURLConnection`, JUnit 4.

---

### Task 1: Enrich Control-Plane Barcode Scan Contract

**Files:**
- Modify: `services/control-plane-api/store_control_plane/schemas/barcode.py`
- Modify: `services/control-plane-api/store_control_plane/services/barcode.py`
- Test: `services/control-plane-api/tests/test_barcode_flow.py`

- [ ] **Step 1: Write the failing backend tests**

Add coverage proving:
- branch scan returns `reorder_point` and `target_stock` when present
- policy fields can be `null`
- not-found behavior remains unchanged

- [ ] **Step 2: Run targeted backend tests to verify they fail**

Run: `python -m pytest services/control-plane-api/tests/test_barcode_flow.py -q`

- [ ] **Step 3: Write minimal backend implementation**

Extend the barcode scan response schema and service mapping to include branch replenishment policy from the branch catalog item.

- [ ] **Step 4: Run targeted backend tests to verify they pass**

Run: `python -m pytest services/control-plane-api/tests/test_barcode_flow.py -q`

### Task 2: Extend Mobile Control-Plane Scan Client

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneModels.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/StoreMobileControlPlaneClient.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/controlplane/StoreMobileControlPlaneClientTest.kt`

- [ ] **Step 1: Write the failing client tests**

Add tests for:
- enriched `catalog-scan` mapping with policy fields
- not-found / null-policy handling at the client boundary

- [ ] **Step 2: Run targeted client tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

- [ ] **Step 3: Write minimal client implementation**

Extend the mobile control-plane scan models and parsing so the Android client returns replenishment policy along with existing scan data.

- [ ] **Step 4: Run targeted client tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest`

### Task 3: Add Remote Scan Lookup Repository

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/RemoteScanLookupRepository.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/RemoteScanLookupRepositoryTest.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt`

- [ ] **Step 1: Write the failing repository tests**

Add tests that verify:
- successful scan lookup mapping
- null-policy mapping
- not-found mapping to the existing nullable repository contract

- [ ] **Step 2: Run targeted repository tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.RemoteScanLookupRepositoryTest`

- [ ] **Step 3: Write minimal repository implementation**

Map enriched control-plane scan responses into `ScanLookupRecord` without changing `ScanLookupViewModel` or scan-screen contracts.

- [ ] **Step 4: Run targeted repository tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.RemoteScanLookupRepositoryTest --tests com.store.mobile.scan.ScanLookupViewModelTest`

### Task 4: Switch Scan Lookup App Wiring

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Test: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/StoreMobileRuntimeContextTest.kt`

- [ ] **Step 1: Write the failing wiring tests**

Add or extend tests to prove scan lookup repository selection uses runtime session/device context and only uses in-memory scan data in unpaired/demo mode.

- [ ] **Step 2: Run targeted wiring tests to verify they fail**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest`

- [ ] **Step 3: Write minimal app wiring**

Build the remote scan lookup repository from paired device + session and switch only scan lookup to that remote path.

- [ ] **Step 4: Run targeted wiring tests to verify they pass**

Run: `cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest`

### Task 5: Verify And Record

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Run targeted verification**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_barcode_flow.py -q
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest --tests com.store.mobile.controlplane.StoreMobileControlPlaneClientTest --tests com.store.mobile.scan.RemoteScanLookupRepositoryTest --tests com.store.mobile.scan.ScanLookupViewModelTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest
```

- [ ] **Step 2: Run full mobile verification**

Run:

```bash
cd apps/store-mobile && .\gradlew.bat testDebugUnitTest
npm run ci:store-mobile
git -c core.safecrlf=false diff --check
```

- [ ] **Step 3: Update worklog**

Record that paired mobile/tablet scan lookup is now control-plane-backed and no longer depends on demo product data.
