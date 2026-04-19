# Platform Admin Productization Foundation Design

Date: 2026-04-19
Owner: Codex
Status: Drafted after design approval

## Goal

Turn `platform-admin` from a flat administrative workspace into a product-quality platform control tower.

This slice is not about adding new backend authority. It is about giving the platform surface a real operational hierarchy, stronger cross-app visual language, and a credible enterprise control posture that matches the rest of the app suite.

When this slice is complete:

- platform admins should land in a control tower rather than a tenant-bootstrap form
- release, incident, security, backup, and environment posture should become first-class product surfaces
- tenant and commercial actions should remain available, but should become secondary to platform operations
- the app should share the modern `light` and `dark` theme system already established across the suite

## Problem Statement

The current `platform-admin` surface is functionally useful but product-wise weak.

Today:

- [PlatformAdminWorkspace.tsx](/d:/codes/projects/store/apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx) is a linear stack of sections
- session bootstrap, tenant creation, owner invites, billing plans, tenant suspension, and observability all compete in one flat screen
- the default posture does not answer the most important platform-admin question: “is the platform safe and stable right now?”
- release-readiness, hardening, and environment-governance capabilities mostly live in scripts and docs rather than a coherent product view
- the app does not yet read as the top operational surface in the suite

This creates the same failure mode seen elsewhere before productization: the app works, but it does not feel like a serious operational control product.

## Chosen Model

The accepted model is:

- `platform-admin` becomes a `platform control tower`
- the first pass optimizes for `platform operations oversight first`
- the app is shaped as a cross-tenant, cross-environment surface rather than a single-environment admin page
- the default landing posture is `incident and release posture first`
- release and hardening status becomes visible directly in the UI as a read-only control-tower layer
- tenant and commercial administration remain present but become subordinate to platform health and operator attention

This is a `control-tower platform console`, not a cosmetic cleanup of the existing form stack.

## Scope

### In Scope

- product-quality rewrite of `platform-admin` around a control-tower shell
- new platform information architecture with:
  - `Overview`
  - `Release`
  - `Operations`
  - `Tenants`
  - `Commercial`
  - `Settings`
- `Overview` as the default landing surface
- platform posture centered on:
  - release-readiness
  - security and hardening
  - queue/runtime degradation
  - backup and restore posture
  - environment drift and TLS posture
- reuse of the shared `light` / `dark` theme system from `packages/ui`
- preservation of current tenant creation, owner invite, billing-plan, suspension, and observability actions wherever possible

### Out Of Scope

- large backend redesign solely for UI shape
- rewriting release and hardening tooling itself
- advanced visualization or charting beyond what improves operator decisions
- deep redesign of every platform-admin subsection in the first pass
- auth model redesign
- mobile-specific platform-admin adaptation

## Product Principles

The rewrite should follow these principles:

1. `Platform health first`
   - the default view should answer whether the platform is healthy, safe, and releaseable
2. `Operator action over form inventory`
   - the product should guide what needs attention now rather than dumping independent admin controls
3. `Status hierarchy matters`
   - failing or degraded posture should visually outrank routine metrics
4. `Technical credibility without clutter`
   - high information density, clear hierarchy, minimal decorative noise
5. `Suite consistency`
   - platform-admin should share the same modern design language as the rest of the app suite while keeping its own personality

## Information Architecture

`platform-admin` should become a control-tower shell with six top-level areas.

### 1. Overview

Purpose:

- answer “is the platform safe and stable right now?”
- summarize release, incident, security, backup, and environment posture
- route operators into deeper workflows quickly

### 2. Release

Purpose:

- make release readiness, certification, rollback, evidence, and launch posture visible and inspectable

Contains:

- release candidate posture
- evidence / certification summaries
- restore-drill status
- rollback verification posture
- retained evidence posture
- launch-readiness summary

### 3. Operations

Purpose:

- expose live platform operations oversight

Contains:

- observability summary
- dead-letter / retryable operations posture
- degraded runtime branches
- backup freshness
- alert-verification posture
- environment drift
- TLS posture

### 4. Tenants

Purpose:

- govern tenant lifecycle and onboarding

Contains:

- tenant list
- owner binding and invite flow
- tenant status and suspension posture
- tenant drill-down and exception routing

### 5. Commercial

Purpose:

- manage platform-level commercial policy and billing-plan governance

Contains:

- billing-plan catalog
- default-plan posture
- plan creation and lifecycle actions

### 6. Settings

Purpose:

- expose platform and operator context

Contains:

- current environment identity
- public base URL / platform contract posture
- operator session posture
- later operator preferences and access posture

## Overview Screen Composition

The `Overview` screen should be the default control-tower landing surface.

### Primary Goal

A platform admin should understand at a glance:

- whether the current release is safe
- whether operations are degrading
- whether security / backup / drift posture needs action
- whether any tenant exceptions require intervention

### Layout

#### A. Command Header

Top strip with:

- environment
- release version
- overall health state
- last refresh posture
- quick actions like refresh or inspect release

#### B. Platform Posture Band

Compact summary row for:

- release readiness
- security posture
- operational alert posture
- backup / restore posture

These should read as status-first signals, not giant dashboard cards.

#### C. Critical Exceptions Board

The most important section.

Prioritized items like:

- failed release gates
- dead-letter jobs
- degraded runtime branches
- environment drift
- TLS risk
- stale backup or failed restore drill

This is where operator attention goes first.

#### D. Tenant Exceptions Panel

Cross-tenant exceptions such as:

- suspended or grace-risk tenants
- onboarding-stuck tenants
- commercial lifecycle anomalies
- tenant drill-down links

#### E. Runtime And Operations Panel

Read-only but actionable summary of:

- queue posture
- branch degradation
- sync/runtime health
- recent failures

#### F. Release Evidence Panel

Compact summary of:

- latest certification state
- retained evidence availability
- rollback posture
- launch-readiness / sign-off status

## Visual Direction

### Visual Thesis

`platform-admin` should feel modern, fast, technical, and calm.

It should share the suite-wide token foundation while presenting the most operationally precise surface in the system.

### Shared Design Language

The app should reuse the shared semantic token system established in `packages/ui`:

- light and dark themes
- layered surfaces
- text tiers
- border and muted roles
- accent and destructive roles
- status semantics
- motion tokens
- spacing, radius, and shadow tokens

### Platform-Specific Personality

Compared with the other apps:

- `store-desktop` is action-heavy and transaction-driven
- `owner-web` is supervisory and business-oriented
- `platform-admin` should be the most technical and status-driven

That means:

- tighter signal density
- stronger operational badges
- cleaner, more precise sectional layout
- less warmth than owner-web
- strong contrast around degraded or failing posture

### System Rules

- every screen should have one primary operator purpose
- exception rows should outrank vanity metrics
- motion should clarify navigation and state changes only
- avoid chart-heavy clutter, oversized cards, and decorative effects that hurt speed
- preserve a fast-feeling UI with crisp interactions and low friction

## Implementation Boundary

This slice should preserve existing platform-admin domain actions and backend contracts while replacing the UI composition model.

Likely implementation shape:

- refactor [PlatformAdminWorkspace.tsx](/d:/codes/projects/store/apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx) into a shell plus focused surfaces
- preserve [usePlatformAdminWorkspace.ts](/d:/codes/projects/store/apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts) as the primary state boundary where practical
- introduce platform-admin shell primitives on top of the shared UI token system in [packages/ui/src/index.tsx](/d:/codes/projects/store/packages/ui/src/index.tsx)
- move from section-stack rendering to selected-surface composition
- update existing tests to target operator flows and surface hierarchy rather than legacy stack order

The first slice should not attempt to redesign every detailed platform-admin subview at once.

## Deferred But Release-Critical Product Backlog

These items are intentionally deferred from the first `platform-admin` productization slice, but they should remain visible as part of the pre-public-release product backlog across the suite.

### Platform Admin

- deeper redesign of `Release`, `Operations`, `Tenants`, and `Commercial` subviews beyond the shell and overview layer
- richer evidence and drill-down inspection flows for release-readiness and hardening posture
- operator-grade filtering and drill-down for tenant exceptions and incidents

### Owner Web

- deeper redesign of `Operations`, `Commercial`, `Catalog`, and `Workforce` detail views after the new shell
- stronger branch-drill-down and exception-routing UX
- denser but clearer comparative reporting surfaces

### Store Desktop

- parked / held carts
- receipt history and recovery UX
- deeper redesign of secondary operations screens behind the new runtime shell
- polished production-grade entry and device activation posture beyond local developer bootstrap

### Store Mobile

- full adoption of the shared theme system and modern product language
- productization pass aligned to its handheld operational role

### Cross-App

- polished production auth/session entry flows across all apps
- finalized environment contract and runtime configuration posture for each app shell
- final consistency pass on light/dark theme behavior, motion, typography, and performance across the suite

These are not blockers for this specific slice, but they should be treated as tracked productization work before public launch.

## Testing And Verification

The first platform-admin productization slice should be validated at three levels.

### Component / Interaction Tests

- overview default landing posture
- critical exception rendering
- navigation between top-level platform surfaces
- tenant and billing-plan actions still functioning under the new shell
- theme mode behavior

### Existing Behavior Preservation

- tenant creation still works
- owner invite still works
- billing-plan creation still works
- tenant suspension and reactivation still work
- observability summary still loads correctly

### Build Verification

- `@store/platform-admin` test
- `@store/platform-admin` typecheck
- `@store/platform-admin` build
- targeted shared `packages/ui` verification if shared primitives are added

## Success Criteria

This slice is successful when:

- platform-admin feels like a real control tower rather than a stacked admin worksheet
- release and incident posture become first-class product surfaces
- tenant and commercial actions remain available but properly subordinate
- the app adopts the suite-wide modern light/dark visual language cleanly
- the deferred product backlog remains explicitly documented for pre-public-release completion

## Risks

### Risk: Platform Control Tower Without Enough Real Signal

If the UI adds hierarchy but still surfaces shallow or duplicated posture, the product will look better without becoming more useful.

Mitigation:

- center the overview on operator implications
- emphasize failing, degraded, or action-worthy posture over neutral statistics

### Risk: Section Relabeling Instead Of Productization

If the implementation simply renames or tabs the existing sections without changing surface hierarchy, the result will still feel weak.

Mitigation:

- treat this as a shell and workflow rewrite first
- make `Overview` genuinely summary-first and exception-driven

### Risk: Overloading The First Slice

Trying to redesign every sub-surface in `platform-admin` immediately will slow delivery and weaken the first meaningful improvement.

Mitigation:

- prioritize shell, overview, and product hierarchy first
- keep detailed sub-surface redesign as tracked follow-on work
