# Store Desktop Reviewed Receiving Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a board-driven reviewed receiving workflow to Store Desktop so branch operators can create goods receipts through the existing control-plane model.

**Architecture:** Extend the desktop client with receiving routes, extract request orchestration into a new `storeReceivingActions.ts`, keep `useStoreRuntimeWorkspace.ts` thin by exposing receiving state/actions, and mount a new `StoreReceivingSection.tsx` beside the other inventory-operation surfaces.

**Tech Stack:** React 19, Vitest, Testing Library, TypeScript, Vite, control-plane REST client

---

### Task 1: Add failing receiving client tests

**Files:**
- Create: `apps/store-desktop/src/control-plane/client.receiving.test.ts`
- Modify: `apps/store-desktop/src/control-plane/client.ts`

- [ ] **Step 1: Write the failing test**

Cover:
- `getReceivingBoard`
- `createGoodsReceipt`
- `listGoodsReceipts`

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- client.receiving.test.ts`

- [ ] **Step 3: Implement minimal client support**

Add thin wrappers only.

- [ ] **Step 4: Re-run the targeted client test**

Run: `npm run test --workspace @store/store-desktop -- client.receiving.test.ts`

- [ ] **Step 5: Commit**

`git commit -m "test: add desktop receiving client coverage"`

### Task 2: Add failing workspace receiving flow test

**Files:**
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.receiving.test.tsx`
- Create: `apps/store-desktop/src/control-plane/storeReceivingActions.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`

- [ ] **Step 1: Write the failing workspace flow test**

Cover:
- session bootstrap
- load receiving board
- select PO
- edit reviewed lines
- create goods receipt
- refresh board, goods receipts, and inventory snapshot

- [ ] **Step 2: Run the workspace test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.receiving.test.tsx`

- [ ] **Step 3: Implement receiving action helpers and workspace state**

Add only the state and actions needed for the tested flow.

- [ ] **Step 4: Re-run the workspace test**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.receiving.test.tsx`

- [ ] **Step 5: Commit**

`git commit -m "feat: add desktop receiving workspace actions"`

### Task 3: Add failing receiving section test

**Files:**
- Create: `apps/store-desktop/src/control-plane/StoreReceivingSection.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreReceivingSection.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`

- [ ] **Step 1: Write the failing section test**

Cover:
- board-driven selection UI
- reviewed line inputs
- create receipt button state
- latest goods receipt rendering after creation

- [ ] **Step 2: Run the section test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- StoreReceivingSection.test.tsx`

- [ ] **Step 3: Implement the minimal section and mount it**

Keep the new UI self-contained and align with desktop section patterns.

- [ ] **Step 4: Re-run the section test**

Run: `npm run test --workspace @store/store-desktop -- StoreReceivingSection.test.tsx`

- [ ] **Step 5: Commit**

`git commit -m "feat: add desktop reviewed receiving workflow"`

### Task 4: Verify and document

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Update worklog**

Add one concise bullet for the desktop reviewed receiving slice.

- [ ] **Step 2: Run targeted receiving verification**

Run:
- `npm run test --workspace @store/store-desktop -- client.receiving.test.ts StoreRuntimeWorkspace.receiving.test.tsx StoreReceivingSection.test.tsx`

- [ ] **Step 3: Run full desktop verification**

Run:
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `git -c core.safecrlf=false diff --check`

- [ ] **Step 4: Prepare integration**

If everything is green, merge/push through the normal completion flow.
