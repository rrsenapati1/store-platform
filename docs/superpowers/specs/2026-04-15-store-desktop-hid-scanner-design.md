# Store Desktop HID Scanner Inventory Design

## Context

`V2-002` is still open because Store Desktop only has:

- keyboard-wedge barcode capture in the browser/runtime layer
- basic packaged-runtime scanner diagnostics
- no real HID/USB scanner inventory, assignment, or presence posture

Mobile now has camera scanning, external-scanner intake, rugged diagnostics, and optional Zebra provisioning. Desktop is the weaker runtime surface for richer external-scanner support.

## Chosen Approach

Keep the existing wedge-capture path as the active barcode-input mechanism, but add a native packaged-runtime HID inventory and assignment layer.

This slice does **not** jump straight to raw HID capture. Instead it adds:

- native HID scanner discovery on Windows
- local preferred-scanner assignment
- connected/disconnected posture for the preferred scanner
- scan-activity publication back into the native hardware status

That gives operators real richer HID/USB support without widening into fragile raw-input routing too early.

## Scope

Included:

- Windows packaged-runtime HID scanner discovery
- scanner-candidate normalization in the native bridge
- local preferred-scanner assignment in the runtime hardware profile
- scanner presence diagnostics in the native hardware status
- wedge-hook publication of scan activity into the native hardware store
- scanner inventory and assignment UI in Store Desktop

Out of scope:

- raw-input capture by HID device identity
- vendor SDK integrations
- backend/control-plane changes
- Linux/macOS native scanner support

## Architecture

### 1. Native Scanner Backend

Add a dedicated native scanner backend beside the existing printer backend.

Responsibilities:

- enumerate HID scanner candidates
- normalize each candidate into a stable record
- expose best-effort transport posture:
  - `usb_hid`
  - `bluetooth_hid`
  - `keyboard_wedge`
  - `unknown`

The backend is Windows-first. On unsupported platforms, scanner discovery returns an unavailable posture rather than pretending native support exists.

### 2. Scanner Candidate Records

`StoreRuntimeHardwareStatus` grows a `scanners` list.

Each scanner record should include:

- `id`
- `label`
- `transport`
- `vendor_name`
- `product_name`
- `serial_number`
- `is_connected`

The `id` only needs to be stable enough for local preferred-scanner assignment on the same machine. It does not need to become a cross-device authority key.

### 3. Preferred Scanner Profile

The local runtime hardware profile grows:

- `preferred_scanner_id`

This remains local packaged-runtime state, just like local printer assignment. It is not sent to the control plane.

### 4. Diagnostics Model

The existing native hardware diagnostics remain the source for packaged runtime scanner posture.

Rules:

- no preferred scanner configured:
  - scanner capture stays `ready`
  - setup message explains that wedge scanning still works and a preferred scanner can be assigned for stronger presence checks
- preferred scanner configured and connected:
  - scanner capture stays `ready`
  - transport reflects the preferred scanner when detectable
- preferred scanner configured but missing:
  - scanner capture becomes `attention_required`
  - setup hint tells the operator to reconnect or reassign
- scanner enumeration failure:
  - scanner capture becomes `unavailable`
  - native diagnostics carry the failure message

### 5. Wedge Capture Integration

The desktop barcode hook continues to parse rapid keyboard bursts. That remains the actual input path for this slice.

When a scan is accepted:

- the hook updates its local React state
- the hook publishes a small scan-activity event to the native hardware bridge
- the native bridge updates:
  - `last_scan_at`
  - `last_scan_barcode_preview`

This keeps the native packaged-runtime diagnostics aligned with real scan activity instead of treating the HID inventory as separate from actual scanning.

### 6. UI Surfaces

Use existing surfaces only.

`StoreRuntimeShellSection`

- show preferred scanner
- show discovered scanner count
- show preferred-scanner presence posture through the existing diagnostics labels

`StoreBarcodeLookupSection`

- keep the compact diagnostics card
- add discovered local scanners
- add `Use as preferred scanner` actions
- add `Clear preferred scanner` when one is assigned

This keeps scanner setup near the actual scan workflow.

## Error Handling

- no HID scanners discovered:
  - do not block wedge scanning
  - explain that manual/wedge capture still works
- preferred scanner disconnected:
  - show `attention_required`
  - do not block barcode lookup
- native enumeration failure:
  - surface `unavailable`
  - keep the browser/dev fallback behavior unchanged
- scan-activity publication failure:
  - do not block barcode lookup
  - keep the runtime UI usable

## Testing Strategy

TypeScript:

- hardware contract validation
- native adapter handling of scanner lists/profile/scan-activity command
- wedge-hook merge of local session gating with native scanner posture
- barcode and shell UI rendering of preferred-scanner posture

Rust:

- scanner candidate normalization and profile assignment
- preferred-scanner connected/disconnected diagnostics
- scan-activity persistence into the hardware state

## Expected Outcome

After this slice, Store Desktop will still use wedge capture for input, but packaged runtimes will finally know:

- which scanner candidates are locally connected
- which one the operator expects to use
- whether that preferred scanner is actually present
- when the last scan happened

That is the right next step for `V2-002` before any deeper raw HID or vendor-specific desktop capture work.
