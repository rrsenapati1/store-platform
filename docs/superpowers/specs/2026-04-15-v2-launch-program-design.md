# V2 Launch Program Design

Date: 2026-04-15  
Owner: Codex  
Status: Draft for review

## Goal

Rewrite Store's endgame from a narrower public-release target into a broader `V2 launch` program for an enterprise-grade physical retail suite.

This design replaces the idea of "ship the current desktop-first release and call it done" with a larger launch target that includes mobile/tablet runtime surfaces, richer device support, stronger store controls, deeper commercial/CRM features, vertical extensions, and harder production readiness.

## Why The Ledger Must Change

The current ledger was shaped around a viable first public release:

- packaged Store Desktop
- branch hub/spoke foundations
- offline checkout continuity
- enterprise auth, billing, infrastructure, observability, and release tooling

That is enough for a serious first release, but it is not yet a "competitive full-suite retail platform" in the sense the product direction now calls for.

There are already explicit deferred capabilities in the repo:

- future spoke device classes like `mobile_store_spoke`, `inventory_tablet_spoke`, and `customer_display`
- camera-friendly barcode normalization but no real mobile camera scanning product surface
- advanced hardware explicitly deferred, such as cash drawer, weighing scale, and payment terminal integration

The ledger therefore needs a new endgame that reflects the actual target product scope instead of leaving those capabilities as scattered future notes.

## Product Boundary

`V2 launch` remains focused on `physical retail/store operations`.

Included:

- desktop hub + spoke maturity
- mobile store runtime
- inventory tablet runtime
- customer display
- richer barcode/device input
- advanced hardware integration
- stronger retail operations
- CRM/commercial features relevant to in-store retail
- staff/branch governance
- advanced reporting/analytics
- regulated/vertical retail extensions
- deeper hardening, scale, and launch readiness

Excluded from `V2 launch`:

- e-commerce storefronts
- marketplace sync
- online ordering
- customer app
- delivery orchestration
- broader omnichannel expansion

Those should be documented explicitly as `post-V2 future work`, not mixed into the V2 critical path.

## V2 Program Principles

1. `Keep completed history intact.`
   - Existing `CP-001` through `CP-027` remain the historical foundation.
   - Already-completed work is not rewritten or hidden.

2. `Stop treating CP-028 as the final release gate for the smaller launch.`
   - `CP-028` becomes the transition point where the program formally pivots to the V2 launch target.

3. `Use a new V2 task namespace.`
   - The new work should not continue stretching the `CP-0xx` range.
   - A dedicated `V2-` series makes the program boundary obvious.

4. `Separate critical-path work from parallel required lanes.`
   - "Add everything" must not become one flat queue.
   - The ledger should distinguish what blocks the core suite from what can run in parallel and still be required before sign-off.

5. `Keep physical retail core and vertical-specific logic separate.`
   - Generic store operations stay in the retail core.
   - Pharmacy/prescription, serial-number/IMEI, and category-specific compliance stay isolated as V2 vertical extensions.

## V2 Capability Families

### 1. Runtime And Devices

This family expands Store beyond the packaged desktop hub.

Included:

- mobile store app
- inventory tablet app
- customer display
- richer QR/manual spoke pairing maturity
- role-appropriate runtime UX by device class

This is a launch-critical family because it changes what "the product" is in the field.

### 2. Barcode And Device Input

This family closes the current gap between desktop keyboard-wedge scanning and modern device input.

Included:

- camera barcode scanning
- richer HID/USB scanner support
- scan workflows tuned for mobile/tablet
- better device diagnostics and fallback posture

This is launch-critical because mobile/tablet runtimes are not credible without it.

### 3. Advanced Hardware

This family broadens Store from basic printer/scanner support into more complete retail hardware.

Included:

- cash drawer integration
- weighing scale integration
- payment terminal integration
- vendor-profile abstractions where needed
- clearer operator diagnostics and recovery posture

This remains within physical retail scope and is part of the V2 target.

### 4. Store Operations Depth

This family deepens the store-operational workflows beyond the first desktop checkout/replay baseline.

Included:

- stronger receiving/count/expiry/backroom workflows
- better assisted lookup and stock workflows
- stronger replenishment/purchase suggestions
- improved runtime/operator recovery tooling

### 5. Customer And Commercial Features

This family moves Store toward a fuller retail operating platform.

Included:

- CRM/customer profile depth
- loyalty
- promotions/discount rules
- gift cards/store credit
- multi-price tiers and related in-store commercial controls

These are part of the V2 suite because they are central to competing retail software.

### 6. Staff And Branch Controls

This family expands operational governance and branch-level control.

Included:

- attendance
- shift controls
- cashier/session governance
- branch/device policy controls
- stronger audit/export posture

### 7. Reporting And Decision Support

This family matures Store from operational system to management system.

Included:

- advanced analytics
- branch performance dashboards
- replenishment/purchase insights
- exception/decision-support views

### 8. Vertical Extensions

This family captures category-specific features without polluting the generic retail core.

Included:

- pharmacy/prescription controls
- serial-number/IMEI tracking
- category-specific compliance modules

These are in-scope for V2, but should be isolated by module and implementation track.

### 9. Hardening And Scale

This family becomes the real launch gate for V2.

Included:

- deeper security controls
- stronger recovery/backup drills
- operational maturity
- performance/load validation
- beta exit, certification, and final cutover

`CP-028` should no longer act as the terminal gate for the old smaller launch. The terminal gate moves here.

## Critical Path Vs Parallel Required Lanes

The V2 program should not be one serial queue.

### Critical Path

These shape whether the suite is broadly launchable:

- runtime surfaces
- barcode/device input
- advanced hardware
- customer/commercial features
- staff/branch controls
- reporting/operator dashboards
- hardening and scale

### Parallel But Still Required Before Sign-Off

These are required for the chosen V2 scope, but should not all sit on the same dependency chain:

- purchase suggestions and replenishment intelligence
- deeper advanced analytics
- branch policy refinement
- pharmacy/prescription controls
- serial-number/IMEI tracking
- category-specific compliance modules

The ledger should show both types clearly.

## Ledger Rewrite Strategy

### Historical Work

Keep:

- `CP-001` through `CP-027` as completed history

Keep but reinterpret:

- `CP-028` becomes the transition task for moving the program from the smaller public-release endgame to the V2 launch program

### New Task Namespace

Add a `V2-` series after the existing CP block.

Recommended V2 tasks:

- `V2-001` Runtime surfaces
- `V2-002` Barcode and device input
- `V2-003` Advanced hardware
- `V2-004` Store operations depth
- `V2-005` Customer and commercial features
- `V2-006` Staff and branch controls
- `V2-007` Reporting and decision support
- `V2-008` Vertical extensions
- `V2-009` Hardening and scale
- `V2-010` V2 launch readiness and cutover

The exact subtask decomposition can happen within the ledger, but the top-level tracks should look like this.

## Canonical Doc Changes Required

To keep the repo coherent, the ledger rewrite must also update:

- `docs/PROJECT_CONTEXT.md`
- `docs/STORE_CANONICAL_BLUEPRINT.md`
- `docs/TASK_LEDGER.md`

Those docs must stop implying that the current endgame is the smaller release and instead describe:

- V2 as the actual launch target
- omnichannel as future work
- mobile/tablet/customer-display/hardware/commercial/vertical expansion as first-class planned scope

## Future Work After V2

The repo should explicitly call out a post-V2 future-work section for:

- e-commerce
- online ordering
- marketplace sync
- customer app
- delivery orchestration
- broader omnichannel commerce

This avoids losing those ideas while keeping V2 physically scoped.

## Exit Criteria For This Design

This design is complete when:

- the repo has one explicit V2 launch program definition
- the task ledger is rewritten around a V2 program instead of the smaller public-release endgame
- canonical docs describe V2 as the active target
- omnichannel scope is explicitly deferred instead of mixed into V2
