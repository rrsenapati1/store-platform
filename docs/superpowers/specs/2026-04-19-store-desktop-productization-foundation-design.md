# Store Desktop Productization Foundation Design

Date: 2026-04-19
Owner: Codex
Status: Drafted after design approval

## Goal

Turn `store-desktop` from a broad section-stacked control-plane workspace into a product-quality branch runtime centered on cashier billing.

This slice is not about adding more backend authority. It is about making the existing runtime understandable, navigable, and credible as enterprise retail software.

When this slice is complete:

- a cashier should know what to do immediately after launch
- the billing flow should feel like a real POS runtime
- branch operations should still exist, but should no longer clutter the primary sell flow
- the resulting visual and component language should be reusable by later `owner-web` and `store-mobile` productization work

## Problem Statement

The current runtime is functionally wide but product-wise weak.

Today:

- `store-desktop` exposes many capabilities in one large workspace
- billing, customer, attendance, cashier-session, branch operations, reporting, and runtime health all compete for attention at once
- the runtime reads like a control surface assembled from sections rather than a coherent cashier product
- visual hierarchy is weak, workflow hierarchy is weak, and the operator does not get one dominant next action

This creates the exact failure mode the user called out: the app feels operationally capable but not enterprise-grade in design, flow, or presentation.

## Chosen Model

The accepted model is:

- `store-desktop` becomes the anchor product-quality surface
- the first rewrite is `cashier billing first`
- the redesign includes the `entry posture`, not only the in-session shell
- runtime navigation becomes `role-aware`
- the cashier surface stays tightly focused on `one active cart`
- a reusable design-system foundation is introduced as part of this work, but the first full productization target remains `store-desktop`

This is a `workflow-first shell redesign`, not a cosmetic polish pass.

## Scope

### In Scope

- product-quality rewrite of the `store-desktop` runtime shell
- redesigned `entry` posture for:
  - actor sign-in
  - attendance
  - cashier session open/resume
  - branch/device/session context
- new runtime navigation model with:
  - `Sell`
  - `Returns`
  - `Operations`
  - `Manager`
- focused `Sell` screen built around:
  - scan/add flow
  - one active cart
  - customer selection
  - pricing/tax/discount summary
  - payment posture
  - session/device/online state
- shared UI primitives needed to support the new shell and commerce posture
- preservation of the current backend contracts and control-plane authority wherever possible

### Out Of Scope

- full `owner-web` redesign
- full `platform-admin` redesign
- full `store-mobile` visual unification
- parked carts / held carts
- multi-cart cashier workflow
- receipt-history UX overhaul
- major backend domain redesign
- production identity-provider redesign
- advanced animation-heavy polish beyond what materially improves hierarchy and usability

## Product Principles

The rewrite should follow these principles:

1. `Workflow over module exposure`
   - primary runtime flow comes first
   - secondary operations are discoverable but not omnipresent
2. `One screen, one job`
   - every top-level screen must have one dominant purpose
3. `Financial truth must stay visible`
   - totals, discounts, tax, payable posture, and payment state must remain legible through the whole transaction
4. `Touch-first with scanner acceleration`
   - optimize for POS hardware and fast item entry
   - preserve keyboard/scanner efficiency
5. `Enterprise restraint`
   - no dashboard-card sprawl
   - no decorative SaaS noise
   - information density with clear hierarchy

## Information Architecture

`store-desktop` should become a runtime shell with five top-level areas:

### 1. Entry

Purpose:

- get the operator from launch to a valid working posture

Contains:

- actor identity
- device identity
- branch identity
- attendance state
- cashier-session state
- opening actions:
  - `Clock in`
  - `Open register`
  - `Resume selling`

This is not a generic login view. It is an operational checkpoint that explains exactly what is required before billing is allowed.

### 2. Sell

Purpose:

- own the default cashier workflow

This is the primary screen and should open by default for cashier-capable actors.

### 3. Returns

Purpose:

- handle sale return posture without polluting the active-sale experience

Returns should reuse familiar lookup patterns but remain a separate working mode.

### 4. Operations

Purpose:

- expose branch tasks that are important but not part of the live checkout loop

Contains secondary operational views such as:

- receiving
- stock count
- restock
- expiry
- barcode lookup
- sync / offline posture

### 5. Manager

Purpose:

- give branch managers oversight and action posture without turning the cashier shell into an admin dashboard

Contains:

- today’s trade posture
- cashier/session posture
- shift posture
- low-stock and exception posture
- runtime health

## Sell Screen Composition

The `Sell` screen should be the centerpiece of the rewrite.

### Primary Goal

The cashier must understand, at a glance:

- what is being sold
- who the customer is
- what pricing rules apply
- how much remains payable
- what the next action is

### Desktop Layout

The recommended model is a three-zone layout:

#### A. Scan And Cart Zone

This is the primary and widest zone.

Contains:

- scan / barcode / manual product entry
- recent match or addable product posture
- active cart lines
- quantity controls
- remove-line actions
- serialized item assignment posture
- compliance prompts inline when required

Each cart line should show:

- product name
- barcode / SKU secondary text
- MRP
- unit selling price
- quantity
- line discount posture
- final line total

#### B. Commercial Summary Zone

This is the financial truth panel.

Contains:

- selected customer summary
- loyalty posture
- store credit posture
- voucher / promotion posture
- subtotal
- discount totals
- tax
- invoice total
- remaining payable

This panel should stay visible and should not require the cashier to mentally assemble the numbers from multiple modules.

#### C. Payment And Session Zone

This is the action zone.

Contains:

- payment method selection
- provider-backed payment action
- finalize-sale CTA
- cashier/session badge
- device/branch/online-offline posture

The right action should always be obvious:

- add item
- select customer
- choose payment
- continue provider-backed payment
- finalize sale

### Touch-First Adaptation

On narrower or touch-biased layouts:

- the cart remains primary
- the commercial summary becomes a collapsible sheet or side drawer
- the payment/session zone becomes a sticky action footer or lower action rail

## Visual Direction

### Visual Thesis

Serious retail operations software with calm authority.

The product should feel:

- light
- precise
- high-contrast
- disciplined
- operationally trustworthy

It should not feel like a generic React admin dashboard or a marketing-site concept.

### Visual Language

- warm off-white / paper base surfaces
- charcoal ink text
- deep blue primary actions
- green / amber / red reserved for state and risk
- one expressive but disciplined heading face
- one utilitarian UI face

### System Rules

- one dominant visual idea per screen
- strong layout planes before card treatment
- cards only where interaction boundaries truly need them
- primary actions loud, secondary actions quiet
- status represented by compact, disciplined chips/badges
- prose minimized inside operational screens

## Shared Design-System Foundation

This slice should introduce stronger reusable primitives in `packages/ui`.

Likely additions or reworked primitives:

- runtime shell frame
- left navigation rail
- session / status strip
- command / scan bar
- transaction line item
- commercial summary block
- sticky action footer
- drawer / sheet primitives for customer and payment flows

These primitives should be designed for reuse later in:

- `owner-web`
- `store-mobile`

But this slice should not wait for those apps to be redesigned first.

## Entry Flow Design

The entry flow should be intentional and operational.

Recommended sequence:

1. identify actor
2. confirm branch/device posture
3. satisfy attendance requirement if policy requires it
4. open or resume cashier session
5. enter the `Sell` screen

The current local stub-bootstrap posture is a development convenience only. It should not drive the product design.

This redesign should produce a real runtime entry experience that can later sit behind the proper identity-provider and device-activation posture.

## Navigation And Role Visibility

Recommended shell behavior:

- persistent left rail for desktop
- compact action rail / adapted navigation for narrow widths
- role-aware visibility
- `Sell` as default home for cashier-capable actors

Cashiers should not land in a giant all-capabilities workspace.

Managers should gain access to:

- `Manager`
- selected `Operations`
- session and oversight tools

This preserves breadth without sacrificing the cashier flow.

## Implementation Boundary

This rewrite should prefer preserving domain logic and backend contracts while replacing the composition model of the UI.

Likely implementation shape:

- refactor [StoreRuntimeWorkspace.tsx](/d:/codes/projects/store/apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx) from section-stack composition into a runtime shell
- preserve and adapt existing service hooks in [useStoreRuntimeWorkspace.ts](/d:/codes/projects/store/apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts)
- refactor billing/session/attendance surfaces into productized flows rather than independent stacked sections
- add or upgrade shared UI primitives in [packages/ui/src/index.tsx](/d:/codes/projects/store/packages/ui/src/index.tsx)

The first slice should not attempt to re-architect the entire control-plane state model.

## Testing And Verification

The first productization slice should be validated at three levels:

### Component / Interaction Tests

- entry flow state changes
- sell-screen action hierarchy
- cart, customer, totals, and payment posture rendering
- role-aware nav visibility

### Existing Behavior Preservation

- cashier session gating still works
- attendance gating still works
- billing payloads and payment flows still work
- pricing preview, loyalty, store credit, and vouchers still render correctly in the new shell

### Build Verification

- `@store/store-desktop` test
- `@store/store-desktop` typecheck
- `@store/store-desktop` build
- Tauri shell check where affected

## Success Criteria

This slice is successful when:

- a cashier can launch the app and understand the required next step immediately
- the runtime feels like a POS product, not a documentation-shaped control panel
- `Sell` becomes a coherent primary workflow
- secondary branch operations no longer dominate the main runtime
- the visual/system foundation is strong enough to guide later `owner-web` and `store-mobile` productization work

## Risks

### Risk: Re-skin Without Workflow Improvement

If the work only changes colors, spacing, and cards, the result will still feel weak.

Mitigation:

- treat this as a shell and flow rewrite first
- visual polish follows workflow clarity

### Risk: Overloading The First Slice

Trying to redesign every secondary operations screen in the same pass will slow delivery and dilute the primary win.

Mitigation:

- keep the first slice centered on `Entry` and `Sell`
- move secondary areas behind navigation with minimal disruption first

### Risk: Breaking Existing Domain Flows

The runtime already has deep billing, loyalty, voucher, and compliance behavior.

Mitigation:

- preserve service hooks and payload contracts
- keep verification focused on behavior as well as presentation
