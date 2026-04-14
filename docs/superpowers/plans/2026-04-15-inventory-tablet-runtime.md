# Inventory Tablet Runtime Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans or superpowers:subagent-driven-development when executing this plan.

**Goal:** Extend the existing Android runtime into an `inventory_tablet_spoke` profile with minimal backend changes and a distinct tablet shell.

**Architecture:** Keep one Android app, reuse shared spoke/session/operations layers, add runtime-profile resolution plus a tablet-first shell, and extend the generic runtime activation contract to map `inventory_tablet -> inventory_tablet_spoke`.

**Tech Stack:** Kotlin, Jetpack Compose, existing FastAPI control plane, existing branch-hub runtime contracts

---

### Task 1: Add Tablet Runtime Activation Contract

**Files:**
- Modify: `services/control-plane-api/tests/test_store_mobile_activation_flow.py`
- Modify: `services/control-plane-api/store_control_plane/services/workforce.py`

- [ ] Add a failing backend test proving `session_surface = inventory_tablet` redeems to `inventory_tablet_spoke`
- [ ] Run the focused pytest case and confirm it fails
- [ ] Extend runtime-profile mapping minimally
- [ ] Re-run the mobile/tablet activation tests and confirm both pass

### Task 2: Add Tablet Pairing Selection In Android

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileHubClient.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingViewModel.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingScreen.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/pairing/PairingViewModelTest.kt`

- [ ] Add a failing Android unit test for tablet pairing selection
- [ ] Run the targeted Gradle test and confirm it fails
- [ ] Add runtime-surface selection and fake-client support for tablet activation
- [ ] Re-run the pairing tests and confirm they pass

### Task 3: Split Handheld And Tablet Shells

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileShellMode.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/handheld/HandheldStoreShell.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/tablet/InventoryTabletShell.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/operations/OperationsHomeScreen.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/StoreMobileShellModeTest.kt`

- [ ] Add a failing test for runtime-profile-to-shell resolution
- [ ] Run the targeted Gradle test and confirm it fails
- [ ] Extract shell resolution and add handheld/tablet shell composables
- [ ] Make tablet default to an inventory-first section
- [ ] Re-run the shell test and the full mobile unit suite

### Task 4: Update Docs, Verify, Commit

**Files:**
- Modify: `apps/store-mobile/README.md`
- Modify: `docs/PROJECT_CONTEXT.md`
- Modify: `docs/STORE_CANONICAL_BLUEPRINT.md`
- Modify: `docs/WORKLOG.md`

- [ ] Update docs to reflect the tablet slice inside the shared Android app
- [ ] Run:
  - `npm run ci:store-mobile`
  - `python -m pytest services/control-plane-api/tests/test_store_mobile_activation_flow.py -q`
  - `git diff --check`
- [ ] Commit the slice with a dedicated message
