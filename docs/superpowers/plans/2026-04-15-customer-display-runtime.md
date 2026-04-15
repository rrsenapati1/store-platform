# Customer Display Runtime Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Store Desktop customer-display slice as a terminal-owned, read-only second-window experience with packaged-runtime window controls and browser-safe fallback.

**Architecture:** Add a small customer-display module inside `apps/store-desktop` that derives a serialized payload from cashier state and renders it in a dedicated display route. The packaged Tauri shell only manages the display window lifecycle; the cashier runtime remains the single writer for checkout state and display updates.

**Tech Stack:** React 19, Vitest, Tauri 2, Rust, existing Store Desktop runtime shell

---

### Task 1: Add The Customer-Display Model And Route Selection

**Files:**
- Create: `apps/store-desktop/src/customer-display/customerDisplayModel.ts`
- Create: `apps/store-desktop/src/customer-display/customerDisplayModel.test.ts`
- Modify: `apps/store-desktop/src/App.tsx`

- [ ] **Step 1: Write the failing customer-display model tests**

Add `customerDisplayModel.test.ts` covering:

- idle payload when no sale exists
- active-cart payload with lines and totals
- sale-complete payload with paid amount and cash change

- [ ] **Step 2: Run the model test to verify it fails**

Run:

```powershell
npm run test --workspace @store/store-desktop -- customerDisplayModel.test.ts
```

Expected: FAIL because the model does not exist yet.

- [ ] **Step 3: Implement the minimal model and route selection**

Add:

- `CustomerDisplayState` types
- payload builders for idle/cart/complete
- `App.tsx` route/query switch to render customer-display route when requested

- [ ] **Step 4: Re-run the model test**

Run:

```powershell
npm run test --workspace @store/store-desktop -- customerDisplayModel.test.ts
```

Expected: PASS

- [ ] **Step 5: Commit the model slice**

```powershell
git add apps/store-desktop/src/App.tsx apps/store-desktop/src/customer-display
git commit -m "feat: add customer display model"
```

### Task 2: Add The Customer-Display Controller And UI

**Files:**
- Create: `apps/store-desktop/src/customer-display/customerDisplayRoute.tsx`
- Create: `apps/store-desktop/src/customer-display/useCustomerDisplayController.ts`
- Create: `apps/store-desktop/src/customer-display/customerDisplayRoute.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`

- [ ] **Step 1: Write the failing display route/controller tests**

Add a route test covering:

- idle rendering without cashier sale state
- active cart rendering after a sale is created
- sale-complete rendering when paid amounts are present

- [ ] **Step 2: Run the route test to verify it fails**

Run:

```powershell
npm run test --workspace @store/store-desktop -- customerDisplayRoute.test.tsx
```

Expected: FAIL because the route/controller do not exist.

- [ ] **Step 3: Implement the controller and display UI**

Add:

- customer-display controller hook
- read-only customer-display route
- workspace state needed to open/close the display and expose current payload
- cashier-side action in the billing/workspace UI to manage the display

- [ ] **Step 4: Re-run the route/controller tests**

Run:

```powershell
npm run test --workspace @store/store-desktop -- customerDisplayRoute.test.tsx
```

Expected: PASS

- [ ] **Step 5: Commit the controller/UI slice**

```powershell
git add apps/store-desktop/src/customer-display apps/store-desktop/src/control-plane apps/store-desktop/src/App.tsx
git commit -m "feat: add customer display route"
```

### Task 3: Add Packaged-Runtime Window Controls

**Files:**
- Create: `apps/store-desktop/src/customer-display/nativeStoreCustomerDisplay.ts`
- Create: `apps/store-desktop/src/customer-display/nativeStoreCustomerDisplay.test.ts`
- Create: `apps/store-desktop/src-tauri/src/runtime_customer_display.rs`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`

- [ ] **Step 1: Write the failing native bridge tests**

Add:

- TypeScript test for the JS adapter calling open/close commands
- Rust unit tests for packaged-runtime open/close behavior

- [ ] **Step 2: Run the bridge tests to verify they fail**

Run:

```powershell
npm run test --workspace @store/store-desktop -- nativeStoreCustomerDisplay.test.ts
cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml runtime_customer_display --lib
```

Expected: FAIL because the bridge and commands do not exist.

- [ ] **Step 3: Implement the minimal native window boundary**

Add:

- JS adapter for open/close commands
- Tauri command handlers for opening/closing the customer-display window
- safe reuse if the window is already open
- dev/test-compatible URL/route targeting

- [ ] **Step 4: Re-run the bridge tests**

Run:

```powershell
npm run test --workspace @store/store-desktop -- nativeStoreCustomerDisplay.test.ts
cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml runtime_customer_display --lib
```

Expected: PASS

- [ ] **Step 5: Commit the window-control slice**

```powershell
git add apps/store-desktop/src/customer-display apps/store-desktop/src-tauri/src
git commit -m "feat: add customer display window controls"
```

### Task 4: Verify The Full Desktop Slice And Update Docs

**Files:**
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`
- Modify: `apps/store-desktop/README.md` (if needed)

- [ ] **Step 1: Update the ledger/worklog for customer-display progress**

Reflect that `V2-001` now includes customer-display runtime progress.

- [ ] **Step 2: Run the full desktop verification stack**

Run:

```powershell
npm run test --workspace @store/store-desktop
npm run typecheck --workspace @store/store-desktop
npm run build --workspace @store/store-desktop
cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib
git diff --check
```

Expected: PASS

- [ ] **Step 3: Commit the completed customer-display slice**

```powershell
git add apps/store-desktop docs
git commit -m "feat: add customer display runtime"
```
