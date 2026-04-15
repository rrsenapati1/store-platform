# Store Desktop Cash Drawer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first `V2-003` advanced-hardware slice by supporting packaged Store Desktop cash drawer assignment, manual drawer-open actions, and operator diagnostics.

**Architecture:** Extend the existing runtime hardware bridge with a printer-backed cash drawer path. Use a native Windows cash drawer backend for raw ESC/POS drawer pulses, persist assignment/diagnostics in the runtime hardware state, and surface the controls in the packaged cashier UI.

**Tech Stack:** React, TypeScript, Vitest, Tauri, Rust, Windows printing APIs

---

### Task 1: Extend the desktop hardware contract for cash drawers

**Files:**
- Modify: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareContract.ts`
- Modify: `apps/store-desktop/src/runtime-hardware/browserStoreRuntimeHardware.ts`
- Modify: `apps/store-desktop/src/runtime-hardware/nativeStoreRuntimeHardware.ts`
- Test: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts`

- [ ] **Step 1: Write the failing adapter test expectations for cash drawer fields and command**

- [ ] **Step 2: Run the targeted adapter test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts`

- [ ] **Step 3: Add contract types for cash drawer assignment, diagnostics, and `openCashDrawer()`**

- [ ] **Step 4: Update browser/native hardware adapters to satisfy the contract**

- [ ] **Step 5: Re-run the targeted adapter test to verify it passes**

### Task 2: Add native packaged-runtime cash drawer support

**Files:**
- Create: `apps/store-desktop/src-tauri/src/runtime_cash_drawer.rs`
- Modify: `apps/store-desktop/src-tauri/Cargo.toml`
- Modify: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`
- Test: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`
- Test: `apps/store-desktop/src-tauri/src/runtime_cash_drawer.rs`

- [ ] **Step 1: Add the failing Rust tests for drawer assignment and drawer-open diagnostics**

- [ ] **Step 2: Run the targeted Rust tests to verify they fail**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml runtime_hardware --lib`

- [ ] **Step 3: Implement the cash drawer backend module and Windows raw pulse bridge**

- [ ] **Step 4: Extend runtime hardware state/profile/diagnostics and add the open-drawer command**

- [ ] **Step 5: Re-run the targeted Rust tests to verify they pass**

### Task 3: Surface cash drawer controls in the cashier UI

**Files:**
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeHardwareIntegration.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StorePrintQueueSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx`
- Create: `apps/store-desktop/src/control-plane/StorePrintQueueSection.test.tsx`

- [ ] **Step 1: Write the failing print-queue UI test for drawer controls and diagnostics**

- [ ] **Step 2: Run the targeted UI test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- src/control-plane/StorePrintQueueSection.test.tsx`

- [ ] **Step 3: Expose cash drawer assignment/open actions through the workspace and hardware integration hook**

- [ ] **Step 4: Add the drawer assignment, diagnostics, and open action to the print queue and shell UI**

- [ ] **Step 5: Re-run the targeted UI test to verify it passes**

### Task 4: Update docs and verify the slice

**Files:**
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Mark `V2-003` as `In Progress` and record the cash drawer slice in the worklog**

- [ ] **Step 2: Run the full desktop verification suite**

Run:
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
- `git -c core.safecrlf=false diff --check`

- [ ] **Step 3: Commit the docs/spec**

```bash
git add docs/superpowers/specs/2026-04-15-store-desktop-cash-drawer-design.md docs/superpowers/plans/2026-04-15-store-desktop-cash-drawer.md
git commit -m "docs: add desktop cash drawer design"
```

- [ ] **Step 4: Commit the implementation**

```bash
git add apps/store-desktop/src-tauri/Cargo.toml apps/store-desktop/src-tauri/src/runtime_cash_drawer.rs apps/store-desktop/src-tauri/src/runtime_hardware.rs apps/store-desktop/src-tauri/src/lib.rs apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareContract.ts apps/store-desktop/src/runtime-hardware/browserStoreRuntimeHardware.ts apps/store-desktop/src/runtime-hardware/nativeStoreRuntimeHardware.ts apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts apps/store-desktop/src/control-plane/useStoreRuntimeHardwareIntegration.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StorePrintQueueSection.tsx apps/store-desktop/src/control-plane/StorePrintQueueSection.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx docs/TASK_LEDGER.md docs/WORKLOG.md
git commit -m "feat: add desktop cash drawer integration"
```
