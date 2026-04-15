# Store Desktop Cashfree QR Rendering Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a real Cashfree UPI QR image and relative expiry countdown in Store Desktop and the customer display.

**Architecture:** Add one shared QR-rendering component and one shared expiry formatter in `apps/store-desktop`, then reuse them in the cashier billing section and customer-display route without changing the existing payment-session control-plane workflow.

**Tech Stack:** React, TypeScript, Vitest, Vite, local QR rendering library

---

### Task 1: Write Failing Presentation Tests First

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx`
- Modify: `apps/store-desktop/src/customer-display/customerDisplayRoute.test.tsx`

- [ ] Add a failing billing test that expects a scannable QR image for active Cashfree sessions.
- [ ] Add a failing customer-display test that expects a customer-facing QR image for active QR state.
- [ ] Assert `Expires in ...` copy so the slice also upgrades expiry presentation.
- [ ] Run the targeted Vitest command and confirm the failures are caused by missing QR rendering.

### Task 2: Add Shared QR Rendering Utilities

**Files:**
- Create: `apps/store-desktop/src/customer-display/paymentQr.tsx`
- Modify: `apps/store-desktop/package.json`

- [ ] Add a local QR rendering dependency instead of relying on an external QR image service.
- [ ] Implement one shared QR image component with accessible `img` output.
- [ ] Implement a shared relative-expiry formatter/hook for `Expires in ...` posture.
- [ ] Keep the utility local to Store Desktop so customer display and cashier UI stay synchronized.

### Task 3: Update Cashier And Customer Display Surfaces

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Modify: `apps/store-desktop/src/customer-display/customerDisplayRoute.tsx`

- [ ] Replace raw-payload-only presentation in the billing section with a real QR image plus relative expiry.
- [ ] Replace raw-payload-only presentation in the customer display with a larger QR image and customer-facing copy.
- [ ] Keep the existing retry/cancel/manual-fallback behavior unchanged.
- [ ] Preserve raw payload visibility in smaller text for operator fallback/support use.

### Task 4: Verify And Record The Slice

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] Add a `V2-003` worklog entry for the QR-rendering upgrade.
- [ ] Run:
  - `npm run test --workspace @store/store-desktop -- StoreBillingSection.payment-session.test.tsx customerDisplayRoute.test.tsx`
  - `npm run test --workspace @store/store-desktop`
  - `npm run typecheck --workspace @store/store-desktop`
  - `npm run build --workspace @store/store-desktop`
  - `git -c core.safecrlf=false diff --check`
- [ ] Commit the docs/spec/plan and implementation once verification is green.
