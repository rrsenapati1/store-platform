# Store Desktop Reviewed Expiry Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the desktop runtime's direct expiry write-off shortcut with the real reviewed expiry session workflow already supported by the control plane.

**Architecture:** Extend the desktop control-plane client for expiry review board and session lifecycle calls, then rework the runtime workspace and section UI so desktop operators create, review, approve, or cancel expiry sessions instead of directly mutating the first expiring lot. Keep the backend authority model unchanged and reuse the existing control-plane reviewed expiry lifecycle.

**Tech Stack:** TypeScript, React, Vitest, Testing Library, existing control-plane batch expiry routes, `@store/types`.

---

### Task 1: Extend Desktop Control-Plane Client For Reviewed Expiry

**Files:**
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Create: `apps/store-desktop/src/control-plane/client.batch-expiry.test.ts`

- [ ] **Step 1: Write the failing client tests**

Add tests for:
- loading the batch expiry board
- creating an expiry review session
- recording a reviewed quantity/reason
- approving a reviewed session
- canceling a reviewed session

- [ ] **Step 2: Run targeted client tests to verify they fail**

Run: `npm run test --workspace @store/store-desktop -- client.batch-expiry.test.ts`

- [ ] **Step 3: Write minimal client implementation**

Extend `storeControlPlaneClient` with:
- `getBatchExpiryBoard`
- `createBatchExpirySession`
- `recordBatchExpirySession`
- `approveBatchExpirySession`
- `cancelBatchExpirySession`

Reuse the existing `ControlPlaneBatchExpiryBoard`, `ControlPlaneBatchExpiryReviewSession`, and `ControlPlaneBatchExpiryReviewApproval` types from `@store/types`.

- [ ] **Step 4: Run targeted client tests to verify they pass**

Run: `npm run test --workspace @store/store-desktop -- client.batch-expiry.test.ts`

### Task 2: Add Reviewed Expiry State And Actions To The Runtime Workspace

**Files:**
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.batch-expiry.test.tsx`

- [ ] **Step 1: Write the failing workspace tests**

Extend the batch-expiry workspace test to prove desktop can:
- load the expiry report and review board
- create a review session for a lot
- record proposed quantity/reason
- approve a session
- cancel a session

- [ ] **Step 2: Run targeted workspace tests to verify they fail**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.batch-expiry.test.tsx`

- [ ] **Step 3: Write minimal workspace implementation**

Add reviewed expiry workspace state for:
- `batchExpiryBoard`
- `activeBatchExpirySession`
- `expiryProposedQuantity`
- `expirySessionNote`
- `expiryReviewNote`

Add actions for:
- loading the expiry board
- creating a session for a selected lot
- recording the active session review
- approving the active session
- canceling the active session

Keep `latestBatchWriteOff` as the post-approval result surface.

- [ ] **Step 4: Run targeted workspace tests to verify they pass**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.batch-expiry.test.tsx`

### Task 3: Replace The Shortcut Expiry UI With Reviewed Session Controls

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreBatchExpirySection.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreBatchExpirySection.test.tsx`

- [ ] **Step 1: Write the failing section tests**

Add tests for:
- report and review-board visibility
- selected lot / active session display
- create, record, approve, and cancel controls
- latest approved write-off showing only after approval

- [ ] **Step 2: Run targeted section tests to verify they fail**

Run: `npm run test --workspace @store/store-desktop -- StoreBatchExpirySection.test.tsx`

- [ ] **Step 3: Write minimal section implementation**

Replace:
- `Expiry write-off quantity`
- `Expiry write-off reason`
- `Write off first expiring lot`

with a reviewed-session UI that:
- loads report + board
- opens a review session for a lot
- captures proposed quantity, reason, session note, and review note
- records review
- approves or cancels the session

- [ ] **Step 4: Run targeted section tests to verify they pass**

Run: `npm run test --workspace @store/store-desktop -- StoreBatchExpirySection.test.tsx`

### Task 4: Verify The Desktop Slice End-To-End And Record It

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Run focused desktop expiry verification**

Run:

```bash
npm run test --workspace @store/store-desktop -- client.batch-expiry.test.ts StoreRuntimeWorkspace.batch-expiry.test.tsx StoreBatchExpirySection.test.tsx
```

- [ ] **Step 2: Run full desktop verification**

Run:

```bash
npm run test --workspace @store/store-desktop
npm run typecheck --workspace @store/store-desktop
npm run build --workspace @store/store-desktop
git -c core.safecrlf=false diff --check
```

- [ ] **Step 3: Update the worklog**

Record that Store Desktop batch expiry now follows the reviewed expiry session lifecycle instead of using the direct write-off shortcut.
