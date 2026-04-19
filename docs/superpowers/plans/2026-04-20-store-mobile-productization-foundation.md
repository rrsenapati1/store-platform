# Store Mobile Productization Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `store-mobile` into a handheld-first, scan-led associate runtime with modern light/dark UI, contextual task routing, and a clearer live-runtime shell.

**Architecture:** Preserve the existing pairing, session, repository, and operation view-model contracts, but split the oversized mobile root into focused entry, shell, scan, task, and runtime surfaces. The new handheld shell should own navigation and product hierarchy, while existing operations flows remain as task detail content behind a stronger scan-first model.

**Tech Stack:** Kotlin, Jetpack Compose Material 3, Android unit tests, existing `StoreMobile*Repository` interfaces, current pairing/session persistence, camera/DataWedge scan flows.

---

## File Structure

### Existing files to keep but narrow

- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
  - Classification: `mixed-responsibility`
  - Current seams to extract: entry composition, handheld runtime shell selection, theme wrapper, contextual action derivation
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingScreen.kt`
  - Keep pairing/session lifecycle behavior, but reframe the UI as a polished runtime entry surface
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt`
  - Preserve scanner and lookup mechanics, but restyle and recompose it into the new scan-first home
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/runtime/RuntimeStatusScreen.kt`
  - Convert from plain diagnostics dump into a usable runtime area
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsContent.kt`
  - Keep operation screens reachable, but route them through the new shell model instead of equal-weight top tabs
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsHomeScreen.kt`
  - Replace or reduce the current equal-weight section switcher
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/StoreMobileAppBootstrapTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/runtime/RuntimeStatusScreenTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt`

### New theme and shell files

- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/theme/StoreMobileTheme.kt`
  - Mobile light/dark theme contract and semantic colors
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/theme/StoreMobileThemeMode.kt`
  - Theme-mode state model and helpers
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/entry/StoreMobileEntrySurface.kt`
  - Productized pre-runtime lifecycle surface
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldRuntimeShell.kt`
  - Live-runtime shell with `Scan`, `Tasks`, and `Runtime`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldRuntimeDestination.kt`
  - Destination model for the new handheld shell

### New scan-first and task-routing files

- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldScanHomeScreen.kt`
  - Scan header, last scanned item panel, contextual action rail, recent task context, queue preview
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldTasksScreen.kt`
  - Task hub and resumable work routing
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldScanActionModel.kt`
  - Pure derivation of recommended actions and task previews from lookup and operation state
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldRuntimeSummary.kt`
  - Compact runtime/device/session summary for the shell

### New tests

- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/handheld/HandheldScanActionModelTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/handheld/HandheldRuntimeDestinationTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/theme/StoreMobileThemeModeTest.kt`

## Task 1: Add the handheld theme and destination foundation

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/theme/StoreMobileTheme.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/theme/StoreMobileThemeMode.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldRuntimeDestination.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/handheld/HandheldRuntimeDestinationTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/theme/StoreMobileThemeModeTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/StoreMobileAppBootstrapTest.kt`

- [ ] **Step 1: Write failing tests for theme-mode and destination semantics**

Add tests that require:

- handheld destinations to be exactly `SCAN`, `TASKS`, and `RUNTIME`
- `Entry` to stay a lifecycle surface outside the live shell
- mobile theme-mode helpers to support `LIGHT`, `DARK`, and `SYSTEM`

- [ ] **Step 2: Run the focused Android tests to verify they fail**

Run:

```powershell
cd apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.handheld.HandheldRuntimeDestinationTest --tests com.store.mobile.ui.theme.StoreMobileThemeModeTest --tests com.store.mobile.StoreMobileAppBootstrapTest
```

Expected: FAIL because the destination and theme files do not exist yet.

- [ ] **Step 3: Implement the new theme and destination types**

Create:

```kotlin
enum class StoreMobileThemeMode { SYSTEM, LIGHT, DARK }
enum class HandheldRuntimeDestination { SCAN, TASKS, RUNTIME }
```

and a dedicated `StoreMobileTheme(...)` wrapper that owns light/dark color schemes instead of relying on raw `MaterialTheme {}` calls at the app root.

- [ ] **Step 4: Re-run the focused tests**

Run the same Gradle command.

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add apps/store-mobile/app/src/main/java/com/store/mobile/ui/theme/StoreMobileTheme.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/theme/StoreMobileThemeMode.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldRuntimeDestination.kt apps/store-mobile/app/src/test/java/com/store/mobile/ui/handheld/HandheldRuntimeDestinationTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/ui/theme/StoreMobileThemeModeTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/StoreMobileAppBootstrapTest.kt
git commit -m "feat: add store mobile theme and shell foundation"
```

## Task 2: Split the app root and productize the entry posture

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/entry/StoreMobileEntrySurface.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingScreen.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingViewModel.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/pairing/PairingViewModelTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobilePairingRepositoryTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobileSessionRepositoryTest.kt`

- [ ] **Step 1: Write failing tests for entry-state semantics**

Add or expand tests to require:

- expired runtime sessions stay paired but surface explicit recovery copy
- signed-out-but-paired posture remains distinct from unpaired posture
- live runtime state no longer depends on the old root-level inline header buttons alone
- sign-out preserves the paired device record
- unpair clears both pairing and runtime session state

- [ ] **Step 2: Run the focused entry tests to verify they fail**

Run:

```powershell
cd apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.pairing.PairingViewModelTest --tests com.store.mobile.runtime.StoreMobilePairingRepositoryTest --tests com.store.mobile.runtime.StoreMobileSessionRepositoryTest
```

Expected: FAIL because the new entry surface and refined state expectations do not exist yet.

- [ ] **Step 3: Extract the entry surface and narrow `StoreMobileApp.kt`**

Move pre-runtime rendering into `StoreMobileEntrySurface.kt`.

`StoreMobileApp.kt` should become an orchestrator that:

- wires repositories and view models
- derives live runtime context
- chooses between:
  - `StoreMobileEntrySurface`
  - `HandheldRuntimeShell`
  - existing tablet shell fallback

Do not let the root keep direct responsibility for all entry-screen layout details.

- [ ] **Step 4: Re-run the focused entry tests**

Run the same Gradle command.

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/entry/StoreMobileEntrySurface.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingScreen.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingViewModel.kt apps/store-mobile/app/src/test/java/com/store/mobile/ui/pairing/PairingViewModelTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobilePairingRepositoryTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobileSessionRepositoryTest.kt
git commit -m "feat: productize store mobile entry flow"
```

## Task 3: Build the scan-first handheld home and action model

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldScanActionModel.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldScanHomeScreen.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/handheld/HandheldScanActionModelTest.kt`

- [ ] **Step 1: Write failing tests for contextual scan actions**

Create `HandheldScanActionModelTest.kt` to require:

- scanned item with stock posture yields a prioritized action list
- no scanned item yields `Scan another` / idle posture only
- active receiving/count/restock/expiry state yields resumable task context

- [ ] **Step 2: Run the focused scan/action tests to verify they fail**

Run:

```powershell
cd apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.handheld.HandheldScanActionModelTest --tests com.store.mobile.scan.ScanLookupViewModelTest
```

Expected: FAIL because the new action model and scan-home composition do not exist yet.

- [ ] **Step 3: Implement the pure action model first**

Create a pure model function like:

```kotlin
fun buildHandheldScanActionModel(...): HandheldScanActionModel
```

that derives:

- primary action
- secondary action
- recent task context
- queue preview labels

from existing lookup and task state without touching repositories.

- [ ] **Step 4: Build the new scan-first screen**

Create `HandheldScanHomeScreen.kt` and refactor `ScanLookupScreen.kt` to support:

- scan command header
- last scanned item panel
- contextual action rail
- recent task context
- short queue preview

Keep the existing camera/DataWedge/manual lookup mechanics intact.

- [ ] **Step 5: Re-run the focused scan/action tests**

Run the same Gradle command.

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldScanActionModel.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldScanHomeScreen.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt apps/store-mobile/app/src/test/java/com/store/mobile/ui/handheld/HandheldScanActionModelTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/scan/ScanLookupViewModelTest.kt
git commit -m "feat: add store mobile scan-first handheld home"
```

## Task 4: Replace the equal-weight handheld switcher with the new runtime shell

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldRuntimeShell.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldTasksScreen.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldRuntimeSummary.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldStoreShell.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsContent.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsHomeScreen.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/runtime/RuntimeStatusScreen.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/runtime/RuntimeStatusScreenTest.kt`

- [ ] **Step 1: Write failing tests for the new shell routing**

Add tests that require:

- handheld runtime to default to `SCAN`
- task hub to exist separately from runtime diagnostics
- runtime area to expose live-session actions like `Sign out` and `Unpair`

- [ ] **Step 2: Run the focused shell/runtime tests to verify they fail**

Run:

```powershell
cd apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.runtime.RuntimeStatusScreenTest --tests com.store.mobile.ui.handheld.HandheldRuntimeDestinationTest
```

Expected: FAIL because the old equal-weight shell still drives the handheld UI.

- [ ] **Step 3: Implement the handheld runtime shell**

Create a shell that owns:

- destination selection
- live runtime header
- scan/tasks/runtime composition

`OperationsContent.kt` should stop acting like the primary top-level navigation driver for handheld mode.

- [ ] **Step 4: Rework runtime diagnostics into a usable runtime area**

`RuntimeStatusScreen.kt` should move beyond plain text rows and surface:

- connection posture
- session expiry
- scanner posture
- sign out
- unpair

in a modern, legible handheld layout.

- [ ] **Step 5: Re-run the focused shell/runtime tests**

Run the same Gradle command.

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldRuntimeShell.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldTasksScreen.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldRuntimeSummary.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldStoreShell.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsContent.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsHomeScreen.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/runtime/RuntimeStatusScreen.kt apps/store-mobile/app/src/test/java/com/store/mobile/ui/runtime/RuntimeStatusScreenTest.kt
git commit -m "feat: add store mobile handheld runtime shell"
```

## Task 5: Final integration, verification, and deferred release tracking

**Files:**
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/runbooks/dev-workflow.md`

- [ ] **Step 1: Record the deferred public-release follow-ups**

Add explicit deferred items to `docs/TASK_LEDGER.md` under a dedicated section named `Public Release Deferred Productization` so the following remain visible:

- inventory tablet productization
- secure-storage hardening review
- final mobile error/empty/loading polish
- final cross-app visual parity audit

- [ ] **Step 2: Record the mobile productization slice in the worklog**

Document:

- handheld-first shell rewrite
- scan-first home
- entry/runtime lifecycle polish
- theme foundation
- deferred follow-on items

- [ ] **Step 3: Run final verification**

Run:

```powershell
cd D:\codes\projects\store\.worktrees\korsenex-store-mobile-productization
npm run ci:store-mobile
cd apps/store-mobile
.\gradlew.bat testDebugUnitTest --tests com.store.mobile.ui.pairing.PairingViewModelTest --tests com.store.mobile.runtime.StoreMobilePairingRepositoryTest --tests com.store.mobile.runtime.StoreMobileSessionRepositoryTest --tests com.store.mobile.ui.StoreMobileRuntimeContextTest
git -c core.safecrlf=false diff --check
```

This explicit second Gradle command is required to prove:

- persisted pairing restore still works
- sign-out still preserves pairing
- unpair still clears both pairing and session
- repository-backed runtime context still survives the shell rewrite

- [ ] **Step 4: Commit**

```powershell
git add docs/WORKLOG.md docs/TASK_LEDGER.md docs/runbooks/dev-workflow.md
git commit -m "docs: record store mobile productization foundation"
```
