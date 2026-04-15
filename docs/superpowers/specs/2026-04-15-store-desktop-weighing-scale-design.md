# Store Desktop Weighing Scale Design

Date: 2026-04-15  
Status: Approved in terminal

## Goal

Land the next `V2-003` slice as a packaged `Store Desktop` weighing-scale integration that supports local scale assignment, live weight reads, and operator diagnostics without expanding billing authority or introducing weighed-item pricing logic yet.

## Why This Slice

- it advances `V2-003` with a real hardware bridge instead of another diagnostics-only placeholder
- it follows the same local assignment and recovery pattern already established for printers, scanners, and cash drawer
- it avoids payment-terminal complexity while still delivering real counter utility

## Scope

### Included

- packaged `Store Desktop` only
- local serial/COM-style scale candidate discovery
- preferred scale assignment in the local hardware profile
- manual `read current weight` action
- persisted diagnostics for latest successful or failed weight read
- operator-facing scale posture in the print/hardware desk and barcode lookup section

### Explicitly Deferred

- weighed-item pricing rules
- automatic sale quantity population
- mobile/tablet scale support
- payment terminal integration
- vendor-specific scale SDKs or advanced protocol matrices

## Architecture

Add a new native scale bridge in the Tauri runtime that mirrors the existing hardware pattern:

- native Rust command layer owns:
  - serial scale discovery
  - preferred scale reads
  - persistence of last-read diagnostics
- React consumes the scale state through the existing `storeRuntimeHardware` contract
- browser runtime remains fallback-only and exposes setup guidance rather than pretending scale support exists there

## Device Model

The first slice treats weighing scales as local serial candidates:

- discover likely local `COM` ports
- expose them as local scale candidates
- let the operator assign one preferred scale
- read the current weight from that assigned scale only when the cashier explicitly requests it

This keeps the slice realistic for low-setup Windows retail machines without over-claiming device support.

## State Model

Extend the desktop hardware contract with:

- `scales`
- `preferred_scale_id`
- `scale_capture_state`
  - `ready`
  - `unavailable`
  - `browser_fallback`
  - `attention_required`
- `last_weight_value`
- `last_weight_unit`
- `last_weight_status`
- `last_weight_message`
- `last_weight_read_at`
- `scale_status_message`
- `scale_setup_hint`

## Native Behavior

### Discovery

The native bridge should enumerate likely serial scale candidates from local Windows `COM` ports and expose them as:

- stable identifier
- operator-facing label
- transport type
- port name
- connected posture

### Weight Read

The native bridge should:

- require a preferred scale assignment
- open the assigned serial port with a conservative default configuration
- read a bounded payload from the scale
- parse the first stable numeric weight + unit pattern
- persist the last read status and timestamp

If reading fails:

- record a failed weight-read posture in diagnostics
- return a clear operator error

## UI Surfaces

### Print / Hardware Desk

Extend the existing `StorePrintQueueSection` with:

- preferred scale
- scale status
- setup hint
- last weight read
- `Use for weighing scale` action on discovered scales
- `Read current weight` action when a preferred scale exists

### Barcode Lookup

Extend the existing `StoreBarcodeLookupSection` with a compact scale card that shows:

- scale posture
- last stable weight
- manual read action

This keeps the scale workflow near the counter scan flow without creating a separate hardware screen.

## Error Handling

For the first slice:

- no preferred scale assigned -> explicit operator error
- preferred scale missing from discovered candidates -> `attention_required`
- serial read failure -> `attention_required`
- browser runtime -> `browser_fallback`

Errors should produce actionable setup guidance, not raw transport noise.

## Testing

### Rust

- default diagnostics include scale guidance
- profile round-trip persists preferred scale assignment
- successful manual weight read updates diagnostics
- missing assigned scale yields `attention_required`

### TypeScript

- hardware contract accepts scale fields
- native adapter bridges `read current weight`
- browser fallback exposes scale fallback posture

### React

- hardware desk renders scale assignment and read controls
- barcode lookup renders compact scale posture
- workspace exposes scale actions and state

## Success Criteria

- packaged Store Desktop can assign one preferred local scale
- operators can manually read current weight from the assigned scale
- latest scale posture is visible in the counter UI
- browser fallback remains honest
- no billing authority or weighed-pricing behavior changes are introduced in this slice
