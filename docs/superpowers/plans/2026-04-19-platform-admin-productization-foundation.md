# Platform Admin Productization Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `platform-admin` into a platform control tower with a modern light/dark shell, an exception-driven overview, and focused `Release`, `Operations`, `Tenants`, `Commercial`, and `Settings` surfaces while preserving the existing tenant and billing actions.

**Architecture:** Keep `usePlatformAdminWorkspace` as the domain state boundary, extend it with real control-plane posture reads (`observability`, `security-controls`, `environment-contract`), and split the current monolithic `PlatformAdminWorkspace.tsx` into a shell plus focused surfaces. Reuse the shared theme foundation from `packages/ui`, but add platform-specific shell primitives so the app reads as a technical control tower rather than a recycled owner console.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, `@store/ui`, `@store/types`, existing control-plane HTTP routes in `services/control-plane-api`.

---

## File Structure

### Existing files to modify

- `apps/platform-admin/src/App.tsx`
  - Keep the root theme provider and app entry, but wire the new platform shell cleanly.
- `apps/platform-admin/src/App.test.tsx`
  - Update the app-level tests for the new overview-first product model and new control-plane reads.
- `apps/platform-admin/src/control-plane/client.ts`
  - Extend the platform-admin client with `getSecurityControls()` and `getEnvironmentContract()`.
- `apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts`
  - Add shell-navigation state, derived overview posture, new system-read state, and keep existing tenant/commercial actions intact.
- `apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx`
  - Reduce this file to orchestration and selected-surface composition instead of inline section-stack rendering.
- `packages/ui/src/index.tsx`
  - Export new platform shell primitives.
- `packages/ui/src/index.test.tsx`
  - Add coverage for the new exports.

### New files to create

- `apps/platform-admin/src/control-plane/PlatformAdminWorkspaceShell.tsx`
  - Own the control-tower shell layout, selected top-level section, and overview composition.
- `apps/platform-admin/src/control-plane/platformAdminOverviewModel.ts`
  - Centralize signal and exception derivation from workspace state so UI stays presentational.
- `apps/platform-admin/src/control-plane/PlatformAdminWorkspaceShell.test.tsx`
  - Product-shell behavior coverage: default overview, nav switching, and exception-driven rendering.
- `packages/ui/src/platformShell.tsx`
  - Platform-specific shell primitives: nav rail, command header, signal row, and exception board wrappers.
- `packages/ui/src/platformShell.test.tsx`
  - Focused UI tests for the shared platform primitives.

### Existing files to check while implementing

- `packages/ui/src/theme.tsx`
  - Reuse the shared theme contract; do not fork theme logic.
- `packages/ui/src/ownerShell.tsx`
  - Reuse patterns, but do not force platform-admin to inherit owner wording or structure.
- `packages/types/src/index.ts`
  - Add system posture types for the new client reads.

## Task 1: Add system-posture types and client reads

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/platform-admin/src/control-plane/client.ts`
- Test: `apps/platform-admin/src/App.test.tsx`

- [ ] **Step 1: Add failing app-level expectations for system posture**

Update `apps/platform-admin/src/App.test.tsx` so the control-plane bootstrap mocks include:

- `GET /v1/system/security-controls`
- `GET /v1/system/environment-contract`

Add assertions on overview-visible platform posture such as:

- environment contract values rendering
- secure-header or rate-limit posture rendering
- release/environment context in the control-tower header

- [ ] **Step 2: Run the platform-admin app test to verify the new expectations fail**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/App.test.tsx
```

Expected:

- FAIL because `client.ts` and `usePlatformAdminWorkspace.ts` do not yet load the new system posture routes

- [ ] **Step 3: Add the missing shared TS contracts**

Extend `packages/types/src/index.ts` with minimal types for:

- `ControlPlaneSystemSecurityControls`
- `ControlPlaneSystemEnvironmentContract`

Keep the shape narrowly aligned to current backend responses; do not invent speculative fields.

- [ ] **Step 4: Extend the platform-admin client**

Add:

```ts
getSecurityControls(accessToken: string)
getEnvironmentContract(accessToken: string)
```

Both should call the existing `/v1/system/...` routes and return the typed payloads.

- [ ] **Step 5: Re-run the focused app test**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/App.test.tsx
```

Expected:

- still FAIL, but now on missing workspace/state wiring rather than missing client methods

- [ ] **Step 6: Commit**

```bash
git add packages/types/src/index.ts apps/platform-admin/src/control-plane/client.ts apps/platform-admin/src/App.test.tsx
git commit -m "feat: add platform admin system posture client reads"
```

## Task 2: Extend workspace state and derive overview posture

**Files:**
- Modify: `apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts`
- Create: `apps/platform-admin/src/control-plane/platformAdminOverviewModel.ts`
- Test: `apps/platform-admin/src/App.test.tsx`

- [ ] **Step 1: Write a failing derived-overview test**

Add a focused expectation in `src/App.test.tsx` or a small new test case that requires:

- default landing on `Overview`
- a release/incident posture band
- at least one exception surfaced from dead-letter, degraded branch, or backup risk input

- [ ] **Step 2: Run the focused platform-admin test**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/App.test.tsx
```

Expected:

- FAIL because the workspace still exposes only the old flat section state

- [ ] **Step 3: Extend workspace state**

Update `usePlatformAdminWorkspace.ts` to add:

- `activeSection`
- `setActiveSection`
- `securityControls`
- `environmentContract`
- derived `platformOverviewSignals`
- derived `platformExceptions`

Load the new posture reads during `startSession()` in parallel with the existing tenant, billing-plan, and observability reads.

- [ ] **Step 4: Move derivation into a focused helper**

Create `platformAdminOverviewModel.ts` to map workspace data into:

- signal row items
- critical exception items
- tenant exception items
- release evidence summary items

Keep UI files presentational; do not bury business-ish derivation in JSX.

- [ ] **Step 5: Re-run the focused platform-admin test**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/App.test.tsx
```

Expected:

- PASS for the new overview/state expectations, or at least move the failure into the new shell render layer

- [ ] **Step 6: Commit**

```bash
git add apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts apps/platform-admin/src/control-plane/platformAdminOverviewModel.ts apps/platform-admin/src/App.test.tsx
git commit -m "feat: add platform admin overview state model"
```

## Task 3: Add shared platform shell primitives in `packages/ui`

**Files:**
- Create: `packages/ui/src/platformShell.tsx`
- Create: `packages/ui/src/platformShell.test.tsx`
- Modify: `packages/ui/src/index.tsx`
- Modify: `packages/ui/src/index.test.tsx`

- [ ] **Step 1: Add a failing shared-UI test**

Create `packages/ui/src/platformShell.test.tsx` with coverage for:

- nav rail rendering and active state
- command header rendering
- signal row rendering
- exception board rendering

- [ ] **Step 2: Run the focused UI test**

Run:

```bash
npm run test --workspace @store/ui -- src/platformShell.test.tsx
```

Expected:

- FAIL because the primitive file does not exist yet

- [ ] **Step 3: Implement the platform shell primitives**

Create `packages/ui/src/platformShell.tsx` with focused components for:

- `PlatformCommandShell`
- `PlatformNavRail`
- `PlatformCommandHeader`
- `PlatformSignalRow`
- `PlatformExceptionBoard`
- optional `PlatformPanel` wrapper if it reduces duplication cleanly

Use the existing semantic tokens from `theme.tsx`; do not create app-specific hardcoded colors outside the token set.

- [ ] **Step 4: Export the primitives**

Update `packages/ui/src/index.tsx` and `packages/ui/src/index.test.tsx` so the new components are exported and smoke-covered.

- [ ] **Step 5: Re-run the UI tests**

Run:

```bash
npm run test --workspace @store/ui
```

Expected:

- PASS with the new platform shell coverage

- [ ] **Step 6: Commit**

```bash
git add packages/ui/src/platformShell.tsx packages/ui/src/platformShell.test.tsx packages/ui/src/index.tsx packages/ui/src/index.test.tsx
git commit -m "feat: add platform admin shell primitives"
```

## Task 4: Split the monolithic workspace into a control-tower shell

**Files:**
- Create: `apps/platform-admin/src/control-plane/PlatformAdminWorkspaceShell.tsx`
- Modify: `apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx`
- Test: `apps/platform-admin/src/App.test.tsx`
- Create: `apps/platform-admin/src/control-plane/PlatformAdminWorkspaceShell.test.tsx`

- [ ] **Step 1: Write a failing shell test**

Create `PlatformAdminWorkspaceShell.test.tsx` to cover:

- default `Overview` selection
- switching to `Release`, `Operations`, `Tenants`, `Commercial`, `Settings`
- overview rendering the critical exceptions board and posture band

- [ ] **Step 2: Run the focused shell test**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/control-plane/PlatformAdminWorkspaceShell.test.tsx
```

Expected:

- FAIL because the shell file does not exist yet

- [ ] **Step 3: Implement the new shell**

Create `PlatformAdminWorkspaceShell.tsx` that:

- consumes the existing workspace state object
- renders the platform nav rail and command header
- shows `Overview` by default
- renders focused top-level surfaces instead of the old stacked sections

The first pass should keep the detail sub-surfaces simple and reuse current actions, but the hierarchy must be real.

- [ ] **Step 4: Reduce `PlatformAdminWorkspace.tsx` to orchestration**

Refactor `PlatformAdminWorkspace.tsx` so it only handles:

- local-dev bootstrap
- app/session startup side effects
- rendering `PlatformAdminWorkspaceShell`

Do not leave the old inline section stack in place behind hidden conditionals.

- [ ] **Step 5: Re-run focused platform-admin tests**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/App.test.tsx src/control-plane/PlatformAdminWorkspaceShell.test.tsx
```

Expected:

- PASS for the new shell and updated app-level platform-admin expectations

- [ ] **Step 6: Commit**

```bash
git add apps/platform-admin/src/control-plane/PlatformAdminWorkspaceShell.tsx apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx apps/platform-admin/src/control-plane/PlatformAdminWorkspaceShell.test.tsx apps/platform-admin/src/App.test.tsx
git commit -m "feat: productize platform admin shell"
```

## Task 5: Preserve tenant and commercial workflows inside the new IA

**Files:**
- Modify: `apps/platform-admin/src/control-plane/PlatformAdminWorkspaceShell.tsx`
- Modify: `apps/platform-admin/src/App.test.tsx`

- [ ] **Step 1: Add failing workflow assertions under the new navigation model**

Update `App.test.tsx` to explicitly navigate through the new shell and verify:

- tenant creation still works under `Tenants`
- owner invite still works under `Tenants`
- billing-plan creation still works under `Commercial`
- tenant suspension still works under `Tenants` or `Commercial`, whichever the shell chooses

- [ ] **Step 2: Run the focused test**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/App.test.tsx
```

Expected:

- FAIL where the new shell has not yet preserved the old action paths cleanly

- [ ] **Step 3: Wire the detail surfaces**

Update `PlatformAdminWorkspaceShell.tsx` so the `Tenants` and `Commercial` surfaces expose the preserved forms and actions with the new layout.

Keep the existing payload behavior unchanged; this task is about discoverability and hierarchy, not business-logic rewrites.

- [ ] **Step 4: Re-run the focused test**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/App.test.tsx
```

Expected:

- PASS for the preserved tenant and billing workflows under the new shell

- [ ] **Step 5: Commit**

```bash
git add apps/platform-admin/src/control-plane/PlatformAdminWorkspaceShell.tsx apps/platform-admin/src/App.test.tsx
git commit -m "feat: preserve platform admin tenant workflows"
```

## Task 6: Full verification and merge preparation

**Files:**
- Review all modified files above

- [ ] **Step 1: Run full platform-admin tests**

```bash
npm run test --workspace @store/platform-admin
```

Expected:

- PASS

- [ ] **Step 2: Run shared UI tests**

```bash
npm run test --workspace @store/ui
```

Expected:

- PASS

- [ ] **Step 3: Run typechecks**

```bash
npm run typecheck --workspace @store/platform-admin
npm run typecheck --workspace @store/ui
```

Expected:

- PASS

- [ ] **Step 4: Run builds**

```bash
npm run build --workspace @store/platform-admin
npm run build --workspace @store/ui
```

Expected:

- PASS

- [ ] **Step 5: Run whitespace / patch sanity check**

```bash
git -c core.safecrlf=false diff --check
```

Expected:

- no output

- [ ] **Step 6: Commit final verification fixes if needed**

```bash
git add <any changed files>
git commit -m "test: finalize platform admin productization coverage"
```

## Review Notes

- Keep `usePlatformAdminWorkspace.ts` as the main domain-state boundary; avoid creating a second logic store.
- Prefer one new overview-model helper over scattering derived status logic across multiple JSX files.
- Reuse the shared token system exactly; do not add a second theme implementation for platform-admin.
- Treat `Release` and `Operations` as real top-level surfaces even if the first slice uses compact summaries rather than deep sub-routes.
- Any additional platform posture fields should come from existing control-plane endpoints unless a missing API is proven necessary during implementation.
