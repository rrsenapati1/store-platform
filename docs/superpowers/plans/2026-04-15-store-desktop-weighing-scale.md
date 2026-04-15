# Store Desktop Weighing Scale Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first packaged Store Desktop weighing-scale slice with local scale assignment, live weight reads, and operator diagnostics.

**Architecture:** Extend the existing desktop hardware bridge instead of creating a new subsystem. Add one native serial-scale backend, thread the scale state through the shared hardware contract, and expose assignment/read posture in the existing hardware desk and barcode lookup sections.

**Tech Stack:** Rust + Tauri commands, TypeScript runtime hardware adapter, React/Vitest, PowerShell-backed Windows serial bridge

---

### Task 1: Write Scale Contract Tests First

**Files:**
- Modify: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts`
- Modify: `apps/store-desktop/src/control-plane/StorePrintQueueSection.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.test.tsx`

- [ ] Add failing scale expectations to the native/browser hardware adapter tests.
- [ ] Add failing print-queue expectations for preferred-scale assignment and manual reads.
- [ ] Add failing barcode-section expectations for compact scale posture.
- [ ] Run the targeted Vitest command and confirm the new assertions fail before implementation.

### Task 2: Add Native Scale Backend

**Files:**
- Create: `apps/store-desktop/src-tauri/src/runtime_scale.rs`
- Modify: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`

- [ ] Add a scale backend trait, Windows serial/COM discovery, and manual read operation in `runtime_scale.rs`.
- [ ] Extend runtime hardware profile, diagnostics, and status records with scale fields.
- [ ] Add preferred-scale assignment and manual-read persistence logic in `runtime_hardware.rs`.
- [ ] Register the new native scale command in `lib.rs`.
- [ ] Add failing Rust tests first, then implement the minimum code to satisfy them.

### Task 3: Thread Scale State Through The TS Hardware Bridge

**Files:**
- Modify: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareContract.ts`
- Modify: `apps/store-desktop/src/runtime-hardware/browserStoreRuntimeHardware.ts`
- Modify: `apps/store-desktop/src/runtime-hardware/nativeStoreRuntimeHardware.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeHardwareIntegration.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`

- [ ] Extend the contract types and runtime adapter with scale records, diagnostics, assignment, and manual read actions.
- [ ] Add browser fallback posture for scale support.
- [ ] Wire preferred-scale assignment and read-current-weight actions through the existing workspace hook chain.
- [ ] Re-run the targeted adapter tests and confirm they pass.

### Task 4: Surface Scale Controls In The Counter UI

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StorePrintQueueSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`

- [ ] Add discovered-scale assignment controls and a manual read action in the hardware desk.
- [ ] Add a compact scale posture card in the barcode lookup section.
- [ ] Keep the UI read-only with respect to billing; do not change sale pricing logic.
- [ ] Re-run the targeted React tests and confirm they pass.

### Task 5: Update Ledger And Verify End-To-End

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] Add a worklog entry for the weighing-scale slice.
- [ ] Run full verification:
  - `npm run test --workspace @store/store-desktop`
  - `npm run typecheck --workspace @store/store-desktop`
  - `npm run build --workspace @store/store-desktop`
  - `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
  - `git -c core.safecrlf=false diff --check`
- [ ] Commit docs and implementation separately with clear messages.
