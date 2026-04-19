# Store Desktop Productization Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `store-desktop` into a product-quality branch runtime centered on entry posture and cashier billing, while preserving the existing control-plane authority and runtime business behavior.

**Architecture:** Keep `useStoreRuntimeWorkspace.ts` as the domain/state authority for this slice, but stop using it as the rendering surface. Introduce a new runtime shell, entry flow, role-aware navigation, and sell-first composition layer on top of the current state/actions. Add reusable layout and commerce primitives in `packages/ui`, then recompose the existing billing, attendance, cashier-session, returns, operations, and manager surfaces under the new shell instead of stacking every section in one page.

**Tech Stack:** React, TypeScript, Vite, Vitest, Tauri, existing control-plane API hooks, shared `@store/ui`

---

## File Structure

### Large-file governance

- `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
  - Classification: `mixed-responsibility`
  - Threshold: `2901` lines (`>2000`)
  - Rule: do not add shell composition, layout decisions, or new view-specific transforms here; keep it as a state/action seam and move presentation shaping into focused files.
- `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
  - Classification: `mixed-responsibility`
  - Threshold: `687` lines
  - Rule: do not keep expanding this into the new POS screen; extract sell-surface panels around it and leave only logic that truly belongs to the legacy section wrapper.

### Shared UI

- Create: `packages/ui/src/runtimeShell.tsx`
  - Runtime shell frame, left rail, top status strip, section title block, and sticky action footer primitives.
- Create: `packages/ui/src/commerce.tsx`
  - Transaction line item, totals block, compact status chip row, and drawer/sheet wrapper primitives for POS flows.
- Modify: `packages/ui/src/index.tsx`
  - Re-export the new primitives while keeping existing exports stable.
- Modify: `packages/ui/src/index.test.tsx`
  - Cover the new shell and commerce primitives.

### Store Desktop shell and routing

- Create: `apps/store-desktop/src/control-plane/storeRuntimeScreens.ts`
  - Shared screen IDs and role-visibility helpers for `entry`, `sell`, `returns`, `operations`, and `manager`.
- Create: `apps/store-desktop/src/control-plane/storeRuntimeLayout.tsx`
  - Orchestrates shell chrome, role-aware nav, and screen switching.
- Create: `apps/store-desktop/src/control-plane/storeRuntimeEntrySurface.tsx`
  - Productized entry surface for actor, attendance, cashier-session, and resume posture.
- Create: `apps/store-desktop/src/control-plane/storeRuntimeSellSurface.tsx`
  - Top-level sell workflow composition.
- Create: `apps/store-desktop/src/control-plane/storeRuntimeSellCartPanel.tsx`
  - Scan/add posture and cart-line composition.
- Create: `apps/store-desktop/src/control-plane/storeRuntimeSellSummaryPanel.tsx`
  - Customer, discount, tax, total, loyalty, credit, and voucher posture.
- Create: `apps/store-desktop/src/control-plane/storeRuntimeSellPaymentPanel.tsx`
  - Payment selector, provider-backed checkout action state, finalize CTA, and runtime status.
- Create: `apps/store-desktop/src/control-plane/storeRuntimeOperationsSurface.tsx`
  - Wrapper surface that groups existing receiving/stock/expiry/offline tools under one screen.
- Create: `apps/store-desktop/src/control-plane/storeRuntimeManagerSurface.tsx`
  - Wrapper surface that groups the manager dashboard, decision support, and runtime oversight.
- Create: `apps/store-desktop/src/control-plane/storeRuntimeReturnsSurface.tsx`
  - Wrapper surface around returns and exchange posture.
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
  - Replace the section stack with the new runtime shell composition.
- Modify: `apps/store-desktop/src/App.tsx`
  - Keep customer display split, but route the main app through the new runtime shell.

### Existing section adapters

- Modify: `apps/store-desktop/src/control-plane/StoreAttendanceSection.tsx`
  - Support compact embedding inside the new entry surface.
- Modify: `apps/store-desktop/src/control-plane/StoreCashierSessionSection.tsx`
  - Support compact embedding inside the new entry surface.
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
  - Reuse existing business controls inside the new sell surface or expose minimal embedded fragments.
- Modify: `apps/store-desktop/src/control-plane/StoreReturnsSection.tsx`
  - Fit cleanly inside the returns surface.
- Modify: `apps/store-desktop/src/control-plane/StoreBranchOperationsDashboardSection.tsx`
  - Fit inside the manager surface.
- Modify: `apps/store-desktop/src/control-plane/StoreBranchDecisionSupportSection.tsx`
  - Fit inside the manager surface.
- Modify: `apps/store-desktop/src/control-plane/StoreReceivingSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreStockCountSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRestockSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBatchExpirySection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreOfflineContinuitySection.tsx`
  - Each should support being hosted inside `Operations` without assuming full-page top-level layout.

### Tests

- Create: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.product-shell.test.tsx`
  - New shell/navigation/entry coverage.
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeEntrySurface.test.tsx`
  - Entry posture coverage for sign-in, attendance, cashier session, and resume state.
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeSellSurface.test.tsx`
  - Sell layout, action hierarchy, and totals/payment posture coverage.
- Modify: `apps/store-desktop/src/App.test.tsx`
  - Align smoke assertions with the new sell-first runtime.
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.attendance.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.cashier-sessions.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.shell.test.tsx`
  - Preserve domain behavior under the new UI composition.

### Docs

- Modify: `docs/WORKLOG.md`
  - Record the productization slice and verification commands.
- Modify: `docs/TASK_LEDGER.md`
  - Advance ledger state only if this slice creates a new visible track marker.
- Modify: `docs/runbooks/dev-workflow.md`
  - Update screenshots/URLs/workflow notes only if the runtime shell changes the local operator path materially.

## Task 1: Add failing shell and entry tests

**Files:**
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.product-shell.test.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeEntrySurface.test.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeSellSurface.test.tsx`
- Modify: `apps/store-desktop/src/App.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.shell.test.tsx`

- [ ] **Step 1: Write the failing product-shell smoke test**

Create `StoreRuntimeWorkspace.product-shell.test.tsx` to assert that the runtime now renders:

- a persistent runtime navigation rail
- `Sell` as the default active screen for cashier-capable actors
- secondary screens `Returns`, `Operations`, and `Manager` only when role posture allows them

Use the same mocked fetch/session pattern already used in `App.test.tsx`.

- [ ] **Step 2: Write the failing entry-surface tests**

Create `StoreRuntimeEntrySurface.test.tsx` to cover:

- signed-out runtime showing the actor/bootstrap posture
- attendance required before cashier open
- open-cashier CTA disabled until the attendance and opening-float gate is satisfied
- active cashier session switching the CTA posture to `Resume selling`

Use explicit assertions like:

```tsx
expect(screen.getByText('Open register')).toBeInTheDocument();
expect(screen.getByRole('button', { name: 'Resume selling' })).toBeDisabled();
```

- [ ] **Step 3: Write the failing sell-surface tests**

Create `StoreRuntimeSellSurface.test.tsx` to cover:

- scan/add and cart posture on the primary panel
- customer and totals posture in the summary panel
- payment method and finalize-sale posture in the action panel
- sticky primary action hierarchy when a provider-backed payment session is active

- [ ] **Step 4: Update the app smoke test to expect the new shell**

Modify `apps/store-desktop/src/App.test.tsx` so the current smoke path asserts for:

- entry/runtime shell
- active `Sell` screen
- productized billing posture instead of the old section-stack labels

- [ ] **Step 5: Run the focused tests to verify they fail**

Run:

- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeWorkspace.product-shell.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeEntrySurface.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeSellSurface.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/App.test.tsx`

Expected: FAIL with missing shell components, missing entry surface, and outdated app expectations.

- [ ] **Step 6: Commit**

```bash
git add apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.product-shell.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeEntrySurface.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeSellSurface.test.tsx apps/store-desktop/src/App.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.shell.test.tsx
git commit -m "test: add store desktop product shell coverage"
```

## Task 2: Add shared runtime-shell and commerce primitives

**Files:**
- Create: `packages/ui/src/runtimeShell.tsx`
- Create: `packages/ui/src/commerce.tsx`
- Modify: `packages/ui/src/index.tsx`
- Modify: `packages/ui/src/index.test.tsx`

- [ ] **Step 1: Write the failing shared-UI tests**

Extend `packages/ui/src/index.test.tsx` to cover:

- runtime shell frame rendering title, navigation, and status strip
- commerce totals block rendering invoice/posture rows
- transaction line item rendering product, price posture, and quantity

- [ ] **Step 2: Create the runtime-shell primitives**

Implement `packages/ui/src/runtimeShell.tsx` with focused components such as:

```tsx
export function RuntimeShellFrame(...) { ... }
export function RuntimeNavRail(...) { ... }
export function RuntimeStatusStrip(...) { ... }
export function RuntimeWorkspaceBody(...) { ... }
export function StickyActionFooter(...) { ... }
```

Keep these layout primitives neutral and reusable.

- [ ] **Step 3: Create the commerce primitives**

Implement `packages/ui/src/commerce.tsx` with focused components such as:

```tsx
export function TransactionLineItem(...) { ... }
export function CommerceTotalsBlock(...) { ... }
export function CommerceSummaryRow(...) { ... }
export function CommerceDrawer(...) { ... }
```

Use the approved visual direction:

- light surfaces
- strong typography
- restrained deep-blue action color
- compact state chips

- [ ] **Step 4: Re-export from the package barrel**

Update `packages/ui/src/index.tsx` so the new primitives are exported without breaking existing imports.

- [ ] **Step 5: Run the shared-UI tests**

Run:

- `npm run test --workspace @store/ui`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packages/ui/src/runtimeShell.tsx packages/ui/src/commerce.tsx packages/ui/src/index.tsx packages/ui/src/index.test.tsx
git commit -m "feat: add runtime shell ui primitives"
```

## Task 3: Build the new runtime shell and screen model

**Files:**
- Create: `apps/store-desktop/src/control-plane/storeRuntimeScreens.ts`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeLayout.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
- Modify: `apps/store-desktop/src/App.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.product-shell.test.tsx`

- [ ] **Step 1: Add the screen and visibility model**

Create `storeRuntimeScreens.ts` with:

```ts
export type StoreRuntimeScreenId = 'entry' | 'sell' | 'returns' | 'operations' | 'manager';
export function resolveVisibleRuntimeScreens(...) { ... }
export function resolveDefaultRuntimeScreen(...) { ... }
```

Rules:

- cashier-capable actors default to `sell`
- signed-out or gated actors route to `entry`
- manager-only areas only render when the actor has the right role/capability posture

- [ ] **Step 2: Implement the shell layout**

Create `storeRuntimeLayout.tsx` to:

- render the left navigation rail
- render the top runtime/status strip
- host the active screen body
- adapt to narrower widths without losing the primary workflow

Do not move business logic into this file; it should compose state already exposed by the workspace hook.

- [ ] **Step 3: Replace the old section stack**

Modify `StoreRuntimeWorkspace.tsx` so it:

- consumes the existing workspace hook
- chooses the active screen
- renders `storeRuntimeLayout.tsx`
- stops rendering every section in one page

Preserve the existing customer-display route split in `App.tsx`.

- [ ] **Step 4: Run the shell tests**

Run:

- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeWorkspace.product-shell.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeWorkspace.shell.test.tsx`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/store-desktop/src/control-plane/storeRuntimeScreens.ts apps/store-desktop/src/control-plane/storeRuntimeLayout.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx apps/store-desktop/src/App.tsx
git commit -m "feat: add store runtime shell"
```

## Task 4: Productize the entry posture

**Files:**
- Create: `apps/store-desktop/src/control-plane/storeRuntimeEntrySurface.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreAttendanceSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreCashierSessionSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeEntrySurface.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.attendance.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.cashier-sessions.test.tsx`

- [ ] **Step 1: Extract compact attendance and cashier-entry fragments**

Refactor `StoreAttendanceSection.tsx` and `StoreCashierSessionSection.tsx` so they can render in:

- compact embedded mode for the new entry flow
- existing standalone mode during the transition

Do not duplicate the mutation logic.

- [ ] **Step 2: Implement the entry surface**

Create `storeRuntimeEntrySurface.tsx` to render:

- actor identity
- branch/device posture
- attendance state
- cashier-session state
- primary CTA path:
  - `Start runtime session`
  - `Clock in`
  - `Open register`
  - `Resume selling`

The surface should clearly explain why selling is blocked when a gate is not satisfied.

- [ ] **Step 3: Wire entry into the shell**

Connect the `entry` screen into the runtime layout:

- default to `entry` when gating is incomplete
- advance to `sell` when the operator can work
- allow manager-capable users to navigate elsewhere only when runtime state allows it

- [ ] **Step 4: Run the entry and gating tests**

Run:

- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeEntrySurface.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeWorkspace.attendance.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeWorkspace.cashier-sessions.test.tsx`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/store-desktop/src/control-plane/storeRuntimeEntrySurface.tsx apps/store-desktop/src/control-plane/StoreAttendanceSection.tsx apps/store-desktop/src/control-plane/StoreCashierSessionSection.tsx apps/store-desktop/src/control-plane/StoreRuntimeEntrySurface.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.attendance.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.cashier-sessions.test.tsx
git commit -m "feat: add runtime entry flow"
```

## Task 5: Build the sell-first cashier surface

**Files:**
- Create: `apps/store-desktop/src/control-plane/storeRuntimeSellSurface.tsx`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeSellCartPanel.tsx`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeSellSummaryPanel.tsx`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeSellPaymentPanel.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeSellSurface.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.pricing-preview.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx`

- [ ] **Step 1: Extract cart-panel rendering**

Create `storeRuntimeSellCartPanel.tsx` to own:

- scan/add posture
- selected item/cart-line composition
- serialized/compliance inline prompts

It may reuse state and handlers from the existing billing section, but the layout responsibility should move out of `StoreBillingSection.tsx`.

- [ ] **Step 2: Extract summary-panel rendering**

Create `storeRuntimeSellSummaryPanel.tsx` to own:

- customer posture
- loyalty/store-credit/voucher/promotion posture
- subtotal/discount/tax/invoice/remaining payable rows

This panel should become the always-visible financial truth block.

- [ ] **Step 3: Extract payment-panel rendering**

Create `storeRuntimeSellPaymentPanel.tsx` to own:

- payment method selection
- provider-backed checkout action state
- finalize sale CTA
- session/device/online posture

This panel should surface one obvious next action.

- [ ] **Step 4: Compose the sell surface**

Create `storeRuntimeSellSurface.tsx` and compose the three panels into the approved three-zone layout.

Use the shared runtime-shell and commerce primitives instead of the old `SectionCard` stack.

- [ ] **Step 5: Reduce `StoreBillingSection.tsx` to reusable logic**

Modify `StoreBillingSection.tsx` so it no longer owns the full product layout.

Keep:

- reusable state helpers
- any domain-specific rendering fragments that are still needed

Move:

- primary sell-screen composition
- visual hierarchy
- totals/payment orchestration presentation

into the new sell-surface files.

- [ ] **Step 6: Run the sell-surface tests**

Run:

- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeSellSurface.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreBillingSection.pricing-preview.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreBillingSection.payment-session.test.tsx`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add apps/store-desktop/src/control-plane/storeRuntimeSellSurface.tsx apps/store-desktop/src/control-plane/storeRuntimeSellCartPanel.tsx apps/store-desktop/src/control-plane/storeRuntimeSellSummaryPanel.tsx apps/store-desktop/src/control-plane/storeRuntimeSellPaymentPanel.tsx apps/store-desktop/src/control-plane/StoreBillingSection.tsx apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx apps/store-desktop/src/control-plane/StoreRuntimeSellSurface.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx apps/store-desktop/src/control-plane/StoreBillingSection.pricing-preview.test.tsx apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx
git commit -m "feat: add sell-first runtime surface"
```

## Task 6: Re-home returns, operations, and manager screens

**Files:**
- Create: `apps/store-desktop/src/control-plane/storeRuntimeReturnsSurface.tsx`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeOperationsSurface.tsx`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeManagerSurface.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreReturnsSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreReceivingSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreStockCountSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRestockSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBatchExpirySection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreOfflineContinuitySection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBranchOperationsDashboardSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBranchDecisionSupportSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.product-shell.test.tsx`

- [ ] **Step 1: Add thin wrapper surfaces**

Create wrapper surfaces for:

- `Returns`
- `Operations`
- `Manager`

These should primarily provide:

- page title/eyebrow
- layout grouping
- appropriate use of shared shell primitives

- [ ] **Step 2: Adapt existing sections for embedded hosting**

Modify the existing section components so they no longer assume they are top-level full-page sections.

Do not redesign every internal workflow in this slice. Keep the changes shallow:

- remove redundant top-level framing where needed
- allow the new wrapper surfaces to own the page structure

- [ ] **Step 3: Wire the screens into the shell**

Connect the wrapper surfaces into `storeRuntimeLayout.tsx` using the screen model from Task 3.

- [ ] **Step 4: Run the product-shell and secondary-screen tests**

Run:

- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeWorkspace.product-shell.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreBranchOperationsDashboardSection.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreBranchDecisionSupportSection.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreReturnsSection.tsx`

Expected: PASS

If `StoreReturnsSection.tsx` has no focused test entrypoint, substitute the nearest existing returns-focused runtime test.

- [ ] **Step 5: Commit**

```bash
git add apps/store-desktop/src/control-plane/storeRuntimeReturnsSurface.tsx apps/store-desktop/src/control-plane/storeRuntimeOperationsSurface.tsx apps/store-desktop/src/control-plane/storeRuntimeManagerSurface.tsx apps/store-desktop/src/control-plane/StoreReturnsSection.tsx apps/store-desktop/src/control-plane/StoreReceivingSection.tsx apps/store-desktop/src/control-plane/StoreStockCountSection.tsx apps/store-desktop/src/control-plane/StoreRestockSection.tsx apps/store-desktop/src/control-plane/StoreBatchExpirySection.tsx apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx apps/store-desktop/src/control-plane/StoreOfflineContinuitySection.tsx apps/store-desktop/src/control-plane/StoreBranchOperationsDashboardSection.tsx apps/store-desktop/src/control-plane/StoreBranchDecisionSupportSection.tsx
git commit -m "feat: move secondary runtime flows behind navigation"
```

## Task 7: Final verification and docs

**Files:**
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/runbooks/dev-workflow.md`

- [ ] **Step 1: Update the worklog**

Record:

- the store-desktop productization foundation slice
- the new shell direction
- the verification commands actually run

- [ ] **Step 2: Update ledger or workflow docs only if the visible operator flow changed materially**

Only modify:

- `docs/TASK_LEDGER.md`
- `docs/runbooks/dev-workflow.md`

when the rewrite changes what a future operator/developer needs to know.

- [ ] **Step 3: Run the full store-desktop verification set**

Run:

- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
- `git -c core.safecrlf=false diff --check`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add docs/WORKLOG.md docs/TASK_LEDGER.md docs/runbooks/dev-workflow.md
git commit -m "docs: record store desktop productization foundation"
```
