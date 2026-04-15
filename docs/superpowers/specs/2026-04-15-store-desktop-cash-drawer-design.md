# Store Desktop Cash Drawer Design

## Context

`V2-003` starts the advanced-hardware track. The first slice should be the packaged Store Desktop cash drawer because it is the lowest-risk hardware bridge:

- it stays inside the existing Windows desktop runtime
- it reuses the current local printer discovery and assignment model
- it avoids payment-terminal and weighing-scale vendor complexity in the first step

The existing runtime already supports:

- receipt/label printer discovery and assignment
- scanner discovery, diagnostics, and preferred assignment
- a packaged-runtime hardware status bridge surfaced in the cashier UI

What is missing is a bounded way to:

- assign a drawer-capable printer for cash drawer pulses
- trigger a drawer open from the cashier runtime
- record drawer diagnostics and failure posture

## Recommended Approach

Implement cash drawer support as a `receipt-printer-driven ESC/POS pulse` inside the packaged Windows runtime.

Why this is the right first slice:

- most low-cost retail drawers are connected to the receipt printer, not directly to the PC
- it fits the current discovered-printer model
- it creates the assignment/diagnostics pattern that weighing scales and payment terminals can follow later

This slice does **not** try to:

- enumerate standalone USB cash drawers
- auto-open the drawer after every sale
- add control-plane server changes
- add mobile cash drawer support

## Architecture

### Native runtime

Add a new packaged-runtime cash drawer module next to the existing printer/scanner modules:

- `runtime_cash_drawer.rs`

Responsibilities:

- send a raw ESC/POS pulse to the assigned local printer on Windows
- expose a small backend trait so the hardware state layer can be tested without touching the real spooler

The raw pulse should use the common ESC/POS drawer kick command:

- `ESC p m t1 t2`

The first slice only needs one safe default pulse profile.

### Hardware state

Extend the existing persisted runtime hardware state with cash drawer fields.

Profile:

- `cash_drawer_printer_name`

Diagnostics:

- `last_cash_drawer_status`
- `last_cash_drawer_message`
- `last_cash_drawer_opened_at`
- `cash_drawer_status_message`
- `cash_drawer_setup_hint`

The diagnostics should be derived conservatively:

- assigned + printer discovered = ready posture
- assigned + printer missing/offline = attention-required message
- not assigned = setup guidance
- browser shell = packaged-runtime required guidance

### Frontend

Expose the new hardware fields through the desktop runtime adapter and workspace state.

Primary UI surface:

- `StorePrintQueueSection.tsx`

That section should gain:

- cash drawer assignment display
- drawer diagnostics
- a manual `Open assigned cash drawer` action
- `Use for cash drawer` on discovered printers

Secondary read-only surface:

- `StoreRuntimeShellSection.tsx`

That section should show the assigned drawer printer and latest drawer activity.

## Error Handling

The first slice should be explicit and operator-friendly:

- opening the drawer without assignment fails clearly
- spooler/raw-print failure becomes a visible drawer error
- drawer open failures do not break invoice printing or runtime session bootstrap

## Testing

Required coverage:

- runtime hardware contract and adapter tests for the new cash drawer fields and command
- Rust tests for:
  - default hardware status shape
  - profile round-trip with drawer assignment
  - drawer-open requiring assignment
  - successful drawer-open diagnostics update
- React UI test for print queue drawer controls and diagnostics

## Exit Criteria

This slice is done when:

- packaged desktop can assign a printer for cash drawer duty
- cashier can manually open the assigned drawer
- success/failure diagnostics are visible in the runtime UI
- browser fallback remains safe
- full desktop test/typecheck/build and Tauri unit tests pass
