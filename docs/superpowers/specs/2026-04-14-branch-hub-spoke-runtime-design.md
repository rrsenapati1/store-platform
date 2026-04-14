# Branch Hub And Spoke Runtime Design (CP-017)

Date: 2026-04-14  
Owner: Codex  
Status: Ready for user review

## Goal

Land the first real branch hub and spoke runtime contract for Store so branch-local runtime traffic no longer assumes every device is a direct human-operated desktop shell.

This design must:

- preserve control-plane Postgres as the only backend authority
- keep `CP-017` separate from `CP-018` offline business continuity
- support future spoke devices, including mobile apps
- reuse the strong parts of RMS spoke bootstrap without importing RMS restaurant-specific scope
- make local hub relay posture explicit, bounded, and auditable

## Current Context

Store already has:

- control-plane-backed branch device registration
- approved packaged desktop claim-and-bind
- owner-issued desktop activation for packaged desktop staff access
- branch hub machine identity bootstrap for designated hub devices
- cloud sync monitoring and hub-spoke observation visibility
- a bounded local loopback hub service with:
  - `GET /healthz`
  - `GET /v1/spoke-manifest`

Store does not yet have:

- explicit spoke device classes
- QR or approval-code spoke pairing
- local spoke registration against the hub
- hub-issued short-lived spoke runtime sessions
- spoke-authenticated relay routes through the hub

## RMS Alignment

RMS already has a broader pairing and runtime matrix.

Relevant RMS posture:

- pairing bootstrap supports `approval_code` and `qr`
- the pairing contract carries `issued_for` and expected device type
- RMS normalizes multiple runtime profiles such as:
  - `desktop_pos`
  - `mobile_pos`
  - `delivery_rider`
  - `kds_spoke`
  - `customer_display`
  - `kiosk`

Store should reuse the RMS architectural idea:

- QR is a transport for spoke bootstrap
- pairing is one-time and short-lived
- the hub is the branch-local trust anchor for spokes

Store should not inherit RMS restaurant-specific device scope by default.

## Product Decision

Store will support spoke bootstrap in both of these modes:

- `qr`
- `approval_code`

QR is the preferred future transport for mobile and tablet spokes.

Manual code entry remains required for:

- camera-less desktops
- recovery workflows
- operator-assisted fallback

The trust model is identical in both modes. Only the transport differs.

## Non-Goals

This slice will not:

- make the hub a generic local proxy for arbitrary control-plane routes
- promote local hub state to branch authority
- finalize checkout, billing, inventory, or returns locally during cloud loss
- replace `CP-018` bounded offline business continuity
- add restaurant-specific device classes such as KDS or delivery rider

## Store Device Classes

Store should stop relying on `session_surface` alone to describe runtime role.

### Broad Surface

`session_surface` stays as the broad app surface:

- `store_desktop`
- future `store_mobile`
- future `customer_display`

### Runtime Role

Add an explicit device role field such as `runtime_profile` or `device_class`.

Recommended Store runtime roles:

- `branch_hub`
  - one approved packaged Store Desktop per branch
  - local trust anchor for spoke devices
- `desktop_spoke`
  - secondary cashier or counter desktop behind the hub
- `mobile_store_spoke`
  - future handheld mobile app for cashier assist, barcode scan, stock lookup, receiving, expiry, and returns support
- `inventory_tablet_spoke`
  - future tablet workflow using the same pairing model with an inventory-focused UI
- `customer_display`
  - optional future paired display surface

Store will not define these in this phase:

- `kds_spoke`
- `delivery_rider`
- `kiosk`

If self-service retail later becomes a real product requirement, `kiosk` can be added intentionally instead of being inherited accidentally from RMS.

### Compatibility Rule

During migration, `is_branch_hub` may remain as a compatibility bridge, but the long-term classifier should be the explicit runtime role.

## Pairing And Bootstrap Contract

### Activation Shape

Spoke pairing is always driven by a short-lived, single-use activation.

Activation must be bound to:

- tenant
- branch
- expected runtime role
- expiry
- optional issuing hub identity when a hub-assisted pairing flow is used

In `CP-017`, the control plane is the only authority that can mint or approve the activation contract. Owner web may initiate that issuance directly, and a future hub-assisted pairing flow may request an activation from the control plane, but the hub must not mint standalone trust offline.

### QR Payload

The QR payload should contain only bootstrap-safe metadata:

- `v`
- `pairing_mode`
- `activation_code`
- `runtime_profile`
- `hub_manifest_url`
- `tenant_label`
- `branch_label`
- `hub_device_code`
- `expires_at`

The QR payload must not contain:

- cloud bearer tokens
- hub sync secret
- desktop local auth token
- staff PIN material
- reusable machine credentials

### Bootstrap Flow

1. The spoke scans QR or receives a manual activation code.
2. The spoke reads the local hub manifest from the hub's loopback-backed service, exposed to the local branch network.
3. The spoke posts its device bootstrap payload to the hub.
4. The hub validates the activation, expected runtime role, and local branch scope.
5. The hub records spoke registration and returns a short-lived spoke runtime session.
6. The spoke uses that session only against the hub relay boundary.

## Local Hub Service Contract

The hub service should stay small and explicit.

### Public Bootstrap Endpoints

#### `GET /healthz`

Returns:

- service status
- protocol version
- hub device code
- tenant id
- branch id

This is for simple local health visibility only.

#### `GET /v1/spoke-manifest`

Returns the branch-local bootstrap manifest:

- `hub_device_id`
- `hub_device_code`
- `tenant_id`
- `branch_id`
- `supported_runtime_profiles`
- `pairing_modes`
- `register_url`
- `relay_base_url`
- `manifest_version`

This endpoint is intentionally public within the local branch network. It does not issue trust by itself.

### Spoke Session Endpoints

#### `POST /v1/spokes/register`

Redeems a one-time activation against the hub.

Input:

- activation code
- installation id
- runtime kind
- runtime profile
- hostname or device label
- app version

Output:

- `spoke_device_id`
- `spoke_runtime_token`
- `expires_at`
- `relay_base_url`
- `heartbeat_interval_seconds`

#### `POST /v1/spokes/heartbeat`

Keeps the spoke visible to the hub and refreshes local connectivity posture.

Input:

- spoke runtime token
- local status summary
- last seen or activity timestamp

Output:

- accepted heartbeat status
- optional new expiry hint

#### `POST /v1/spokes/disconnect`

Allows explicit spoke detach or sign-out.

This endpoint clears local spoke session posture without changing cloud authority.

## First Relay Surface

The hub relay must be allowlisted, not generic.

### Relay Endpoints

#### `GET /v1/relay/runtime/status`

Spoke-authenticated read of:

- branch hub service status
- basic branch runtime posture
- local relay health

#### `POST /v1/relay/runtime/heartbeat`

Allows the spoke to relay branch device heartbeat through the hub.

The hub forwards this to the control plane with explicit source context.

#### `POST /v1/relay/runtime/print-jobs`

First concrete relayed write path.

This lets a spoke submit a print request through the hub without making the spoke a cloud client.

#### `GET /v1/relay/runtime/print-jobs`

Lets the spoke read relayed print-job posture back from the hub.

#### `GET /v1/relay/runtime/sync-status`

Returns read-only local and cloud sync posture for spoke visibility.

### Relay Rules

Every relayed request must be stamped with:

- `hub_device_id`
- `spoke_device_id`
- tenant id
- branch id
- operation name

The hub must reject:

- unknown relay paths
- unknown runtime profiles
- expired spoke tokens
- branch mismatches
- spoke requests that attempt operations outside the allowlist

## Authentication And Security Rules

### Spoke Session Rules

- QR or approval code only bootstraps registration
- the hub issues a short-lived spoke runtime token after successful registration
- that token is local-to-hub only
- that token is never a cloud bearer token
- the hub may invalidate local spoke sessions on restart

Restart invalidation is acceptable for `CP-017`.

### Branch Scope Rules

The hub must ensure:

- the hub itself is the approved active branch hub
- the activation code belongs to the same tenant and branch
- the activation code is single-use and unexpired
- the spoke runtime profile matches the activation contract

### Audit Rules

The system must audit:

- activation issuance
- spoke registration
- relay request acceptance
- relay request rejection
- disconnect
- invalid or expired activation attempts

### Authority Rules

This slice does not promote local authority.

Forbidden in `CP-017`:

- local checkout completion while cloud is unavailable
- local inventory authority
- local invoice finalization without cloud confirmation
- generic forwarding proxy

Those belong to `CP-018`.

## Monitoring And Operator Visibility

Store desktop runtime monitoring should expose:

- hub health
- hub device code
- observed spokes
- connected spokes
- last local spoke sync timestamp
- spoke registration posture
- local relay availability

Owner web should later expose the same posture at the branch level, but store-desktop is the first runtime-facing monitoring surface in this slice.

## Data Model Changes

### Control Plane

Add explicit spoke-facing device metadata:

- runtime profile or device class
- pairing mode support
- spoke registration records or equivalent branch-local observation contract

The existing `device_registrations` surface should remain the branch-controlled device directory, but it needs enough metadata to distinguish:

- branch hub
- desktop spoke
- mobile store spoke
- inventory tablet spoke
- customer display

### Hub Local State

The hub needs a bounded local store for:

- registered spokes
- short-lived spoke runtime tokens
- relay session expiry
- last heartbeat per spoke

This local store does not become backend authority. It exists only to support local connectivity and relay posture.

## Implementation Order

1. Extend Store device modeling for explicit spoke runtime roles and pairing mode support.
2. Add control-plane activation support for spoke pairing.
3. Add QR payload generation and manual-code parity.
4. Extend the local hub service with:
   - manifest
   - register
   - heartbeat
   - disconnect
5. Add hub-local spoke session persistence and validation.
6. Add the first allowlisted relay endpoints.
7. Feed spoke registration and relay posture into runtime sync monitoring.
8. Update store-desktop runtime UI for hub and spoke visibility where needed.

## Verification

### Backend

- activation issuance for spoke runtime roles
- invalid runtime profile rejection
- expired or reused activation rejection
- branch mismatch rejection
- allowlisted relay acceptance
- non-allowlisted relay rejection

### Desktop Runtime

- manifest visibility
- spoke registration success path
- QR/manual bootstrap parity at the contract level
- local relay token validation
- restart invalidation posture
- monitoring visibility for connected and disconnected spokes

### Native Hub Service

- `GET /healthz`
- `GET /v1/spoke-manifest`
- `POST /v1/spokes/register`
- `POST /v1/spokes/heartbeat`
- `POST /v1/spokes/disconnect`
- relay route allowlist enforcement

## Exit Criteria

`CP-017` is complete when:

- one approved hub per branch exposes a real local runtime service
- spokes can bootstrap through QR or manual code
- spokes can register and obtain a short-lived local spoke session
- spokes can use the first bounded relay routes
- spoke discovery and relay posture are visible in runtime monitoring
- branch-local runtime traffic no longer assumes direct human desktop use only

## Deferred Work

The following remain intentionally deferred:

- bounded offline checkout authority
- authoritative cloud reconciliation after local business continuity
- broad local proxying for arbitrary runtime routes
- self-service retail kiosk behavior
- restaurant-specific device classes from RMS

Those belong in later tasks, especially `CP-018`.
