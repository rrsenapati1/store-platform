# Branch Hub And Spoke Runtime (CP-017) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the first real branch-hub local runtime service for Store so an approved hub can issue spoke bootstrap sessions, register spoke devices, expose narrow local relay routes, and report spoke posture back through the control plane.

**Architecture:** Implement this slice as hub-assisted pairing. The control plane remains the only authority that mints spoke activations, but the approved hub requests those activations with its sync identity and serves the local bootstrap and relay boundary over the packaged runtime’s local HTTP service. On the desktop side, split the current oversized workspace hook into focused modules for control-plane origin resolution, sync monitoring, and hub-assisted spoke pairing before adding new behavior.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React 19, Vitest, Tauri 2, Rust std HTTP listener, `reqwest` (blocking) for native outbound control-plane calls.

---

## File Structure

### Existing files to modify

- `services/control-plane-api/store_control_plane/models/workforce.py`
  - add explicit runtime-role metadata and spoke pairing authority records
- `services/control-plane-api/store_control_plane/models/sync_runtime.py`
  - extend spoke observation records so monitoring distinguishes discovery, registration, relay, and disconnect posture
- `services/control-plane-api/store_control_plane/repositories/workforce.py`
  - persist runtime profiles and spoke pairing activations
- `services/control-plane-api/store_control_plane/repositories/sync_runtime.py`
  - persist richer spoke posture and relay visibility
- `services/control-plane-api/store_control_plane/routes/sync_runtime.py`
  - add sync-authenticated spoke activation issuance and relay target routes
- `services/control-plane-api/store_control_plane/services/sync_runtime.py`
  - keep cloud sync service focused on sync-state authority and thin relay target helpers
- `services/control-plane-api/store_control_plane/schemas/sync_runtime.py`
  - add request and response contracts for spoke pairing and relay posture
- `services/control-plane-api/store_control_plane/schemas/workforce.py`
  - add runtime-profile fields to device registration payloads
- `packages/types/src/index.ts`
  - mirror runtime-profile, spoke activation, and local relay types for web and desktop
- `apps/store-desktop/src/runtime-shell/storeRuntimeShellContract.ts`
  - carry explicit control-plane origin and richer hub manifest metadata
- `apps/store-desktop/src/runtime-shell/nativeStoreRuntimeShell.ts`
  - normalize new native shell fields
- `apps/store-desktop/src/control-plane/client.ts`
  - stop assuming relative `/v1/...` is enough for packaged runtime; use a resolved control-plane base URL
- `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
  - keep orchestration only and render new extracted spoke pairing UI
- `apps/store-desktop/src/control-plane/StoreSyncRuntimeSection.tsx`
  - show spoke activation, registration, and relay posture
- `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
  - **classification:** `mixed-responsibility`, 1198 lines, `>800` threshold from `@large-file-governance`
  - extract pairing and sync-monitoring logic before adding new spoke behavior
- `apps/store-desktop/src-tauri/Cargo.toml`
  - add native HTTP client dependency for relay calls
- `apps/store-desktop/src-tauri/src/runtime_shell.rs`
  - expose packaged control-plane origin and richer hub service status
- `apps/store-desktop/src-tauri/src/runtime_hub_service.rs`
  - expand from read-only health/manifest to registration, heartbeat, disconnect, and relay endpoints
- `apps/store-desktop/src-tauri/src/lib.rs`
  - register any new native modules and commands
- `docs/TASK_LEDGER.md`
  - mark `CP-017` done after verification passes

### New files to create

- `services/control-plane-api/alembic/versions/20260414_0018_spoke_runtime_pairing.py`
  - schema migration for runtime profiles and spoke activations
- `services/control-plane-api/store_control_plane/services/spoke_runtime.py`
  - dedicated control-plane authority for sync-authenticated spoke activation issuance and allowlisted relay translation
- `services/control-plane-api/tests/test_spoke_runtime_flow.py`
  - backend regression suite for activation issuance, registration authority, relay allowlist, and monitoring posture
- `apps/store-desktop/src/control-plane/controlPlaneOrigin.ts`
  - resolve browser vs packaged control-plane base URL
- `apps/store-desktop/src/control-plane/useStoreRuntimeSyncMonitoring.ts`
  - extracted runtime sync-monitoring loader and state
- `apps/store-desktop/src/control-plane/useStoreRuntimeSpokePairing.ts`
  - extracted hub-assisted spoke activation, QR payload, and local registration orchestration
- `apps/store-desktop/src/control-plane/storeRuntimeHubLocalClient.ts`
  - typed local HTTP client for `/healthz`, `/v1/spoke-manifest`, `/v1/spokes/*`, and `/v1/relay/*`
- `apps/store-desktop/src/control-plane/storeRuntimeHubLocalClient.test.ts`
  - contract tests for the local hub client
- `apps/store-desktop/src-tauri/src/runtime_control_plane_origin.rs`
  - packaged-runtime origin resolution for native shell and hub service
- `apps/store-desktop/src-tauri/src/runtime_spoke_registry.rs`
  - in-memory local registry for issued activations, short-lived spoke runtime tokens, and per-spoke heartbeat state

### Notes

- Do **not** add spoke pairing logic directly into `useStoreRuntimeWorkspace.ts`; extract first.
- Do **not** add a generic proxy route. Every relay operation stays explicit and allowlisted.
- Owner-web direct spoke issuance is deferred in this implementation. `CP-017` ships hub-assisted pairing first because Store has no dedicated spoke-admin web surface yet.

### Task 1: Add Packaged Control-Plane Origin Resolution

**Files:**
- Create: `apps/store-desktop/src/control-plane/controlPlaneOrigin.ts`
- Create: `apps/store-desktop/src-tauri/src/runtime_control_plane_origin.rs`
- Modify: `apps/store-desktop/src/runtime-shell/storeRuntimeShellContract.ts`
- Modify: `apps/store-desktop/src/runtime-shell/nativeStoreRuntimeShell.ts`
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src-tauri/src/runtime_shell.rs`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`
- Test: `apps/store-desktop/src/runtime-shell/storeRuntimeShellAdapter.test.ts`
- Test: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.shell.test.tsx`

- [ ] **Step 1: Write the failing desktop-shell tests**

```ts
expect(shellStatus.control_plane_base_url).toBe('https://control.acme.local');
expect(resolveControlPlaneUrl('/v1/auth/me', shellStatus)).toBe('https://control.acme.local/v1/auth/me');
```

- [ ] **Step 2: Run the targeted desktop tests and confirm they fail**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.shell.test.tsx storeRuntimeShellAdapter.test.ts`
Expected: FAIL because `control_plane_base_url` does not exist in the shell contract.

- [ ] **Step 3: Extend the shell contract and browser fallback helper**

```ts
export interface StoreRuntimeShellStatus {
  // existing fields...
  control_plane_base_url: string | null;
}

export function resolveControlPlaneUrl(path: string, shell: StoreRuntimeShellStatus | null) {
  const base = shell?.control_plane_base_url ?? window.location.origin;
  return new URL(path, `${base}/`).toString();
}
```

- [ ] **Step 4: Expose packaged origin from the native shell**

```rust
pub struct StoreRuntimeShellStatus {
    // existing fields...
    pub control_plane_base_url: Option<String>,
}
```

- [ ] **Step 5: Update the control-plane client to use resolved absolute URLs**

```ts
const endpoint = resolveControlPlaneUrl(path, shellStatus);
return fetch(endpoint, { ...init, headers });
```

- [ ] **Step 6: Re-run the targeted desktop tests and confirm they pass**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.shell.test.tsx storeRuntimeShellAdapter.test.ts`
Expected: PASS

- [ ] **Step 7: Commit the origin-contract slice**

```bash
git add apps/store-desktop/src/control-plane/controlPlaneOrigin.ts apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/runtime-shell/storeRuntimeShellContract.ts apps/store-desktop/src/runtime-shell/nativeStoreRuntimeShell.ts apps/store-desktop/src-tauri/src/runtime_control_plane_origin.rs apps/store-desktop/src-tauri/src/runtime_shell.rs apps/store-desktop/src-tauri/src/lib.rs apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.shell.test.tsx apps/store-desktop/src/runtime-shell/storeRuntimeShellAdapter.test.ts
git commit -m "feat: add packaged control-plane origin contract"
```

### Task 2: Add Runtime Profiles And Spoke Pairing Authority To The Control Plane

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260414_0018_spoke_runtime_pairing.py`
- Modify: `services/control-plane-api/store_control_plane/models/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/models/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/workforce.py`
- Modify: `packages/types/src/index.ts`
- Test: `services/control-plane-api/tests/test_spoke_runtime_flow.py`

- [ ] **Step 1: Write the failing backend model and contract tests**

```python
assert device_payload["runtime_profile"] == "branch_hub"
assert activation_payload["pairing_mode"] == "approval_code"
assert activation_payload["runtime_profile"] == "desktop_spoke"
```

- [ ] **Step 2: Run the new backend test file and confirm it fails**

Run: `python -m pytest services/control-plane-api/tests/test_spoke_runtime_flow.py -q`
Expected: FAIL because runtime-profile and spoke-activation tables do not exist.

- [ ] **Step 3: Add migration and SQLAlchemy fields**

```python
class DeviceRegistration(Base, TimestampMixin):
    runtime_profile: Mapped[str] = mapped_column(String(64), default="desktop_spoke")

class SpokeRuntimeActivation(Base, TimestampMixin):
    __tablename__ = "spoke_runtime_activations"
```

- [ ] **Step 4: Extend repositories and schemas without changing existing device semantics**

```python
class DeviceRegistrationResponse(BaseModel):
    runtime_profile: str
```

- [ ] **Step 5: Mirror the new shared types in `@store/types`**

```ts
export interface ControlPlaneSpokeRuntimeActivation {
  activation_code: string;
  pairing_mode: 'approval_code' | 'qr';
  runtime_profile: string;
  expires_at: string;
}
```

- [ ] **Step 6: Re-run the backend test file and confirm the schema layer passes**

Run: `python -m pytest services/control-plane-api/tests/test_spoke_runtime_flow.py -q`
Expected: still FAIL, but only at missing service/route logic rather than missing columns or models.

- [ ] **Step 7: Commit the data-model slice**

```bash
git add services/control-plane-api/alembic/versions/20260414_0018_spoke_runtime_pairing.py services/control-plane-api/store_control_plane/models/workforce.py services/control-plane-api/store_control_plane/models/sync_runtime.py services/control-plane-api/store_control_plane/repositories/workforce.py services/control-plane-api/store_control_plane/repositories/sync_runtime.py services/control-plane-api/store_control_plane/schemas/workforce.py packages/types/src/index.ts services/control-plane-api/tests/test_spoke_runtime_flow.py
git commit -m "feat: add spoke runtime pairing models"
```

### Task 3: Implement Sync-Authenticated Spoke Activation And Relay Authority

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/spoke_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/routes/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/services/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
- Test: `services/control-plane-api/tests/test_spoke_runtime_flow.py`

- [ ] **Step 1: Extend the failing backend test to cover activation issuance, relay allowlist, and rejection paths**

```python
issue = client.post("/v1/sync/spokes/activate", headers=device_headers, json={"runtime_profile": "desktop_spoke", "pairing_mode": "qr"})
assert issue.status_code == 200

forbidden = client.post("/v1/sync/spokes/activate", headers=non_hub_headers, json={"runtime_profile": "desktop_spoke", "pairing_mode": "qr"})
assert forbidden.status_code == 403
```

- [ ] **Step 2: Run the backend test and confirm the new route/service assertions fail**

Run: `python -m pytest services/control-plane-api/tests/test_spoke_runtime_flow.py -q`
Expected: FAIL with `404 Not Found` or missing service methods for the new spoke runtime endpoints.

- [ ] **Step 3: Add a focused `SpokeRuntimeService` for activation issuance and relay translation**

```python
class SpokeRuntimeService:
    async def issue_activation(...): ...
    async def record_registration(...): ...
    async def authorize_relay_operation(...): ...
```

- [ ] **Step 4: Add sync-authenticated routes instead of owner-session routes**

```python
@router.post("/v1/sync/spokes/activate")
async def issue_spoke_activation(...):
    ...
```

- [ ] **Step 5: Keep relay support allowlisted**

```python
ALLOWED_RELAY_OPERATIONS = {
    "runtime.status",
    "runtime.heartbeat",
    "runtime.print_jobs.submit",
    "runtime.print_jobs.list",
    "runtime.sync_status",
}
```

- [ ] **Step 6: Update sync monitoring serialization so observations distinguish `DISCOVERED`, `REGISTERED`, `CONNECTED`, and `DISCONNECTED`**

```python
record.connection_state = "REGISTERED"
record.runtime_profile = activation.runtime_profile
```

- [ ] **Step 7: Re-run the backend spoke-runtime tests and confirm they pass**

Run: `python -m pytest services/control-plane-api/tests/test_spoke_runtime_flow.py -q`
Expected: PASS

- [ ] **Step 8: Commit the control-plane authority slice**

```bash
git add services/control-plane-api/store_control_plane/services/spoke_runtime.py services/control-plane-api/store_control_plane/routes/sync_runtime.py services/control-plane-api/store_control_plane/services/sync_runtime.py services/control-plane-api/store_control_plane/repositories/workforce.py services/control-plane-api/store_control_plane/repositories/sync_runtime.py services/control-plane-api/store_control_plane/schemas/sync_runtime.py services/control-plane-api/store_control_plane/schemas/__init__.py services/control-plane-api/store_control_plane/services/__init__.py services/control-plane-api/tests/test_spoke_runtime_flow.py
git commit -m "feat: add spoke runtime control-plane authority"
```

### Task 4: Expand The Native Hub Service Into A Real Local Runtime Boundary

**Files:**
- Create: `apps/store-desktop/src-tauri/src/runtime_spoke_registry.rs`
- Modify: `apps/store-desktop/src-tauri/Cargo.toml`
- Modify: `apps/store-desktop/src-tauri/src/runtime_hub_service.rs`
- Modify: `apps/store-desktop/src-tauri/src/runtime_shell.rs`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`
- Test: `apps/store-desktop/src-tauri/src/runtime_hub_service.rs`

- [ ] **Step 1: Write failing Rust tests for register, heartbeat, disconnect, and allowlisted relay**

```rust
assert!(register_response.contains("\"spoke_runtime_token\""));
assert!(heartbeat_response.contains("\"connected_spoke_count\":1"));
assert!(relay_rejection.contains("\"error\":\"unsupported_relay_operation\""));
```

- [ ] **Step 2: Run the focused cargo tests and confirm they fail**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib runtime_hub_service`
Expected: FAIL because only `/healthz` and `/v1/spoke-manifest` exist.

- [ ] **Step 3: Add a bounded in-memory spoke registry**

```rust
pub struct RegisteredSpokeSession {
    pub spoke_device_id: String,
    pub runtime_profile: String,
    pub expires_at: String,
}
```

- [ ] **Step 4: Teach the hub service to serve register, heartbeat, and disconnect**

```rust
match path {
    "/v1/spokes/register" => { ... }
    "/v1/spokes/heartbeat" => { ... }
    "/v1/spokes/disconnect" => { ... }
}
```

- [ ] **Step 5: Add explicit relay handlers backed by control-plane calls**

```rust
match path {
    "/v1/relay/runtime/status" => relay_runtime_status(...),
    "/v1/relay/runtime/print-jobs" => relay_print_jobs(...),
    _ => unsupported_relay_operation(...),
}
```

- [ ] **Step 6: Re-run the focused cargo tests and confirm they pass**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib runtime_hub_service`
Expected: PASS

- [ ] **Step 7: Commit the native hub-service slice**

```bash
git add apps/store-desktop/src-tauri/Cargo.toml apps/store-desktop/src-tauri/src/runtime_spoke_registry.rs apps/store-desktop/src-tauri/src/runtime_hub_service.rs apps/store-desktop/src-tauri/src/runtime_shell.rs apps/store-desktop/src-tauri/src/lib.rs
git commit -m "feat: add local hub spoke registration and relay"
```

### Task 5: Extract Desktop Pairing And Sync Monitoring From The Oversized Workspace Hook

**Files:**
- Create: `apps/store-desktop/src/control-plane/useStoreRuntimeSyncMonitoring.ts`
- Create: `apps/store-desktop/src/control-plane/useStoreRuntimeSpokePairing.ts`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeHubLocalClient.ts`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeHubLocalClient.test.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreSyncRuntimeSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.sync-runtime.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.shell.test.tsx`

- [ ] **Step 1: Write the failing desktop tests for hub-assisted spoke activation and richer monitoring**

```ts
expect(await screen.findByText('Prepare spoke activation')).toBeInTheDocument();
expect(screen.getByText(/desktop_spoke :: REGISTERED :: COUNTER-02/)).toBeInTheDocument();
expect(screen.getByText(/runtime.print_jobs.submit :: allowed/)).toBeInTheDocument();
```

- [ ] **Step 2: Run the targeted desktop tests and confirm they fail**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.sync-runtime.test.tsx StoreRuntimeWorkspace.shell.test.tsx storeRuntimeHubLocalClient.test.ts`
Expected: FAIL because no spoke-pairing UI or local hub client exists.

- [ ] **Step 3: Extract local hub HTTP access into a dedicated client**

```ts
export async function registerSpokeAtLocalHub(...) { ... }
export async function issueSpokeActivation(...) { ... }
```

- [ ] **Step 4: Extract sync monitoring into its own hook**

```ts
export function useStoreRuntimeSyncMonitoring(args: {...}) {
  const [syncStatus, setSyncStatus] = useState<ControlPlaneSyncStatus | null>(null);
}
```

- [ ] **Step 5: Extract hub-assisted spoke pairing from `useStoreRuntimeWorkspace.ts`**

```ts
export function useStoreRuntimeSpokePairing(args: {...}) {
  const [spokeActivation, setSpokeActivation] = useState<ControlPlaneSpokeRuntimeActivation | null>(null);
}
```

- [ ] **Step 6: Rewire the main workspace hook so it only composes extracted modules**

```ts
const syncMonitoring = useStoreRuntimeSyncMonitoring(...);
const spokePairing = useStoreRuntimeSpokePairing(...);
```

- [ ] **Step 7: Re-run the targeted desktop tests and confirm they pass**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.sync-runtime.test.tsx StoreRuntimeWorkspace.shell.test.tsx storeRuntimeHubLocalClient.test.ts`
Expected: PASS

- [ ] **Step 8: Commit the desktop extraction and UI slice**

```bash
git add apps/store-desktop/src/control-plane/useStoreRuntimeSyncMonitoring.ts apps/store-desktop/src/control-plane/useStoreRuntimeSpokePairing.ts apps/store-desktop/src/control-plane/storeRuntimeHubLocalClient.ts apps/store-desktop/src/control-plane/storeRuntimeHubLocalClient.test.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx apps/store-desktop/src/control-plane/StoreSyncRuntimeSection.tsx apps/store-desktop/src/control-plane/StoreRuntimeShellSection.tsx apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.sync-runtime.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.shell.test.tsx
git commit -m "feat: add desktop hub-assisted spoke pairing"
```

### Task 6: Run Full Verification And Close `CP-017`

**Files:**
- Modify: `docs/TASK_LEDGER.md`
- Test: `services/control-plane-api/tests/test_sync_runtime_flow.py`
- Test: `services/control-plane-api/tests/test_spoke_runtime_flow.py`
- Test: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.sync-runtime.test.tsx`
- Test: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.shell.test.tsx`
- Test: `apps/store-desktop/src/control-plane/storeRuntimeHubLocalClient.test.ts`

- [ ] **Step 1: Mark the ledger done only after all verification passes**

```md
| CP-017 | P0 | Done | Public release | Branch hub runtime | ... |
```

- [ ] **Step 2: Run the backend verification set**

Run: `python -m pytest services/control-plane-api/tests/test_sync_runtime_flow.py services/control-plane-api/tests/test_spoke_runtime_flow.py -q`
Expected: PASS

- [ ] **Step 3: Run the desktop unit and integration verification set**

Run: `npm run test --workspace @store/store-desktop`
Expected: PASS

- [ ] **Step 4: Run the desktop typecheck and build**

Run: `npm run typecheck --workspace @store/store-desktop`
Expected: PASS

Run: `npm run build --workspace @store/store-desktop`
Expected: PASS

- [ ] **Step 5: Run the native verification set**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
Expected: PASS

- [ ] **Step 6: Commit the closure and verification sweep**

```bash
git add docs/TASK_LEDGER.md
git commit -m "chore: close CP-017 branch hub runtime"
```

## Manual Review Checklist

- `useStoreRuntimeWorkspace.ts` shrank materially and no new spoke logic was added inline
- `session_surface` remains broad while `runtime_profile` carries role-specific behavior
- no generic relay proxy exists
- local spoke token is never reused as a cloud bearer token
- packaged runtime no longer depends on relative `/v1/...` semantics for native relay behavior
- hub restart invalidates local spoke sessions cleanly
- sync monitoring distinguishes discovery, registration, connection, and disconnect posture

## Verification Summary

- Backend: `python -m pytest services/control-plane-api/tests/test_sync_runtime_flow.py services/control-plane-api/tests/test_spoke_runtime_flow.py -q`
- Desktop: `npm run test --workspace @store/store-desktop`
- Desktop type safety: `npm run typecheck --workspace @store/store-desktop`
- Desktop build: `npm run build --workspace @store/store-desktop`
- Native: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
