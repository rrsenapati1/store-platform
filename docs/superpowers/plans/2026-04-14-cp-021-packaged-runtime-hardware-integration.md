# CP-021 Packaged Runtime Hardware Integration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace packaged-runtime print and scan simulation with real hardware-backed printer execution, keyboard-wedge scanner capture, and visible local diagnostics.

**Architecture:** Add a Windows-first native hardware bridge in Tauri for printer discovery, printer profile persistence, print dispatch, and diagnostics. Keep `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts` thin by extracting hardware polling and barcode scanner capture into dedicated hooks and adapters instead of expanding the existing 1200-line orchestration file.

**Tech Stack:** Tauri 2, Rust, Windows APIs or Windows-native shell commands, React 19, Vitest, TypeScript

---

### Task 1: Add the native hardware bridge contract and local hardware profile store

**Files:**
- Create: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareContract.ts`
- Create: `apps/store-desktop/src/runtime-hardware/nativeStoreRuntimeHardware.ts`
- Create: `apps/store-desktop/src/runtime-hardware/browserStoreRuntimeHardware.ts`
- Create: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardware.ts`
- Create: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts`
- Create: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`
- Test: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`

- [ ] **Step 1: Write the failing adapter tests**

Cover:
- native bridge payload validation,
- browser fallback posture,
- loading empty hardware status,
- saving printer assignments and reading them back.

- [ ] **Step 2: Run the targeted frontend tests to verify red**

Run: `npm run test --workspace @store/store-desktop -- storeRuntimeHardwareAdapter.test.ts`
Expected: FAIL because the hardware contract and adapter do not exist.

- [ ] **Step 3: Write the failing native store tests**

Add Rust tests for:
- empty hardware state,
- persisted receipt and label printer assignment,
- diagnostics timestamps or status values round-tripping.

- [ ] **Step 4: Run the targeted native tests to verify red**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib runtime_hardware`
Expected: FAIL because the module and commands do not exist.

- [ ] **Step 5: Implement the minimal hardware contract and native store**

Add:
- typed hardware status and diagnostics interfaces,
- native commands to load status and save printer assignments,
- browser fallback adapter,
- command registration in `lib.rs`.

- [ ] **Step 6: Run the targeted tests to verify green**

Run:
- `npm run test --workspace @store/store-desktop -- storeRuntimeHardwareAdapter.test.ts`
- `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib runtime_hardware`
Expected: PASS

- [ ] **Step 7: Commit**

Run:
`git add apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareContract.ts apps/store-desktop/src/runtime-hardware/nativeStoreRuntimeHardware.ts apps/store-desktop/src/runtime-hardware/browserStoreRuntimeHardware.ts apps/store-desktop/src/runtime-hardware/storeRuntimeHardware.ts apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts apps/store-desktop/src-tauri/src/runtime_hardware.rs apps/store-desktop/src-tauri/src/lib.rs`

Commit:
`git commit -m "feat: add packaged runtime hardware bridge contract"`

### Task 2: Add Windows printer discovery, diagnostics, and native print dispatch

**Files:**
- Modify: `apps/store-desktop/src-tauri/Cargo.toml`
- Modify: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`
- Create: `apps/store-desktop/src-tauri/src/runtime_printer.rs`
- Test: `apps/store-desktop/src-tauri/src/runtime_printer.rs`
- Test: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`

- [ ] **Step 1: Write the failing native printer tests**

Cover:
- discovering printers through the Windows bridge abstraction,
- choosing the correct printer for receipt vs barcode-label jobs,
- updating diagnostics after success,
- surfacing a bounded failure reason when no printer is configured.

- [ ] **Step 2: Run the targeted native tests to verify red**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib runtime_printer`
Expected: FAIL because discovery and print dispatch do not exist.

- [ ] **Step 3: Implement printer discovery and dispatch**

Add:
- Windows printer enumeration,
- printer assignment resolution,
- printable text rendering for receipt and label payloads,
- bounded diagnostics state for last print result.

- [ ] **Step 4: Re-run the targeted native tests to verify green**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib runtime_printer`
Expected: PASS

- [ ] **Step 5: Run the broader native bridge tests**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib runtime_hardware`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
`git add apps/store-desktop/src-tauri/Cargo.toml apps/store-desktop/src-tauri/src/runtime_hardware.rs apps/store-desktop/src-tauri/src/runtime_printer.rs`

Commit:
`git commit -m "feat: add native printer discovery and dispatch"`

### Task 3: Automate packaged-runtime print execution and surface hardware diagnostics in the shell

**Files:**
- Create: `apps/store-desktop/src/control-plane/useStoreRuntimeHardwareIntegration.ts`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.hardware.test.tsx`
- Modify: `apps/store-desktop/src/runtime-shell/storeRuntimeShellContract.ts`
- Modify: `apps/store-desktop/src/runtime-shell/nativeStoreRuntimeShell.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeShellStatus.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StorePrintQueueSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.print.test.tsx`

- [ ] **Step 1: Write the failing packaged-runtime print automation tests**

Cover:
- packaged runtime polls print jobs and dispatches them automatically,
- successful dispatch completes the print job through the control plane,
- printer assignment missing keeps the job uncompleted and exposes diagnostics,
- packaged runtime no longer depends on manual completion controls.

- [ ] **Step 2: Run the targeted frontend tests to verify red**

Run:
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.hardware.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.print.test.tsx`
Expected: FAIL because no hardware integration hook or shell diagnostics exist.

- [ ] **Step 3: Implement the hardware integration hook**

Add a focused hook that:
- reads native hardware status,
- polls queued print jobs when the packaged runtime is session-live and unlocked,
- submits jobs through the native bridge,
- reports success or failure back through existing control-plane routes,
- keeps `useStoreRuntimeWorkspace.ts` as orchestration only.

- [ ] **Step 4: Extend shell diagnostics and print UI**

Add:
- shell fields for hardware bridge state and hardware diagnostics,
- print-queue UI for discovered printers and assigned receipt or label printer,
- packaged-runtime removal of the manual complete action.

- [ ] **Step 5: Run the targeted frontend tests to verify green**

Run:
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.hardware.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.print.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
`git add apps/store-desktop/src/control-plane/useStoreRuntimeHardwareIntegration.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.hardware.test.tsx apps/store-desktop/src/runtime-shell/storeRuntimeShellContract.ts apps/store-desktop/src/runtime-shell/nativeStoreRuntimeShell.ts apps/store-desktop/src/control-plane/useStoreRuntimeShellStatus.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StorePrintQueueSection.tsx apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.print.test.tsx`

Commit:
`git commit -m "feat: automate packaged runtime print execution"`

### Task 4: Add keyboard-wedge barcode scanner capture and scan-ready runtime UI

**Files:**
- Create: `apps/store-desktop/src/control-plane/useStoreRuntimeBarcodeScanner.ts`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.barcode-scanner.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.barcode.test.tsx`
- Modify: `packages/barcode/src/index.ts`
- Modify: `packages/barcode/src/index.test.ts`

- [ ] **Step 1: Write the failing scanner tests**

Cover:
- scan bursts ending with `Enter` trigger barcode normalization,
- normal typing does not trigger a scan,
- packaged runtime can auto-populate and optionally auto-lookup scanned barcodes,
- manual barcode entry still works.

- [ ] **Step 2: Run the targeted tests to verify red**

Run:
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.barcode-scanner.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.barcode.test.tsx`
- `npm run test --workspace @store/barcode`
Expected: FAIL because no scanner-capture hook exists.

- [ ] **Step 3: Implement the minimal scanner capture hook**

Add:
- scan burst timing detection,
- reuse of barcode normalization helpers,
- last scan activity diagnostics,
- workspace integration through a dedicated hook rather than inline event logic.

- [ ] **Step 4: Update the barcode lookup UI**

Add:
- scan-ready posture text,
- last scan timestamp or scanner state,
- optional auto-lookup after a valid scan,
- manual fallback controls retained.

- [ ] **Step 5: Run the targeted tests to verify green**

Run:
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.barcode-scanner.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.barcode.test.tsx`
- `npm run test --workspace @store/barcode`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
`git add apps/store-desktop/src/control-plane/useStoreRuntimeBarcodeScanner.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.barcode-scanner.test.tsx apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.barcode.test.tsx packages/barcode/src/index.ts packages/barcode/src/index.test.ts`

Commit:
`git commit -m "feat: add packaged runtime barcode scanner capture"`

### Task 5: Verify the packaged-runtime hardware slice and close the ledger item

**Files:**
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Run the native verification suite**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
Expected: PASS

- [ ] **Step 2: Run the desktop verification suite**

Run:
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
Expected: PASS

- [ ] **Step 3: Update task tracking docs**

Mark `CP-021` done in `docs/TASK_LEDGER.md` and add a concise worklog entry describing:
- native printer discovery and execution,
- keyboard-wedge scanner capture,
- hardware diagnostics surface,
- verification commands.

- [ ] **Step 4: Run the final regression check**

Run:
- `npm run test --workspace @store/store-desktop`
- `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
Expected: PASS

- [ ] **Step 5: Commit**

Run:
`git add docs/TASK_LEDGER.md docs/WORKLOG.md`

Commit:
`git commit -m "chore: close cp-021 hardware integration"`
