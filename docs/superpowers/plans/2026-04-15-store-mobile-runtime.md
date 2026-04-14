# Store Mobile Runtime Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Android-only, Kotlin-native `store-mobile` app slice for pairing, staff unlock, camera scan/lookup, and receiving/count/expiry workflows as a `mobile_store_spoke`.

**Architecture:** Create a new `apps/store-mobile/` Android project that pairs to the existing branch hub as `mobile_store_spoke`, uses bounded control-plane/hub contracts, and keeps billing/payment authority out of mobile. Backend changes should be minimal and focused on generic mobile runtime activation/session support rather than inventing a second mobile-only auth model.

**Tech Stack:** Android/Kotlin, Jetpack Compose, Gradle, CameraX/ML Kit barcode scanning, existing FastAPI control plane, existing hub/spoke runtime contracts

---

### Task 1: Scaffold `apps/store-mobile` As An Android-First Kotlin App

**Files:**
- Create: `apps/store-mobile/settings.gradle.kts`
- Create: `apps/store-mobile/build.gradle.kts`
- Create: `apps/store-mobile/gradle.properties`
- Create: `apps/store-mobile/app/build.gradle.kts`
- Create: `apps/store-mobile/app/proguard-rules.pro`
- Create: `apps/store-mobile/app/src/main/AndroidManifest.xml`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/MainActivity.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/StoreMobileApplication.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Create: `apps/store-mobile/app/src/main/res/values/strings.xml`
- Create: `apps/store-mobile/app/src/main/res/values/themes.xml`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/StoreMobileAppBootstrapTest.kt`
- Create: `apps/store-mobile/README.md`
- Modify: `.gitignore`
- Modify: `README.md`

- [ ] **Step 1: Write the failing bootstrap test**

Create `apps/store-mobile/app/src/test/java/com/store/mobile/StoreMobileAppBootstrapTest.kt`:

```kotlin
package com.store.mobile

import org.junit.Assert.assertEquals
import org.junit.Test

class StoreMobileAppBootstrapTest {
    @Test
    fun exposesMobileRuntimeAppName() {
        assertEquals("Store Mobile", StoreMobileAppBootstrap.appName)
    }
}
```

- [ ] **Step 2: Run the Android unit test to verify it fails**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest
```

Expected: FAIL because the Android project and `StoreMobileAppBootstrap` do not exist yet.

- [ ] **Step 3: Add the minimal Android project and bootstrap implementation**

Create the Gradle/Kotlin app skeleton with:

- Compose-enabled Android app
- application id like `com.store.mobile`
- `minSdk`, `targetSdk`, Kotlin/JVM setup
- `StoreMobileAppBootstrap` object exposing `appName = "Store Mobile"`
- `MainActivity` rendering a minimal Compose root

- [ ] **Step 4: Re-run the Android unit test**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.StoreMobileAppBootstrapTest
```

Expected: PASS

- [ ] **Step 5: Commit the mobile scaffold**

```powershell
git add .gitignore README.md apps/store-mobile
git commit -m "feat: scaffold store mobile app"
```

### Task 2: Add Generic Mobile Runtime Activation And Session Support

**Files:**
- Modify: `services/control-plane-api/store_control_plane/services/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/routes/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/routes/auth.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/auth.py`
- Modify: `services/control-plane-api/tests/test_store_desktop_activation_flow.py`
- Create: `services/control-plane-api/tests/test_store_mobile_activation_flow.py`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write the failing mobile activation flow test**

Create `services/control-plane-api/tests/test_store_mobile_activation_flow.py` with a first test covering:

```python
def test_mobile_store_spoke_can_redeem_activation_and_receive_runtime_session():
    ...
    assert response.status_code == 200
    assert payload["device_id"] == device_id
    assert payload["runtime_profile"] == "mobile_store_spoke"
```

- [ ] **Step 2: Run the new backend test to verify it fails**

Run:

```powershell
python -m pytest services/control-plane-api/tests/test_store_mobile_activation_flow.py -q
```

Expected: FAIL because no generic/mobile activation path exists yet.

- [ ] **Step 3: Implement the minimal generic mobile activation/session path**

Add a bounded flow that:

- allows `session_surface = store_mobile`
- resolves `runtime_profile = mobile_store_spoke`
- issues/redeems mobile runtime activation without copying desktop-only assumptions
- returns a short-lived runtime session plus device/staff context suitable for the mobile spoke

Keep this separate from desktop local-PIN/offline unlock rules unless the spec explicitly needs the same local-auth posture.

- [ ] **Step 4: Re-run the mobile activation test**

Run:

```powershell
python -m pytest services/control-plane-api/tests/test_store_mobile_activation_flow.py -q
```

Expected: PASS

- [ ] **Step 5: Run the existing desktop activation regression**

Run:

```powershell
python -m pytest services/control-plane-api/tests/test_store_desktop_activation_flow.py -q
```

Expected: PASS, proving the genericization did not break desktop auth.

- [ ] **Step 6: Commit the mobile activation contract**

```powershell
git add services/control-plane-api packages/types
git commit -m "feat: add mobile runtime activation flow"
```

### Task 3: Add Mobile Pairing, Session, And Hub Contract Modules

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePairingRepository.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileSessionRepository.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileHubClient.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileModels.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingViewModel.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingScreen.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobilePairingRepositoryTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/pairing/PairingViewModelTest.kt`

- [ ] **Step 1: Write the failing pairing repository test**

Create `StoreMobilePairingRepositoryTest.kt`:

```kotlin
@Test
fun persistsHubManifestAndPairedDeviceContext() {
    val repository = InMemoryStoreMobilePairingRepository()
    repository.savePairedDevice(deviceId = "device-1", runtimeProfile = "mobile_store_spoke")
    assertEquals("device-1", repository.loadPairedDevice()?.deviceId)
}
```

- [ ] **Step 2: Run the Android unit test to verify it fails**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.runtime.StoreMobilePairingRepositoryTest
```

Expected: FAIL because pairing/session repositories do not exist yet.

- [ ] **Step 3: Implement the minimal pairing/session/hub modules**

Add:

- local paired-device persistence
- hub manifest fetch contract
- spoke activation redemption client
- session persistence for the mobile runtime
- pairing screen/view model with QR/manual-code ready state

- [ ] **Step 4: Re-run the pairing/session tests**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.runtime.StoreMobilePairingRepositoryTest --tests com.store.mobile.ui.pairing.PairingViewModelTest
```

Expected: PASS

- [ ] **Step 5: Commit the mobile pairing/session layer**

```powershell
git add apps/store-mobile
git commit -m "feat: add mobile pairing and session layer"
```

### Task 4: Add Camera Barcode Scan And Lookup

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/CameraBarcodeScanner.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/scan/ScanLookupRepository.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupViewModel.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt`
- Modify: `packages/barcode/src/index.ts`
- Modify: `packages/barcode/src/index.test.ts`

- [ ] **Step 1: Write the failing scan/lookup test**

Create `ScanLookupViewModelTest.kt` with a case like:

```kotlin
@Test
fun resolvesScannedBarcodeIntoLookupState() {
    ...
    assertEquals("ACME TEA", state.productName)
}
```

- [ ] **Step 2: Run the scan/lookup test to verify it fails**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.ScanLookupViewModelTest
```

Expected: FAIL because camera scan/lookup state does not exist.

- [ ] **Step 3: Implement camera scan + lookup minimal flow**

Add:

- CameraX/ML Kit barcode scanning boundary
- lookup repository calling existing barcode/catalog/customer routes as needed
- scan-first Compose screen/view model
- shared barcode normalization tweaks only if required by the mobile payload shape

- [ ] **Step 4: Re-run the mobile and shared barcode tests**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.scan.ScanLookupViewModelTest
Set-Location ..\..
npm run test --workspace @store/barcode
```

Expected: PASS

- [ ] **Step 5: Commit the scan/lookup slice**

```powershell
git add apps/store-mobile packages/barcode
git commit -m "feat: add mobile scan and lookup flow"
```

### Task 5: Add Receiving, Stock Count, And Expiry Mobile Workflows

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/operations/ReceivingRepository.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/operations/StockCountRepository.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/operations/ExpiryRepository.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsHomeScreen.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/ReceivingScreen.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/StockCountScreen.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/ExpiryScreen.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/ReceivingRepositoryTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/StockCountRepositoryTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/operations/ExpiryRepositoryTest.kt`

- [ ] **Step 1: Write the failing receiving/count/expiry tests**

Add one focused repository test per flow, for example:

```kotlin
@Test
fun loadsReceivingBoardForBranch() { ... }

@Test
fun loadsStockCountContextForBranch() { ... }

@Test
fun loadsExpiryRecordsForBranch() { ... }
```

- [ ] **Step 2: Run the operation tests to verify they fail**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.ReceivingRepositoryTest --tests com.store.mobile.operations.StockCountRepositoryTest --tests com.store.mobile.operations.ExpiryRepositoryTest
```

Expected: FAIL because the repositories/screens do not exist.

- [ ] **Step 3: Implement minimal operations repositories and screens**

Add:

- receiving read/write support bounded by existing policy
- stock count support
- expiry support
- one operations home/navigation entry point

Keep the UX handheld-first and avoid desktop-style dense forms.

- [ ] **Step 4: Re-run the operation tests**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.operations.ReceivingRepositoryTest --tests com.store.mobile.operations.StockCountRepositoryTest --tests com.store.mobile.operations.ExpiryRepositoryTest
```

Expected: PASS

- [ ] **Step 5: Commit the operations slice**

```powershell
git add apps/store-mobile
git commit -m "feat: add mobile operations workflows"
```

### Task 6: Add Runtime Posture, CI Hooks, And Docs

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/runtime/RuntimeStatusScreen.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/runtime/RuntimeStatusScreenTest.kt`
- Modify: `package.json`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Write the failing runtime-status test**

Create a focused UI/unit test:

```kotlin
@Test
fun showsDisconnectedHubState() { ... }
```

- [ ] **Step 2: Run the runtime-status test to verify it fails**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.runtime.RuntimeStatusScreenTest
```

Expected: FAIL because runtime posture UI does not exist.

- [ ] **Step 3: Implement runtime posture and repo integration hooks**

Add:

- runtime/sync posture screen
- root npm script like `ci:store-mobile`
- CI job invoking Gradle unit tests
- README/worklog/ledger updates marking progress on `V2-001`

- [ ] **Step 4: Run the final mobile verification stack**

Run:

```powershell
Set-Location apps/store-mobile
.\gradlew.bat testDebugUnitTest
Set-Location ..\..
git diff --check
```

Expected: PASS and clean diff hygiene.

- [ ] **Step 5: Commit the mobile first slice**

```powershell
git add apps/store-mobile package.json .github/workflows/ci.yml README.md docs/TASK_LEDGER.md docs/WORKLOG.md
git commit -m "feat: add first store mobile runtime slice"
```
