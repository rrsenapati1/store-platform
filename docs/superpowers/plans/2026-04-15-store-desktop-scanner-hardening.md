# Store Desktop Scanner Hardening Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden Store Desktop scanner posture by extending the existing keyboard-wedge path with richer diagnostics, shell visibility, and barcode-lookup setup guidance.

**Architecture:** Keep the existing wedge-capture hook and barcode lookup flow. Extend the runtime hardware diagnostics contract and native persisted hardware state with richer scanner fields, publish scan metadata from the capture hook, and surface the posture in the shell identity and barcode lookup sections.

**Tech Stack:** TypeScript, React, Vitest, Rust/Tauri.

---

### Task 1: Add failing tests for richer diagnostics and UI posture

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.barcode-scanner.test.tsx`
- Modify: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareAdapter.test.ts`
- Create or modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.hardware.test.tsx`
- Modify: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`

- [ ] **Step 1: Add hook tests for scanner diagnostics metadata**
- [ ] **Step 2: Add hardware contract tests for the new diagnostics fields**
- [ ] **Step 3: Add UI tests for shell/barcode scanner posture**
- [ ] **Step 4: Add or extend Rust tests for default diagnostics shape**
- [ ] **Step 5: Run targeted tests and verify they fail**

### Task 2: Implement richer diagnostics in the web/native contracts

**Files:**
- Modify: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareContract.ts`
- Modify: `apps/store-desktop/src/runtime-hardware/browserStoreRuntimeHardware.ts`
- Modify: `apps/store-desktop/src/runtime-hardware/storeRuntimeHardwareAdapter.ts`
- Modify: `apps/store-desktop/src-tauri/src/runtime_hardware.rs`

- [ ] **Step 1: Extend the TypeScript diagnostics contract**
- [ ] **Step 2: Extend browser/native adapters**
- [ ] **Step 3: Extend the Rust persisted diagnostics shape**
- [ ] **Step 4: Re-run targeted adapter/native tests and make them pass**

### Task 3: Publish scanner metadata from the capture hook

**Files:**
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeBarcodeScanner.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`

- [ ] **Step 1: Add richer scanner state and last-scan preview to the hook**
- [ ] **Step 2: Thread that posture into the workspace state**
- [ ] **Step 3: Re-run targeted hook/workspace tests**

### Task 4: Surface scanner posture in shell and barcode lookup UI

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`

- [ ] **Step 1: Add shell scanner diagnostics rows**
- [ ] **Step 2: Add compact barcode lookup diagnostics card**
- [ ] **Step 3: Re-run targeted UI tests and keep them green**

### Task 5: Update worklog and run full verification

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Record the slice in the worklog**
- [ ] **Step 2: Run `npm run test --workspace @store/store-desktop`**
- [ ] **Step 3: Run `npm run typecheck --workspace @store/store-desktop`**
- [ ] **Step 4: Run `npm run build --workspace @store/store-desktop`**
- [ ] **Step 5: Run `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`**
- [ ] **Step 6: Run `git -c core.safecrlf=false diff --check`**
- [ ] **Step 7: Commit docs/implementation separately and push**
