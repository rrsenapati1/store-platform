# Store Mobile Tablet Productization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Productize the `inventory_tablet_spoke` runtime into an overview-first backroom tablet shell with focused inventory task drill-down.

**Architecture:** Keep the existing operation repositories and view models intact, add a pure tablet destination and overview model, then rebuild the tablet shell around those models. Reuse current receiving/count/restock/expiry content where possible, but stop presenting the tablet as a generic section switcher.

**Tech Stack:** Kotlin, Jetpack Compose Material 3, existing mobile theme system, Android unit tests.

---

### Task 1: Add tablet destination and overview model foundations

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/tablet/InventoryTabletDestination.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/tablet/InventoryTabletOverviewModel.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/tablet/InventoryTabletDestinationTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/tablet/InventoryTabletOverviewModelTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/StoreMobileShellModeTest.kt`

- [ ] Write failing tests for tablet destinations, default overview behavior, and overview derivation.
- [ ] Run the focused tests and confirm they fail.
- [ ] Implement the pure destination enum and overview-model helpers.
- [ ] Re-run the focused tests and confirm they pass.
- [ ] Commit.

### Task 2: Rebuild the tablet shell around an overview-first workflow

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/tablet/InventoryTabletShell.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/tablet/InventoryTabletOverviewScreen.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/tablet/InventoryTabletSectionRail.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/StoreMobileRuntimeContextTest.kt`

- [ ] Write failing tests for tablet routing and overview-first app behavior.
- [ ] Run the focused tests and confirm they fail.
- [ ] Implement the new tablet shell, overview screen, and app routing changes.
- [ ] Re-run the focused tests and confirm they pass.
- [ ] Commit.

### Task 3: Polish tablet scan/runtime composition and document closure

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/scan/ScanLookupScreen.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/runtime/RuntimeStatusScreen.kt`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] Add failing tests for any new tablet-specific scan/runtime labels or states where practical.
- [ ] Implement the tablet polish needed for scan and runtime consistency.
- [ ] Update the deferred backlog/docs to mark tablet productization complete.
- [ ] Run full mobile verification, then commit and merge.
