# Packaged Runtime Hardware Integration Design

## Context

`CP-021` is the first public-release hardware slice for Store Desktop. The control plane already owns runtime print-job queueing, barcode scan lookup, and packaged-runtime shell identity. What is missing is the actual packaged-runtime hardware bridge:

- queued print jobs are still completed manually from the UI,
- barcode lookup still depends on a text field instead of real scanner input,
- packaged runtime shell posture does not describe printer or scanner readiness.

The repo is already effectively Windows-first for the packaged runtime. The Tauri shell depends on Windows-specific crypto features today, and the current desktop task does not require cross-platform device support. That lets this task stay bounded: build a Windows packaged-runtime hardware bridge now instead of inventing a generic cross-platform device framework.

## Chosen Approach

Use one packaged-runtime hardware bridge with three responsibilities:

1. native printer discovery and execution,
2. real barcode scanner capture for keyboard-wedge scanners,
3. local device diagnostics surfaced through the runtime shell and runtime workspace.

The control plane remains authoritative for print job payloads and barcode lookup results. The packaged runtime becomes authoritative only for local hardware execution and diagnostics. This keeps the release task grounded in the existing control-plane contract and avoids introducing a second operational authority boundary.

## Scope

Included in `CP-021`:

- Windows packaged-runtime printer discovery.
- Local printer profile persistence for receipt and barcode-label printing.
- Automatic print-job polling and native print execution for approved packaged runtimes.
- Real scanner capture for keyboard-wedge barcode scanners.
- Hardware diagnostics for printer readiness, last print result, scanner capture posture, and last scan activity.
- Runtime-shell and workspace UI updates for hardware readiness and failure posture.

Out of scope for this slice:

- Cross-platform printer support.
- Full USB or HID-native scanner enumeration.
- Cash drawer, weighing scale, or payment terminal integration.
- Zebra or vendor-specific label command languages.
- Control-plane operator dashboards for hardware telemetry beyond the existing runtime posture.

## Architecture

### 1. Native Hardware Bridge Boundary

Add a dedicated native hardware module in the Tauri shell. It owns:

- printer enumeration,
- saved hardware preferences,
- print rendering and dispatch,
- recent hardware diagnostics.

The React app interacts with it through explicit commands and typed shell status payloads. The bridge is read or write only for local device execution. It does not mint control-plane authority and it does not replace the existing print queue or barcode lookup routes.

### 2. Printer Discovery And Profiles

The packaged runtime discovers local Windows printers and exposes a normalized list with:

- system printer name,
- display label,
- default-printer posture,
- online or offline state when available.

The runtime persists a small local hardware profile:

- `receipt_printer_name`
- `label_printer_name`
- `updated_at`

This profile is local to the packaged runtime installation. It is not stored in the control plane. The UI should allow choosing discovered printers for the two supported document classes:

- thermal receipt or invoice output,
- barcode label output.

If no printer is assigned for a job type, the runtime reports an actionable local diagnostic instead of pretending the job is complete.

### 3. Native Print Execution Loop

When the packaged runtime is session-live and locally unlocked, it should automatically process queued print jobs for the selected runtime device.

The loop is:

1. poll queued print jobs from the control plane,
2. choose the correct local printer based on job type,
3. render the payload into printable text,
4. submit the job through the native printer bridge,
5. complete the control-plane job as `COMPLETED` on success,
6. complete the control-plane job as `FAILED` with a clear failure reason on terminal local errors.

This removes manual “mark first job completed” simulation from the packaged-runtime path.

Rendering stays intentionally narrow:

- sales invoice and credit-note jobs print line-based receipt text,
- barcode label jobs print line-based label text using the existing label payload values.

This is not a vendor-command abstraction yet. It is a real local print path that uses existing payloads and fails clearly if a branch later needs a vendor-specific mode.

### 4. Scanner Capture Service

For this slice, barcode scanner support targets keyboard-wedge scanners, which are the most common enterprise retail deployment mode.

The packaged runtime adds a scan-capture service in the desktop app that:

- listens for rapid key bursts ending with `Enter`,
- ignores ordinary typing cadence,
- normalizes the captured buffer with the existing barcode helpers,
- records the last scan timestamp in local diagnostics,
- forwards the resolved barcode into the existing branch scan lookup flow.

The barcode UI shifts from “type a barcode then click lookup” to “scan-ready with optional manual fallback”. Manual entry remains as a fallback, but real scanner input becomes the primary path.

### 5. Device Diagnostics Surface

The runtime shell and workspace expose local hardware diagnostics:

- hardware bridge state,
- discovered printer count,
- configured receipt and label printer,
- last print poll timestamp,
- last print success or failure summary,
- scanner capture state,
- last scanned barcode timestamp,
- last hardware error message when present.

Diagnostics are local runtime posture. They do not become a new control-plane source of truth.

### 6. UI Changes

Store Desktop gets three concrete UX changes:

- `Print queue` becomes hardware-backed:
  - printer assignments,
  - discovered printers,
  - last local print outcome,
  - no manual completion button for packaged runtime.
- `Barcode lookup` becomes scan-ready:
  - focused scan input posture,
  - optional auto-lookup after a wedge scan,
  - visible last scan source or timestamp.
- `Packaged runtime shell` gains hardware diagnostics:
  - bridge readiness,
  - printer and scanner posture,
  - failure state if hardware is unavailable.

Browser and dev shells keep their existing fallback behavior. The hardware bridge is packaged-runtime only.

## Error Handling

The hardware bridge must fail closed and visibly:

- no assigned printer for a job type:
  - leave the job queued until operator assigns a printer,
  - show a local diagnostic.
- printer dispatch failure:
  - mark the control-plane print job `FAILED` with a bounded reason,
  - preserve the diagnostic locally.
- no hardware bridge available:
  - packaged runtime shows `unavailable` diagnostics,
  - browser shell remains unaffected.
- scanner inactivity or malformed bursts:
  - ignore invalid input,
  - do not trigger barcode lookup,
  - keep manual lookup available.

The runtime should not claim success for work it did not actually send to a printer or receive from a scanner.

## Testing Strategy

Desktop and shared packages:

- printer diagnostics and printer-profile UI behavior,
- automatic print execution flow from queued job to completed or failed result,
- keyboard-wedge scan burst detection and normalization,
- runtime shell hardware diagnostics rendering.

Native shell:

- printer profile persistence,
- shell hardware status resolution,
- print dispatch path with stubbed native backends where direct OS verification is impractical,
- diagnostics updates after print attempts.

Backend regression:

- keep the existing runtime print queue and barcode lookup tests green,
- add targeted tests only if shared type changes affect request or response contracts.

## Rollout

This slice ships the packaged-runtime bridge without widening product scope:

- real printing instead of manual print simulation,
- real scanner capture instead of typed-only lookup,
- local diagnostics instead of invisible hardware failure.

If a branch later needs vendor-specific printer command languages or richer device telemetry, those can build on the same bridge without rewriting the current control-plane runtime ownership model.
