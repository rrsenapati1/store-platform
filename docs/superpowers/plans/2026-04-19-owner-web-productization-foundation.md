# Owner Web Productization Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `owner-web` into a multi-branch owner command center with a modern shell, live-operations-first overview, and shared light/dark theme foundations that also wire into `store-desktop` and `platform-admin`.

**Architecture:** Keep the current owner-web data and action hooks as the domain seam, but stop using [OwnerWorkspace.tsx](/d:/codes/projects/store/apps/owner-web/src/control-plane/OwnerWorkspace.tsx) as the rendering model. Introduce shared semantic theme tokens and a theme provider in `packages/ui`, then build a new owner command shell with focused top-level screens (`Overview`, `Operations`, `Commercial`, `Catalog`, `Workforce`, `Settings`). Re-home existing owner sections beneath those screens without changing backend contracts, and add shell-level theme plumbing to `store-desktop` and `platform-admin` so all primary apps share one visual system.

**Tech Stack:** React, TypeScript, Vite, Vitest, shared `@store/ui`, existing control-plane owner-web hooks, CSS variables via inline React styling or shared token helpers

---

## File Structure

### Large-file governance

- `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
  - Classification: `mixed-responsibility`
  - Current role: owner session bootstrap, onboarding forms, commercial/admin tools, reporting, and runtime controls all in one file
  - Rule: do not continue adding screens or visual logic here; split it into a command shell plus focused screen files
- `packages/ui/src/index.tsx`
  - Classification: `shared surface barrel + primitives`
  - Rule: keep exports stable, but move significant new implementation into focused modules rather than bloating the barrel file

### Shared theming and shell primitives

- Create: `packages/ui/src/theme.tsx`
  - Shared theme provider, semantic token map, theme-mode persistence, resolved-theme logic, and app-shell helper hooks
- Create: `packages/ui/src/theme.test.tsx`
  - Theme mode, persistence, and resolved-theme coverage
- Create: `packages/ui/src/ownerShell.tsx`
  - Owner command-shell frame, navigation rail, command header, filter strip, signal row, exception board, and supporting layout primitives
- Create: `packages/ui/src/ownerShell.test.tsx`
  - Shell primitive coverage
- Modify: `packages/ui/src/index.tsx`
  - Re-export the new theme and owner-shell primitives
- Modify: `packages/ui/src/index.test.tsx`
  - Cover the new primitives through the package barrel

### Owner-web shell and screen composition

- Create: `apps/owner-web/src/control-plane/ownerWorkspaceScreens.ts`
  - Screen IDs, branch-filter types, route helpers, and navigation metadata
- Create: `apps/owner-web/src/control-plane/ownerThemeActions.ts`
  - App-local wiring for theme mode read/write if a thin adapter is useful
- Create: `apps/owner-web/src/control-plane/OwnerWorkspaceShell.tsx`
  - Top-level owner shell composition with nav, command header, branch filter, and active screen rendering
- Create: `apps/owner-web/src/control-plane/OwnerOverviewScreen.tsx`
  - Default command-center overview
- Create: `apps/owner-web/src/control-plane/OwnerOperationsScreen.tsx`
  - Groups procurement, receiving, replenishment, restock, compliance, returns approvals, sync/runtime, and batch-expiry posture
- Create: `apps/owner-web/src/control-plane/OwnerCommercialScreen.tsx`
  - Groups promotions, gift cards, price tiers, customer insights, branch performance, and billing lifecycle
- Create: `apps/owner-web/src/control-plane/OwnerCatalogScreen.tsx`
  - Groups catalog, branch catalog, barcode, and barcode runtime tools
- Create: `apps/owner-web/src/control-plane/OwnerWorkforceScreen.tsx`
  - Groups attendance, shifts, cashier sessions, device claims, runtime policy, and workforce audit
- Create: `apps/owner-web/src/control-plane/OwnerSettingsScreen.tsx`
  - Holds tenant summary, branches, onboarding residue, and device registration
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
  - Reduce to a workspace-state host that mounts `OwnerWorkspaceShell`
- Modify: `apps/owner-web/src/App.tsx`
  - Keep minimal; continue rendering the top-level owner workspace through the new shell

### Owner-web tests

- Create: `apps/owner-web/src/control-plane/OwnerWorkspaceShell.test.tsx`
  - Navigation, default overview, branch-filter routing, and theme toggle coverage
- Create: `apps/owner-web/src/control-plane/OwnerOverviewScreen.test.tsx`
  - Command-center overview coverage
- Modify: `apps/owner-web/src/control-plane/OwnerBranchPerformanceSection.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerRuntimePolicySection.test.tsx`
  - Preserve behavior for representative sections now rendered through the new shell
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.*.test.tsx`
  - Update existing workspace tests that assumed the old linear section stack

### Cross-app theme adoption

- Modify: `apps/store-desktop/src/App.tsx`
  - Wrap the runtime in the shared theme provider and baseline theme mode wiring
- Modify: `apps/platform-admin/src/App.tsx`
  - Wrap platform admin in the shared theme provider and baseline theme mode wiring
- Modify: relevant smoke tests under:
  - `apps/store-desktop/src/App.test.tsx`
  - `apps/platform-admin/src/App.test.tsx`
  - only as needed for shell/theme setup

### Docs

- Modify: `docs/WORKLOG.md`
  - Record the owner-web productization and shared-theme slice
- Modify: `docs/runbooks/dev-workflow.md`
  - Update theme/dev-shell notes only if the local developer flow changes materially

## Task 1: Add failing shared-theme and owner-shell tests

**Files:**
- Create: `packages/ui/src/theme.test.tsx`
- Create: `packages/ui/src/ownerShell.test.tsx`
- Modify: `packages/ui/src/index.test.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerWorkspaceShell.test.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerOverviewScreen.test.tsx`

- [ ] **Step 1: Write the failing theme tests**

Add tests that assert:

- theme mode supports `light`, `dark`, and `system`
- explicit user choice persists locally
- `system` resolves from the color-scheme preference
- fallback resolves to `light` when no system signal is available

- [ ] **Step 2: Write the failing shared owner-shell tests**

Add tests that assert shared owner-shell primitives can render:

- a navigation rail
- a command header
- an overview signal row
- an exception board

- [ ] **Step 3: Write the failing owner-web shell tests**

Create `OwnerWorkspaceShell.test.tsx` to assert:

- `Overview` is the default screen
- top-level navigation includes `Overview`, `Operations`, `Commercial`, `Catalog`, `Workforce`, and `Settings`
- branch filter defaults to `all branches`
- drill-down state is encoded in shell route/query state
- theme toggle is present and updates mode state

- [ ] **Step 4: Write the failing overview-screen tests**

Create `OwnerOverviewScreen.test.tsx` to assert:

- business posture band renders
- exceptions board renders prioritized items
- branch performance panel and workforce/runtime panel render
- exception interactions call the provided drill-down handlers

- [ ] **Step 5: Run the focused tests to verify they fail**

Run:

- `npm run test --workspace @store/ui -- src/theme.test.tsx`
- `npm run test --workspace @store/ui -- src/ownerShell.test.tsx`
- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerWorkspaceShell.test.tsx`
- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerOverviewScreen.test.tsx`

Expected: FAIL with missing theme and shell implementations.

- [ ] **Step 6: Commit**

```bash
git add packages/ui/src/theme.test.tsx packages/ui/src/ownerShell.test.tsx packages/ui/src/index.test.tsx apps/owner-web/src/control-plane/OwnerWorkspaceShell.test.tsx apps/owner-web/src/control-plane/OwnerOverviewScreen.test.tsx
git commit -m "test: add owner web productization coverage"
```

## Task 2: Implement the shared theme system

**Files:**
- Create: `packages/ui/src/theme.tsx`
- Create: `packages/ui/src/theme.test.tsx`
- Modify: `packages/ui/src/index.tsx`
- Modify: `packages/ui/src/index.test.tsx`

- [ ] **Step 1: Implement the semantic token contract**

Create `theme.tsx` with:

- `ThemeMode = 'light' | 'dark' | 'system'`
- resolved-theme computation
- semantic token groups for surfaces, text, borders, accents, states, spacing, radius, shadow, and motion

- [ ] **Step 2: Implement provider and hook wiring**

Expose focused APIs such as:

```tsx
export function StoreThemeProvider(...) { ... }
export function useStoreTheme() { ... }
export function resolveThemeMode(...) { ... }
```

Keep the public API small and app-shell-oriented.

- [ ] **Step 3: Implement persistence and precedence**

Support:

- explicit user-selected mode persistence
- `system` mode resolution from `matchMedia`
- precedence:
  1. explicit mode
  2. system preference when mode is `system`
  3. light fallback

- [ ] **Step 4: Re-export through the package barrel**

Update `packages/ui/src/index.tsx` to re-export the theme primitives.

- [ ] **Step 5: Run the UI package tests**

Run:

- `npm run test --workspace @store/ui`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packages/ui/src/theme.tsx packages/ui/src/theme.test.tsx packages/ui/src/index.tsx packages/ui/src/index.test.tsx
git commit -m "feat: add shared app theme system"
```

## Task 3: Implement owner command-shell primitives

**Files:**
- Create: `packages/ui/src/ownerShell.tsx`
- Create: `packages/ui/src/ownerShell.test.tsx`
- Modify: `packages/ui/src/index.tsx`

- [ ] **Step 1: Implement the owner-shell layout primitives**

Create focused shared primitives such as:

```tsx
export function OwnerCommandShell(...) { ... }
export function OwnerNavRail(...) { ... }
export function OwnerCommandHeader(...) { ... }
export function OwnerSignalRow(...) { ... }
export function OwnerExceptionBoard(...) { ... }
export function OwnerPanel(...) { ... }
```

- [ ] **Step 2: Apply the new theme tokens**

Use semantic tokens from `theme.tsx` instead of hard-coded colors so the shell works in both light and dark themes.

- [ ] **Step 3: Re-export the owner-shell primitives**

Update the package barrel to export the owner-shell components.

- [ ] **Step 4: Run the shared-shell tests**

Run:

- `npm run test --workspace @store/ui -- src/ownerShell.test.tsx`
- `npm run test --workspace @store/ui`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/ui/src/ownerShell.tsx packages/ui/src/ownerShell.test.tsx packages/ui/src/index.tsx
git commit -m "feat: add owner command shell primitives"
```

## Task 4: Build the owner-web shell, navigation, and branch-filter model

**Files:**
- Create: `apps/owner-web/src/control-plane/ownerWorkspaceScreens.ts`
- Create: `apps/owner-web/src/control-plane/OwnerWorkspaceShell.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Modify: `apps/owner-web/src/App.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspaceShell.test.tsx`

- [ ] **Step 1: Add the screen and branch-filter model**

Create `ownerWorkspaceScreens.ts` with:

- top-level screen IDs
- branch filter type
- route/query helpers for branch-aware state
- navigation metadata

- [ ] **Step 2: Implement the command shell**

Create `OwnerWorkspaceShell.tsx` to render:

- left navigation rail
- top command header
- branch filter
- theme mode control
- active screen body

Make branch-aware route state deterministic through URL query state.

- [ ] **Step 3: Reduce `OwnerWorkspace.tsx` to a workspace-state host**

Keep:

- session bootstrap and workspace hook ownership
- owner access token and tenant/branch data

Move out:

- visual layout
- page hierarchy
- top-level navigation

- [ ] **Step 4: Run the shell tests**

Run:

- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerWorkspaceShell.test.tsx`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/owner-web/src/control-plane/ownerWorkspaceScreens.ts apps/owner-web/src/control-plane/OwnerWorkspaceShell.tsx apps/owner-web/src/control-plane/OwnerWorkspace.tsx apps/owner-web/src/App.tsx apps/owner-web/src/control-plane/OwnerWorkspaceShell.test.tsx
git commit -m "feat: add owner web command shell"
```

## Task 5: Build the overview screen and modern owner landing posture

**Files:**
- Create: `apps/owner-web/src/control-plane/OwnerOverviewScreen.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerOverviewScreen.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerBranchPerformanceSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerBranchPerformanceSection.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerRuntimePolicySection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerRuntimePolicySection.test.tsx`

- [ ] **Step 1: Implement the command-center overview**

Build `OwnerOverviewScreen.tsx` with:

- command header context already supplied by shell
- business posture band
- prioritized exceptions board
- branch performance summary panel
- workforce/runtime panel
- commercial pulse panel

- [ ] **Step 2: Define overview drill-down boundaries**

Make overview widgets summary-only and ensure they link into canonical deeper screens instead of duplicating full detailed surfaces.

- [ ] **Step 3: Adapt branch-performance and runtime sections for overview hosting**

Refactor representative sections only as needed so they can render compact summary posture inside the overview without assuming they own a full page.

- [ ] **Step 4: Run the overview and representative section tests**

Run:

- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerOverviewScreen.test.tsx`
- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerBranchPerformanceSection.test.tsx`
- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerRuntimePolicySection.test.tsx`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/owner-web/src/control-plane/OwnerOverviewScreen.tsx apps/owner-web/src/control-plane/OwnerOverviewScreen.test.tsx apps/owner-web/src/control-plane/OwnerBranchPerformanceSection.tsx apps/owner-web/src/control-plane/OwnerBranchPerformanceSection.test.tsx apps/owner-web/src/control-plane/OwnerRuntimePolicySection.tsx apps/owner-web/src/control-plane/OwnerRuntimePolicySection.test.tsx
git commit -m "feat: add owner command center overview"
```

## Task 6: Re-home existing owner tools under focused screens

**Files:**
- Create: `apps/owner-web/src/control-plane/OwnerOperationsScreen.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerCommercialScreen.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerCatalogScreen.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerWorkforceScreen.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerSettingsScreen.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerGiftCardSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerPriceTierSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerReceivingSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerProcurementSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerReplenishmentSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerRestockSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerBatchExpirySection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerAttendanceSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCashierSessionSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerShiftSessionSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkforceAuditSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerDeviceClaimSection.tsx`
- Modify: owner-web focused tests for these sections only as needed

- [ ] **Step 1: Create thin screen wrappers for the five non-overview areas**

Each screen should:

- own its top-level title and layout
- group the existing sections coherently
- avoid duplicating domain logic

- [ ] **Step 2: Adapt existing sections for embedded hosting**

Remove or soften redundant full-page framing where necessary so the new screen wrappers own page structure.

- [ ] **Step 3: Wire the new screens into the shell**

Ensure:

- overview remains default
- navigation switches screens cleanly
- branch filter state is passed consistently to branch-aware sections

- [ ] **Step 4: Run focused owner-web tests**

Run at least:

- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerPromotionCampaignSection.test.tsx`
- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerCustomerInsightsSection.test.tsx`
- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerCashierSessionSection.test.tsx`
- `npm run test --workspace @store/owner-web -- src/control-plane/OwnerShiftSessionSection.test.tsx`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/owner-web/src/control-plane/OwnerOperationsScreen.tsx apps/owner-web/src/control-plane/OwnerCommercialScreen.tsx apps/owner-web/src/control-plane/OwnerCatalogScreen.tsx apps/owner-web/src/control-plane/OwnerWorkforceScreen.tsx apps/owner-web/src/control-plane/OwnerSettingsScreen.tsx apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx apps/owner-web/src/control-plane/OwnerGiftCardSection.tsx apps/owner-web/src/control-plane/OwnerPriceTierSection.tsx apps/owner-web/src/control-plane/OwnerReceivingSection.tsx apps/owner-web/src/control-plane/OwnerProcurementSection.tsx apps/owner-web/src/control-plane/OwnerReplenishmentSection.tsx apps/owner-web/src/control-plane/OwnerRestockSection.tsx apps/owner-web/src/control-plane/OwnerBatchExpirySection.tsx apps/owner-web/src/control-plane/OwnerAttendanceSection.tsx apps/owner-web/src/control-plane/OwnerCashierSessionSection.tsx apps/owner-web/src/control-plane/OwnerShiftSessionSection.tsx apps/owner-web/src/control-plane/OwnerWorkforceAuditSection.tsx apps/owner-web/src/control-plane/OwnerDeviceClaimSection.tsx
git commit -m "feat: organize owner tools into focused screens"
```

## Task 7: Adopt the theme system in owner-web, store-desktop, and platform-admin

**Files:**
- Modify: `apps/owner-web/src/App.tsx`
- Modify: `apps/store-desktop/src/App.tsx`
- Modify: `apps/platform-admin/src/App.tsx`
- Modify: relevant smoke tests in those apps as needed

- [ ] **Step 1: Wrap owner-web in the shared theme provider**

Make theme mode available through the owner shell and ensure light/dark/system all render correctly.

- [ ] **Step 2: Add baseline shell-level theme adoption to store-desktop**

Do not redesign store-desktop again in this slice. Only adopt the shared theme provider and shell token usage where it is safe.

- [ ] **Step 3: Add baseline shell-level theme adoption to platform-admin**

Keep this minimal: shared provider and shell token usage only.

- [ ] **Step 4: Run app smoke tests**

Run:

- `npm run test --workspace @store/owner-web -- src/App.test.tsx`
- `npm run test --workspace @store/store-desktop -- src/App.test.tsx`
- `npm run test --workspace @store/platform-admin`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/owner-web/src/App.tsx apps/store-desktop/src/App.tsx apps/platform-admin/src/App.tsx
git commit -m "feat: adopt shared app themes"
```

## Task 8: Final verification and docs

**Files:**
- Modify: `docs/WORKLOG.md`
- Modify: `docs/runbooks/dev-workflow.md` only if needed

- [ ] **Step 1: Update the worklog**

Record:

- owner-web productization foundation
- shared theme foundation
- verification commands actually run

- [ ] **Step 2: Update developer workflow docs only if necessary**

Only touch `docs/runbooks/dev-workflow.md` if theme or shell wiring changes how local app startup or inspection works.

- [ ] **Step 3: Run the full verification set**

Run:

- `npm run test --workspace @store/ui`
- `npm run test --workspace @store/owner-web`
- `npm run typecheck --workspace @store/owner-web`
- `npm run build --workspace @store/owner-web`
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `npm run test --workspace @store/platform-admin`
- `npm run typecheck --workspace @store/platform-admin`
- `npm run build --workspace @store/platform-admin`
- `git -c core.safecrlf=false diff --check`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add docs/WORKLOG.md docs/runbooks/dev-workflow.md
git commit -m "docs: record owner web productization foundation"
```
