# CP-022 Packaging And Distribution Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Windows-first Store Desktop packaging contract with signed installer builds, runtime release profiles, updater support, and documented publish or rollback flow.

**Architecture:** Add a packaged release-profile resource and native release service, wire Tauri’s updater plugin through runtime-configured profile values, then layer release scripts and Windows deployment docs over the resulting bundle outputs. The packaged runtime stays environment-safe by reading bundled profile data instead of defaulting to localhost after installation.

**Tech Stack:** Tauri v2, Rust, React, Vitest, Node.js scripts, PowerShell-friendly release commands

---

### Task 1: Add packaged release-profile loading and shell exposure

**Files:**
- Create: `apps/store-desktop/src-tauri/src/runtime_release.rs`
- Create: `apps/store-desktop/src-tauri/release-profiles/dev.json`
- Create: `apps/store-desktop/src-tauri/release-profiles/staging.json`
- Create: `apps/store-desktop/src-tauri/release-profiles/prod.json`
- Modify: `apps/store-desktop/src-tauri/build.rs`
- Modify: `apps/store-desktop/src-tauri/tauri.conf.json`
- Modify: `apps/store-desktop/src-tauri/src/runtime_control_plane_origin.rs`
- Modify: `apps/store-desktop/src-tauri/src/runtime_shell.rs`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`
- Test: `apps/store-desktop/src-tauri/src/runtime_release.rs`
- Test: `apps/store-desktop/src/runtime-shell/storeRuntimeShellAdapter.test.ts`

- [ ] **Step 1: Write the failing native and adapter tests**
- [ ] **Step 2: Run the targeted tests to verify red**
- [ ] **Step 3: Implement release-profile generation in `build.rs`**
- [ ] **Step 4: Implement native release-profile loading and packaged shell fields**
- [ ] **Step 5: Run the targeted tests to verify green**
- [ ] **Step 6: Commit**

### Task 2: Add updater plugin integration and desktop updater posture

**Files:**
- Create: `apps/store-desktop/src-tauri/src/runtime_updater.rs`
- Create: `apps/store-desktop/src/runtime-updater/storeRuntimeUpdater.ts`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeReleaseSection.tsx`
- Modify: `apps/store-desktop/src-tauri/Cargo.toml`
- Modify: `apps/store-desktop/package.json`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`
- Modify: `apps/store-desktop/src/runtime-shell/storeRuntimeShellContract.ts`
- Modify: `apps/store-desktop/src/runtime-shell/nativeStoreRuntimeShell.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx`
- Test: `apps/store-desktop/src/control-plane/StoreRuntimeReleaseSection.test.tsx`
- Test: `apps/store-desktop/src/runtime-shell/storeRuntimeShellAdapter.test.ts`
- Test: `apps/store-desktop/src-tauri/src/runtime_updater.rs`

- [ ] **Step 1: Write the failing updater tests**
- [ ] **Step 2: Run the targeted tests to verify red**
- [ ] **Step 3: Add updater plugin dependencies and native commands**
- [ ] **Step 4: Expose updater posture and actions to the React runtime**
- [ ] **Step 5: Run the targeted tests to verify green**
- [ ] **Step 6: Commit**

### Task 3: Add release build and manifest tooling

**Files:**
- Create: `scripts/build-store-desktop-release.mjs`
- Create: `scripts/generate-store-desktop-update-manifest.mjs`
- Create: `scripts/__fixtures__/store-desktop-update-artifacts/README.md`
- Modify: `apps/store-desktop/package.json`
- Test: `scripts/generate-store-desktop-update-manifest.test.mjs`

- [ ] **Step 1: Write the failing manifest-generation test**
- [ ] **Step 2: Run the targeted test to verify red**
- [ ] **Step 3: Implement the manifest generator**
- [ ] **Step 4: Implement the release-build wrapper and npm scripts**
- [ ] **Step 5: Run the targeted test and script `--help` checks to verify green**
- [ ] **Step 6: Commit**

### Task 4: Document Windows packaging, channels, and rollback posture

**Files:**
- Create: `docs/runbooks/store-desktop-packaging-distribution.md`
- Modify: `apps/store-desktop/src-tauri/README.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Write the runbook covering prerequisites, signed build flow, profile selection, manifest publication, and rollback**
- [ ] **Step 2: Update desktop shell docs with release-profile and updater behavior**
- [ ] **Step 3: Mark `CP-022` done in the ledger and add the worklog entry**
- [ ] **Step 4: Commit**

### Task 5: Verify the full packaging slice

**Files:**
- Modify only if verification exposes gaps

- [ ] **Step 1: Run `npm run test --workspace @store/store-desktop`**
- [ ] **Step 2: Run `npm run typecheck --workspace @store/store-desktop`**
- [ ] **Step 3: Run `npm run build --workspace @store/store-desktop`**
- [ ] **Step 4: Run `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`**
- [ ] **Step 5: Run `node scripts/generate-store-desktop-update-manifest.mjs --help`**
- [ ] **Step 6: Run `node scripts/build-store-desktop-release.mjs --help`**
- [ ] **Step 7: Commit the final adjustments if verification required any**
