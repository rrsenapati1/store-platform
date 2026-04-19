# Owner Web Productization Foundation Design

Date: 2026-04-19
Owner: Codex
Status: Drafted after design approval

## Goal

Turn `owner-web` from a long onboarding-shaped section stack into a product-quality tenant command center.

This slice is not about adding new backend authority. It is about making the existing owner surface feel like serious enterprise software with a clear operational hierarchy, modern interaction model, and reusable cross-app visual foundation.

When this slice is complete:

- owners should land in a real command center rather than a linear tool dump
- live operational oversight should become the default posture
- existing commercial, catalog, workforce, and settings tools should remain available but move behind stronger product structure
- the repo should gain a shared `light` and `dark` theme foundation that can be reused across `owner-web`, `store-desktop`, `platform-admin`, and later `store-mobile`

## Problem Statement

The current owner surface is functionally broad but product-wise weak.

Today:

- [OwnerWorkspace.tsx](/d:/codes/projects/store/apps/owner-web/src/control-plane/OwnerWorkspace.tsx) is a long sequence of independent sections
- onboarding residue, procurement, reporting, pricing, customer, workforce, runtime, and device tools all appear in one flat stack
- the owner does not get a meaningful default posture or a clear “what needs attention now?” answer
- the surface reads like a control-plane capability inventory rather than a command center
- visual hierarchy is weak, navigation hierarchy is weak, and the product language is inconsistent with the newer `store-desktop` direction

This creates the exact failure mode the user called out: the app works, but it does not look or feel like a polished enterprise product.

## Chosen Model

The accepted model is:

- `owner-web` becomes the next productization target after `store-desktop`
- the first pass optimizes for `daily owner operations`
- the surface becomes a `multi-branch command center with branch drill-down`
- the default focus is `live operations oversight first`, not onboarding or static administration
- the app adopts a smaller top-level product model instead of exposing every module equally
- this slice includes a reusable shared theme and design-system foundation with both `light` and `dark` modes

This is a `command-center owner console`, not a cosmetic cleanup.

## Scope

### In Scope

- product-quality rewrite of `owner-web` around a command-center shell
- new owner information architecture with:
  - `Overview`
  - `Operations`
  - `Commercial`
  - `Catalog`
  - `Workforce`
  - `Settings`
- `Overview` as the default landing surface
- multi-branch context with branch drill-down and branch filtering
- shared `light` / `dark` theme foundation in `packages/ui`
- baseline theme plumbing for:
  - `owner-web`
  - `store-desktop`
  - `platform-admin`
- modern visual, motion, and layout tokens that can later be adopted by `store-mobile`
- preservation of current owner-web domain actions and backend contracts wherever possible

### Out Of Scope

- full redesign of `platform-admin`
- full redesign of `store-mobile`
- deep redesign of every owner submodule in the first pass
- large backend domain changes
- advanced charting or analytics expansion beyond what the current data can support
- animation-heavy visual experimentation that harms performance

## Product Principles

The rewrite should follow these principles:

1. `Command center over tool cabinet`
   - the owner lands in business posture first
   - modules are organized behind strong navigation and drill-down paths
2. `Overview must answer what needs attention now`
   - exceptions and operating posture outrank vanity metrics
3. `Cross-branch first, branch drill-down second`
   - the owner should not have to “switch apps” mentally to compare branches
4. `Modern but restrained`
   - beautiful and credible, not flashy
   - motion should improve orientation, not compete with information
5. `Fast-feeling software`
   - theme richness and visual quality must not introduce sluggishness, layout thrash, or heavy rendering

## Information Architecture

`owner-web` should become a tenant command center with six top-level areas.

### 1. Overview

Purpose:

- give the owner immediate cross-branch business posture
- surface prioritized exceptions
- route the user into filtered deeper views quickly

This is the default landing surface.

### 2. Operations

Purpose:

- hold daily branch-operating control

Contains:

- procurement
- receiving
- replenishment
- restock
- returns approvals
- batch and expiry posture
- compliance export posture
- sync and runtime posture

### 3. Commercial

Purpose:

- hold the revenue and customer-control surfaces

Contains:

- promotions
- gift cards
- price tiers
- customer insights
- branch performance
- billing lifecycle posture

### 4. Catalog

Purpose:

- hold product and barcode authority

Contains:

- central catalog products
- branch catalog posture
- barcode management
- barcode print runtime posture

### 5. Workforce

Purpose:

- hold people, device, and operating-governance tools

Contains:

- attendance
- cashier sessions
- shift sessions
- workforce audit
- device claims
- runtime policy

### 6. Settings

Purpose:

- hold tenant structure and system-level posture

Contains:

- tenant summary
- branches
- onboarding residue
- device registration
- later entitlement or environment posture as needed

## Navigation Model

Recommended shell behavior:

- persistent left navigation rail on desktop
- top command strip for:
  - tenant identity
  - branch filter
  - refresh/status posture
  - quick actions
- each top-level area should open to a focused surface, not a raw stack of forms
- branch-sensitive screens should support `all branches` plus branch drill-down without forcing a shell switch

The owner should experience one coherent product shell with contextual drill-down, not a collection of pages with no shared hierarchy.

## Overview Screen Composition

The `Overview` screen is the most important part of the rewrite.

### Primary Goal

The owner must understand, at a glance:

- how trading is going
- which branches need attention
- whether workforce and runtime posture are healthy
- whether inventory, compliance, or commercial issues need intervention

### Recommended Layout

#### A. Command Header

Contains:

- tenant identity
- branch filter
- date/range posture
- runtime/sync health
- primary quick actions

This establishes context before metrics appear.

#### B. Business Posture Band

Compact signal row for:

- sales posture
- return/refund posture
- branch-performance posture
- customer/commercial movement

These should be concise business signals, not oversized “hero cards.”

#### C. Exceptions Board

This is the heart of the screen.

Contains prioritized operational exceptions such as:

- low stock or replenishment exceptions
- pending return approvals
- batch/expiry risk
- compliance/export failures
- sync/runtime degradation
- workforce/session anomalies

Exception rows should visually outrank general summary metrics.

#### D. Branch Performance Panel

Cross-branch comparative view for:

- branch status
- sales pace
- operational issues
- quick drill-down actions

The owner should be able to identify weak branches quickly.

#### E. Workforce/Runtime Panel

Compact supervisory posture for:

- active shifts
- attendance posture
- cashier session posture
- device/runtime issues

#### F. Commercial Pulse Panel

Secondary but visible summary for:

- active promotions
- voucher/gift-card posture
- price-tier or customer signals

### Interaction Model

- clicking an exception opens the relevant deeper surface with appropriate filters
- branch comparison rows/cards open branch drill-down views
- overview is summary-first, action-second, detail-third

## Visual Direction

### Shared Product Language

`owner-web` should feel related to the new `store-desktop` runtime, but not identical.

Shared foundation:

- restrained light surfaces
- strong hierarchy
- calm high-contrast typography
- disciplined accent color usage
- clean motion and transitions

But `owner-web` should feel more supervisory and comparative, not transaction-driven.

### Owner Console Visual Thesis

A disciplined operations console:

- quieter than `store-desktop`
- more analytical
- more summary-oriented
- still visibly modern, fast, and polished

### Visual Rules

- warm-neutral backgrounds
- dark ink text
- blue reserved for navigation and primary actions
- amber/red/green reserved for risk and state
- fewer heavy card outlines, more layout planes
- compact, information-dense metrics
- exception rows visually prioritized over vanity summaries

### Motion Rules

- short, purposeful transitions
- motion used for orientation and focus shifts only
- no blur-heavy or glass-heavy gimmicks
- no long choreographed entrance sequences
- responsiveness takes priority over flourish

## Shared Theme Foundation

This slice must include both `light` and `dark` themes as a real cross-app foundation, not a page-level color toggle.

### Theme Requirements

The theme system should define semantic tokens for:

- surface tiers
- text tiers
- border and divider tiers
- accent tokens
- muted/secondary tokens
- success, warning, danger, and info states
- spacing
- radius
- shadow
- motion
- typography roles

The product should not rely on hard-coded color decisions inside individual screens.

### Adoption Boundary

This slice should:

- implement the token system in `packages/ui`
- support user theme choice with persistence
- support system-default theme behavior
- provide baseline theme plumbing in:
  - `owner-web`
  - `store-desktop`
  - `platform-admin`

`store-mobile` does not need a full redesign in this slice, but the theme contract should be explicit enough for later adoption.

## Shared Design-System Foundation

This slice should introduce or strengthen reusable primitives in `packages/ui`.

Likely additions or upgrades:

- owner console shell
- navigation rail
- command header
- filter strip
- overview signal row
- exception board
- branch comparison panel
- compact detail panel
- theme provider and theme toggle boundary

These should be reusable across later app productization work rather than remaining `owner-web`-specific one-offs.

## Implementation Boundary

This rewrite should preserve current domain logic and backend contracts while replacing the composition model of the UI.

Likely implementation shape:

- refactor [OwnerWorkspace.tsx](/d:/codes/projects/store/apps/owner-web/src/control-plane/OwnerWorkspace.tsx) from a section stack into a routed or stateful command-center shell
- preserve and adapt existing owner data and action hooks in [useOwnerWorkspace.ts](/d:/codes/projects/store/apps/owner-web/src/control-plane/useOwnerWorkspace.ts)
- group existing section components behind focused screens within `Overview`, `Operations`, `Commercial`, `Catalog`, `Workforce`, and `Settings`
- add or upgrade shared theme and layout primitives in [packages/ui/src/index.tsx](/d:/codes/projects/store/packages/ui/src/index.tsx)

The first slice should not attempt to redesign every detailed subview equally. It should establish hierarchy first, then progressively deepen individual areas.

## Testing And Verification

The first owner-web productization slice should be validated at three levels.

### Component / Interaction Tests

- top-level shell navigation
- default `Overview` posture
- branch filter behavior
- exception-board drill-down routing
- theme switching and persistence

### Existing Behavior Preservation

- current owner actions and API payloads continue to work
- procurement, receiving, commercial, workforce, and runtime sections remain reachable and functional
- existing control-plane contracts are preserved through the new shell

### Build Verification

- `@store/owner-web` test
- `@store/owner-web` typecheck
- `@store/owner-web` build
- targeted verification for shared theme plumbing if `store-desktop` and `platform-admin` adopt the new theme provider in this slice

## Success Criteria

This slice is successful when:

- the owner lands in a real multi-branch command center
- `Overview` answers what needs attention right now
- the app feels modern, fast, fluid, and beautiful without becoming ornamental
- light and dark theming exist as a reusable shared system, not a local hack
- the owner surface no longer feels like a long linear tool dump
- the resulting design system foundation is strong enough to guide later `platform-admin` and `store-mobile` productization work

## Risks

### Risk: Cosmetic Modernization Without Hierarchy

If the work only adds nicer spacing and colors, the app will still feel weak.

Mitigation:

- treat this as an information-architecture and shell rewrite first
- visual polish follows hierarchy and routing

### Risk: Theme Work Becomes A Massive Cross-App Refactor

If the theme system is implemented as a full redesign of every app at once, the slice will stall.

Mitigation:

- limit this slice to shared theme tokens and baseline app-shell plumbing
- fully productize `owner-web` first

### Risk: Overview Turns Into Dashboard Wallpaper

If all metrics are treated equally, the command center will feel decorative instead of useful.

Mitigation:

- prioritize exceptions, comparative posture, and drill-down routing over oversized KPI tiles

### Risk: Performance Regressions From Modernization

If the new shell adds unnecessary rendering churn or heavy effects, the app may look better but feel worse.

Mitigation:

- keep motion lightweight
- preserve fast render paths
- avoid over-composed shell patterns that cause avoidable rerenders
