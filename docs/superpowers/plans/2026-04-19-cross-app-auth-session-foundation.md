# Cross-App Auth And Session Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual and in-memory auth bootstrap behavior across the suite with a production-grade session model: redirect-based sign-in for `owner-web` and `platform-admin`, device-bound lifecycle cleanup for `store-desktop`, and durable pairing/session recovery for `store-mobile`.

**Architecture:** Keep the control-plane auth backend mostly intact and build a shared session foundation around it. Evolve `packages/auth` into the shared web session layer for browser control surfaces, preserve the existing device-bound desktop runtime contract while tightening restore/refresh/recovery behavior, and replace Android in-memory pairing/session repositories with durable local repositories that still consume the same runtime activation contract.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, Kotlin, Jetpack Compose, Android unit tests, existing control-plane `/v1/auth/*` routes, `@store/auth`, `@store/ui`, `@store/types`.

---

## File Structure

### Shared web auth/session foundation

- Modify: `packages/auth/src/index.ts`
  - Reduce this file to public exports and keep local-dev bootstrap helpers available only as explicit non-production utilities.
- Create: `packages/auth/src/webSession.ts`
  - Shared browser session contract, redirect entry helpers, persistence, callback parsing, refresh scheduling, and sign-out helpers for `owner-web` and `platform-admin`.
- Create: `packages/auth/src/webSession.test.ts`
  - Focused coverage for browser session persistence, restore, expiry, and callback parsing.
- Modify: `packages/auth/src/index.test.ts`
  - Keep export and legacy-bootstrap coverage aligned with the new package surface.

### Owner web

- Modify: `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
  - Stop treating session start as a token-entry action only; add restore, refresh, and sign-out orchestration.
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
  - Replace the token-paste gate with a real signed-out / callback / recovery entry model.
- Create: `apps/owner-web/src/control-plane/OwnerAuthEntrySurface.tsx`
  - Signed-out, loading, expired-session, and sign-in-required owner entry UI.
- Create: `apps/owner-web/src/control-plane/OwnerAuthEntrySurface.test.tsx`
  - Entry-surface behavior coverage.
- Modify: `apps/owner-web/src/App.test.tsx`
  - Update app-level bootstrap expectations away from manual token entry.

### Platform admin

- Modify: `apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts`
  - Add browser session restore, refresh, sign-out, and callback flow support.
- Modify: `apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx`
  - Replace token-entry bootstrap with platform sign-in and recovery states.
- Create: `apps/platform-admin/src/control-plane/PlatformAdminAuthEntrySurface.tsx`
  - Signed-out and recovery platform auth surface.
- Create: `apps/platform-admin/src/control-plane/PlatformAdminAuthEntrySurface.test.tsx`
  - Platform entry-surface behavior coverage.
- Modify: `apps/platform-admin/src/App.test.tsx`
  - Update app-level auth expectations for real sign-in lifecycle behavior.

### Store desktop

- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
  - Keep the existing runtime model, but make restore/refresh/recovery/sign-out explicit and deterministic.
- Modify: `apps/store-desktop/src/control-plane/storeRuntimeEntrySurface.tsx`
  - Refine signed-out activation, unlock, and revoked/expired recovery messaging as product states.
- Modify: `apps/store-desktop/src/control-plane/storeRuntimeLayout.tsx`
  - Surface live session posture and sign-out/recovery controls cleanly in the runtime shell.
- Modify: `apps/store-desktop/src/control-plane/storeRuntimeSessionStore.ts`
  - Tighten session persistence behavior if needed to support deterministic restore and sign-out clearing.
- Modify: `apps/store-desktop/src/control-plane/storeRuntimeLocalAuthStore.ts`
  - Preserve local unlock posture while aligning sign-out and revoked-session cleanup.
- Modify: `apps/store-desktop/src/App.test.tsx`
- Modify: `apps/store-desktop/src/App.browser-production.test.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeAuthLifecycle.test.tsx`
  - Activation, unlock, restore, refresh, sign-out, and recovery coverage.

### Store mobile

- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePairingRepository.kt`
  - Expand the contract so durable implementations can persist and clear pairing cleanly.
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileSessionRepository.kt`
  - Expand the contract for durable runtime-session persistence and explicit sign-out clearing.
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePersistentPairingRepository.kt`
  - Android-local pairing persistence.
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePersistentSessionRepository.kt`
  - Android-local runtime-session persistence.
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileHubClient.kt`
  - Keep the fake client for test/dev as needed, but align the contract with durable restore and explicit session recovery behavior.
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
  - Replace in-memory runtime repositories with durable ones and wire restore / recovery / sign-out / unpair behavior.
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingViewModel.kt`
  - Handle restore-on-boot, expired-session recovery, sign-out, and unpair logic.
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingScreen.kt`
  - Show recovery, resume, sign-out, and unpair actions.
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobilePairingRepositoryTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobileSessionRepositoryTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/pairing/PairingViewModelTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/StoreMobileAppBootstrapTest.kt`

### Docs

- Modify: `docs/runbooks/dev-workflow.md`
  - Document the new web sign-in env/settings expectations and runtime activation/pairing startup posture.
- Modify: `docs/WORKLOG.md`
  - Record the auth/session foundation slice and final verification commands.

## Task 1: Build the shared web auth/session foundation in `packages/auth`

**Files:**
- Create: `packages/auth/src/webSession.ts`
- Create: `packages/auth/src/webSession.test.ts`
- Modify: `packages/auth/src/index.ts`
- Modify: `packages/auth/src/index.test.ts`

- [ ] **Step 1: Write the failing shared-web-session tests**

Create `packages/auth/src/webSession.test.ts` to cover:

- browser callback parsing into a stable auth result
- session persistence and restore
- expiry detection
- session clear on sign-out
- local-dev bootstrap helpers staying separate from production session helpers

- [ ] **Step 2: Run the package test to verify it fails**

Run:

```bash
npm run test --workspace @store/auth
```

Expected: FAIL because the new shared web-session helpers do not exist yet.

- [ ] **Step 3: Implement the browser session contract**

Create `packages/auth/src/webSession.ts` with focused functions and types such as:

```ts
export type StoreWebSessionRecord = { accessToken: string; expiresAt: string };
export function loadStoreWebSession(storageKey: string): StoreWebSessionRecord | null;
export function saveStoreWebSession(storageKey: string, record: StoreWebSessionRecord): void;
export function clearStoreWebSession(storageKey: string): void;
export function isStoreWebSessionExpired(record: StoreWebSessionRecord, now?: number): boolean;
export function readKorsenexCallback(windowLike: Pick<Window, 'location' | 'history'>): { token: string | null };
export function buildKorsenexSignInUrl(args: { authorizeBaseUrl: string; returnTo: string; state?: string }): string;
export function shouldRefreshStoreWebSession(record: StoreWebSessionRecord, now?: number, leadSeconds?: number): boolean;
export async function signOutStoreWebSession(args: { storageKey: string; accessToken: string; signOut: (accessToken: string) => Promise<void> }): Promise<void>;
```

Keep this foundation generic enough for both web apps so `owner-web` and `platform-admin` do not re-implement redirect entry, refresh timing, or sign-out behavior separately.

- [ ] **Step 4: Re-export the new helpers without breaking the existing dev bootstrap API**

Modify `packages/auth/src/index.ts` so:

- local-dev bootstrap helpers stay available
- new web-session helpers become the primary shared browser auth surface

- [ ] **Step 5: Re-run the auth package tests**

Run:

```bash
npm run test --workspace @store/auth
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/auth/src/index.ts packages/auth/src/index.test.ts packages/auth/src/webSession.ts packages/auth/src/webSession.test.ts
git commit -m "feat: add shared web auth session foundation"
```

## Task 2: Replace owner-web token bootstrap with real web auth lifecycle

**Files:**
- Modify: `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerAuthEntrySurface.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerAuthEntrySurface.test.tsx`
- Modify: `apps/owner-web/src/App.test.tsx`

- [ ] **Step 1: Add failing owner auth-entry tests**

Create `OwnerAuthEntrySurface.test.tsx` to cover:

- signed-out entry showing `Sign in with Korsenex`
- loading or restoring session posture
- expired-session or revoked-session messaging

Also update `apps/owner-web/src/App.test.tsx` so production entry no longer expects manual token input.

- [ ] **Step 2: Run the owner-web tests to verify they fail**

Run:

```bash
npm run test --workspace @store/owner-web -- src/App.test.tsx src/control-plane/OwnerAuthEntrySurface.test.tsx
```

Expected: FAIL because owner-web still gates on `Korsenex token` input.

- [ ] **Step 3: Implement the owner auth entry surface**

Create `OwnerAuthEntrySurface.tsx` with product states for:

- signed out
- restoring
- session expired
- session revoked or invalid

Do not leak dev token-entry UI into production entry posture.

- [ ] **Step 4: Extend the owner workspace hook with web-session lifecycle**

Modify `useOwnerWorkspace.ts` to:

- restore persisted browser session on app load
- refresh before expiry when possible
- sign out cleanly
- start session from callback-exchange or explicit sign-in initiation rather than token paste

If the real redirect initiation is only a URL handoff in this slice, keep it explicit and env-driven.

- [ ] **Step 5: Refactor `OwnerWorkspace.tsx`**

Make `OwnerWorkspace.tsx`:

- render `OwnerWorkspaceShell` only when a live actor session exists
- otherwise render `OwnerAuthEntrySurface`
- keep local-dev bootstrap support only behind development-only behavior

- [ ] **Step 6: Re-run the owner-web tests**

Run:

```bash
npm run test --workspace @store/owner-web -- src/App.test.tsx src/control-plane/OwnerAuthEntrySurface.test.tsx
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/owner-web/src/control-plane/useOwnerWorkspace.ts apps/owner-web/src/control-plane/OwnerWorkspace.tsx apps/owner-web/src/control-plane/OwnerAuthEntrySurface.tsx apps/owner-web/src/control-plane/OwnerAuthEntrySurface.test.tsx apps/owner-web/src/App.test.tsx
git commit -m "feat: add owner web auth entry lifecycle"
```

## Task 3: Replace platform-admin token bootstrap with real web auth lifecycle

**Files:**
- Modify: `apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts`
- Modify: `apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx`
- Create: `apps/platform-admin/src/control-plane/PlatformAdminAuthEntrySurface.tsx`
- Create: `apps/platform-admin/src/control-plane/PlatformAdminAuthEntrySurface.test.tsx`
- Modify: `apps/platform-admin/src/App.test.tsx`

- [ ] **Step 1: Add failing platform auth-entry tests**

Create `PlatformAdminAuthEntrySurface.test.tsx` to cover:

- signed-out platform sign-in surface
- restore/loading posture
- expired or revoked session messaging

Update `apps/platform-admin/src/App.test.tsx` so app startup no longer depends on visible token-entry UI.

- [ ] **Step 2: Run the platform-admin tests to verify they fail**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/App.test.tsx src/control-plane/PlatformAdminAuthEntrySurface.test.tsx
```

Expected: FAIL because platform-admin still starts from manual token bootstrap.

- [ ] **Step 3: Implement the platform auth entry surface**

Create `PlatformAdminAuthEntrySurface.tsx` with:

- platform-branded sign-in CTA
- restore/loading state
- invalid, expired, and revoked recovery messages

- [ ] **Step 4: Extend the platform workspace hook with browser session lifecycle**

Modify `usePlatformAdminWorkspace.ts` to:

- restore browser session
- refresh before expiry
- support explicit sign-out
- bootstrap from callback/sign-in initiation rather than token-entry

- [ ] **Step 5: Refactor `PlatformAdminWorkspace.tsx`**

Make `PlatformAdminWorkspace.tsx`:

- render `PlatformAdminWorkspaceShell` only when actor/session are live
- otherwise render `PlatformAdminAuthEntrySurface`
- preserve local-dev bootstrap only under development-only logic

- [ ] **Step 6: Re-run the platform-admin tests**

Run:

```bash
npm run test --workspace @store/platform-admin -- src/App.test.tsx src/control-plane/PlatformAdminAuthEntrySurface.test.tsx
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx apps/platform-admin/src/control-plane/PlatformAdminAuthEntrySurface.tsx apps/platform-admin/src/control-plane/PlatformAdminAuthEntrySurface.test.tsx apps/platform-admin/src/App.test.tsx
git commit -m "feat: add platform admin auth entry lifecycle"
```

## Task 4: Tighten store-desktop runtime auth lifecycle and recovery

**Files:**
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/storeRuntimeEntrySurface.tsx`
- Modify: `apps/store-desktop/src/control-plane/storeRuntimeLayout.tsx`
- Modify: `apps/store-desktop/src/control-plane/storeRuntimeSessionStore.ts`
- Modify: `apps/store-desktop/src/control-plane/storeRuntimeLocalAuthStore.ts`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeAuthLifecycle.test.tsx`
- Modify: `apps/store-desktop/src/App.test.tsx`
- Modify: `apps/store-desktop/src/App.browser-production.test.tsx`

- [ ] **Step 1: Add failing desktop lifecycle tests**

Create `StoreRuntimeAuthLifecycle.test.tsx` to cover:

- restore of a persisted runtime session
- unlock-first posture when local auth is required
- expired-session refresh attempt
- fallback to activation or blocked posture when revoked
- explicit sign-out clearing live session state while preserving approved device posture where intended

Update `App.browser-production.test.tsx` only if needed to keep browser production posture explicit and non-developer-safe.

- [ ] **Step 2: Run the focused desktop auth tests to verify they fail**

Run:

```bash
npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeAuthLifecycle.test.tsx src/App.test.tsx src/App.browser-production.test.tsx
```

Expected: FAIL because the current runtime lifecycle is not fully modeled as explicit product states.

- [ ] **Step 3: Refine runtime lifecycle logic in the workspace hook**

Modify `useStoreRuntimeWorkspace.ts` so:

- session restore is deterministic
- refresh-before-expiry is explicit
- sign-out clears the correct runtime state
- revoked or invalid runtime responses map to specific recovery states rather than generic errors

Do not move shell composition or business flows into new logic here.

- [ ] **Step 4: Refine entry and layout surfaces**

Update:

- `storeRuntimeEntrySurface.tsx`
- `storeRuntimeLayout.tsx`

to make activation, unlock, expired-session, revoked-session, and signed-out posture clearly visible and actionable.

- [ ] **Step 5: Re-run the focused desktop tests**

Run:

```bash
npm run test --workspace @store/store-desktop -- src/control-plane/StoreRuntimeAuthLifecycle.test.tsx src/App.test.tsx src/App.browser-production.test.tsx
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/storeRuntimeEntrySurface.tsx apps/store-desktop/src/control-plane/storeRuntimeLayout.tsx apps/store-desktop/src/control-plane/storeRuntimeSessionStore.ts apps/store-desktop/src/control-plane/storeRuntimeLocalAuthStore.ts apps/store-desktop/src/control-plane/StoreRuntimeAuthLifecycle.test.tsx apps/store-desktop/src/App.test.tsx apps/store-desktop/src/App.browser-production.test.tsx
git commit -m "feat: tighten store desktop auth lifecycle"
```

## Task 5: Replace Android in-memory pairing/session storage with durable runtime persistence

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePairingRepository.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileSessionRepository.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePersistentPairingRepository.kt`
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePersistentSessionRepository.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileHubClient.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingViewModel.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingScreen.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobilePairingRepositoryTest.kt`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobileSessionRepositoryTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/pairing/PairingViewModelTest.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/StoreMobileAppBootstrapTest.kt`

- [ ] **Step 1: Add failing Android repository and pairing tests**

Expand `StoreMobilePairingRepositoryTest.kt` and create `StoreMobileSessionRepositoryTest.kt` to require:

- pairing persistence survives repository recreation
- runtime session persistence survives repository recreation
- sign-out clears runtime session without necessarily clearing paired device
- unpair clears both

Update `PairingViewModelTest.kt` to cover:

- restore of paired device and runtime session
- expired-session recovery path
- explicit sign-out
- explicit unpair

- [ ] **Step 2: Run the Android unit tests to verify they fail**

Run:

```bash
npm run ci:store-mobile
```

Expected: FAIL because the repositories are still in-memory and the view model does not support the full lifecycle.

- [ ] **Step 3: Introduce durable Android repositories**

Create:

- `StoreMobilePersistentPairingRepository.kt`
- `StoreMobilePersistentSessionRepository.kt`

using Android-local persistence appropriate for this app boundary. Keep them behind the existing interfaces so the rest of the app stays testable.

- [ ] **Step 4: Expand repository contracts carefully**

Modify the repository interfaces only as needed to support:

- save/load
- clear session
- clear pairing
- preserve pairing while clearing live session

- [ ] **Step 5: Refactor mobile app bootstrap and pairing flow**

Modify `StoreMobileApp.kt`, `PairingViewModel.kt`, and `PairingScreen.kt` so:

- paired device and runtime session are restored on app reopen
- shell mode is selected from restored runtime profile
- expired or invalid session falls back to a clear recovery posture
- sign-out and unpair are explicit user actions

- [ ] **Step 6: Re-run the Android unit tests**

Run:

```bash
npm run ci:store-mobile
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePairingRepository.kt apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileSessionRepository.kt apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePersistentPairingRepository.kt apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePersistentSessionRepository.kt apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileHubClient.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingViewModel.kt apps/store-mobile/app/src/main/java/com/store/mobile/ui/pairing/PairingScreen.kt apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobilePairingRepositoryTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobileSessionRepositoryTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/ui/pairing/PairingViewModelTest.kt apps/store-mobile/app/src/test/java/com/store/mobile/StoreMobileAppBootstrapTest.kt
git commit -m "feat: add durable store mobile auth lifecycle"
```

## Task 6: Final cross-app verification and docs

**Files:**
- Modify: `docs/runbooks/dev-workflow.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Update the developer workflow runbook**

Document:

- expected env/setup for real web sign-in
- developer-only local bootstrap posture
- desktop activation/unlock expectations
- mobile pairing and session persistence posture

- [ ] **Step 2: Record the slice in the worklog**

Update `docs/WORKLOG.md` with:

- what changed
- which surfaces were affected
- the final verification commands

- [ ] **Step 3: Run focused verification for every affected surface**

Run:

```bash
npm run test --workspace @store/auth
npm run test --workspace @store/owner-web
npm run typecheck --workspace @store/owner-web
npm run build --workspace @store/owner-web
npm run test --workspace @store/platform-admin
npm run typecheck --workspace @store/platform-admin
npm run build --workspace @store/platform-admin
npm run ci:store-desktop
npm run ci:store-mobile
git -c core.safecrlf=false diff --check
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/runbooks/dev-workflow.md docs/WORKLOG.md
git commit -m "docs: record cross-app auth session foundation"
```
