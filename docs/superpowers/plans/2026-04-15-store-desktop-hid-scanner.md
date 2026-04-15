# Store Desktop HID Scanner Inventory Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add packaged Store Desktop HID scanner discovery, preferred-scanner assignment, and scanner-presence diagnostics while keeping keyboard-wedge capture as the active input path.

**Architecture:** Extend the native runtime hardware bridge with a scanner backend and scanner-aware profile/diagnostics model, then feed that posture into the existing wedge-capture hook and desktop UI. Barcode input stays in the existing React hook; native state only adds inventory, assignment, and persisted scan activity.

**Tech Stack:** React 19, Vitest, Tauri 2, Rust, Windows-first HID discovery, existing Store Desktop runtime hardware bridge

---

### Task 1: Extend the desktop hardware contract with scanner inventory

**Files:**
- Modify: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareContract.ts`
- Modify: `apps/store-desktop/src/runtime-hardware/browserStoreRuntimeHardware.ts`
- Test: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts`

- [ ] **Step 1: Write the failing adapter expectations**

Add assertions for:
- `scanners`
- `profile.preferred_scanner_id`
- scanner transports `usb_hid` and `bluetooth_hid`

- [ ] **Step 2: Run the adapter test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts`
Expected: FAIL because the contract and mocked payloads do not support scanner inventory/profile fields yet.

- [ ] **Step 3: Implement the minimal contract changes**

Add:
- `StoreRuntimeScannerTransport`
- `StoreRuntimeScannerRecord`
- `scanners` on `StoreRuntimeHardwareStatus`
- `preferred_scanner_id` on profile/profile input
- adapter validation updates
- browser fallback defaults

- [ ] **Step 4: Re-run the adapter test**

Run: `npm run test --workspace @store/store-desktop -- src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts`
Expected: PASS

### Task 2: Add the native scanner backend and scanner-aware hardware status

**Files:**
- Create: `apps/store-desktop/src-tauri/src/runtime_scanner.rs`
- Modify: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`
- Modify: `apps/store-desktop/src-tauri/Cargo.toml`
- Test: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`

- [ ] **Step 1: Write the failing Rust tests**

Add tests for:
- default hardware status includes empty scanner inventory and `preferred_scanner_id = None`
- preferred scanner connected keeps diagnostics `ready`
- preferred scanner missing yields `attention_required`
- scan activity updates `last_scan_at` and `last_scan_barcode_preview`

- [ ] **Step 2: Run the Rust hardware test to verify it fails**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml runtime_hardware --lib`
Expected: FAIL because no scanner backend/profile field/scan activity command exists yet.

- [ ] **Step 3: Implement the scanner backend**

Add a bounded `runtime_scanner.rs` with:
- `ScannerBackend` trait
- `SystemScannerBackend`
- scanner candidate normalization
- best-effort scanner heuristics for HID scanner candidates

Extend `runtime_hardware.rs` with:
- scanner records in status
- `preferred_scanner_id` in profile
- combined printer/scanner status loading
- new scanner-aware diagnostics resolution
- a command to record scanner activity

- [ ] **Step 4: Re-run the Rust hardware test**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml runtime_hardware --lib`
Expected: PASS

### Task 3: Add scanner activity publication and preferred-scanner diagnostics to the desktop hook

**Files:**
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeBarcodeScanner.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeHardwareIntegration.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.barcode-scanner.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.hardware.test.tsx`

- [ ] **Step 1: Write the failing desktop hook/integration tests**

Add cases proving:
- native scanner `attention_required` posture wins once the packaged session is live/unlocked
- scan detection publishes activity through the hardware bridge
- hardware status exposes preferred scanner inventory/profile information

- [ ] **Step 2: Run the targeted desktop tests to verify they fail**

Run: `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeWorkspace.barcode-scanner.test.tsx src/control-plane/StoreRuntimeWorkspace.hardware.test.tsx`
Expected: FAIL because no hardware-aware scanner merge or scan-activity publication exists yet.

- [ ] **Step 3: Implement the minimal hook/integration changes**

Add:
- hardware diagnostics inputs to `useStoreRuntimeBarcodeScanner`
- optional scan-activity callback on accepted scans
- hardware integration support for:
  - preferred scanner assignment
  - scan-activity publication

- [ ] **Step 4: Re-run the targeted desktop tests**

Run: `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeWorkspace.barcode-scanner.test.tsx src/control-plane/StoreRuntimeWorkspace.hardware.test.tsx`
Expected: PASS

### Task 4: Surface preferred-scanner posture in the desktop UI

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.test.tsx`

- [ ] **Step 1: Write the failing UI test**

Add coverage proving the barcode section renders:
- discovered scanner label
- transport
- preferred assignment action
- clear preferred action when assigned

- [ ] **Step 2: Run the UI test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- src/control-plane/StoreBarcodeLookupSection.test.tsx`
Expected: FAIL because the workspace/UI do not expose scanner inventory or preferred assignment yet.

- [ ] **Step 3: Implement the UI wiring**

Expose from the workspace:
- `runtimeHardwareScanners`
- `runtimePreferredScannerId`
- `assignRuntimePreferredScanner`

Render:
- scanner count / preferred scanner in the shell section
- scanner inventory and actions in the barcode lookup section

- [ ] **Step 4: Re-run the UI test**

Run: `npm run test --workspace @store/store-desktop -- src/control-plane/StoreBarcodeLookupSection.test.tsx`
Expected: PASS

### Task 5: Verify, document, and close the slice

**Files:**
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`

- [ ] **Step 1: Run full desktop verification**

Run:
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
- `git -c core.safecrlf=false diff --check`

Expected: PASS

- [ ] **Step 2: Update docs**

Record the HID scanner inventory slice in `WORKLOG.md` and update `TASK_LEDGER.md` to reflect `V2-002` status based on the remaining richer-device-input work after this slice.

- [ ] **Step 3: Commit docs + implementation**

Suggested commit sequence:

```bash
git add docs/superpowers/specs/2026-04-15-store-desktop-hid-scanner-design.md docs/superpowers/plans/2026-04-15-store-desktop-hid-scanner.md
git commit -m "docs: add desktop hid scanner design"

git add apps/store-desktop docs/WORKLOG.md docs/TASK_LEDGER.md
git commit -m "feat: add desktop hid scanner inventory"
```
