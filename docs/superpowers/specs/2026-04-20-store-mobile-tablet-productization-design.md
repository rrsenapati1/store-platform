# Store Mobile Tablet Productization Design

Date: 2026-04-20
Owner: Codex
Status: Approved by standing user instruction to continue without further review

## Goal

Turn the existing `inventory_tablet_spoke` runtime into a product-quality backroom operations surface that matches the newer handheld product language.

When this slice is complete:

- the tablet runtime should feel like an inventory command surface, not a generic left-nav wrapper
- backroom operators should land in an overview-first workflow with clear branch posture
- receiving, stock count, restock, expiry, scan, and runtime health should remain reachable through deliberate drill-down
- the tablet should share the same light/dark design system and auth/runtime posture as the rest of the suite

## Problem

`InventoryTabletShell.kt` currently exposes a static list of operation buttons and reuses `MobileOperationsContent` as a raw outlet. That preserves capability, but it does not create a tablet-specific product:

- there is no default overview or branch posture
- every module is presented with equal weight
- scan is only another section, not a contextual tool
- runtime and session state are available, but not integrated into a modern tablet workflow

This is the same structural weakness the handheld shell had before productization.

## Chosen Model

The tablet should become a `backroom operations console`, not a larger handheld.

Top-level tablet flow:

- `Overview`
- `Receiving`
- `Count`
- `Restock`
- `Expiry`
- `Scan`
- `Runtime`

Key posture:

- `Overview` is the default landing screen
- the overview summarizes live branch inventory work using existing operation state
- operators drill into focused task screens from the overview or left rail
- scan remains available, but as a tool for contextual lookup rather than the home screen

## Scope

### In Scope

- tablet-specific destination model and default overview
- tablet overview model derived from existing operation state
- productized tablet shell with stronger navigation, header, and branch context
- updated tablet scan, task, and runtime composition so they feel consistent with the suite
- dedicated tests for tablet routing and overview derivation
- deferred backlog updates in docs once the slice is complete

### Out Of Scope

- backend contract changes
- new inventory workflows beyond the existing receiving/count/restock/expiry authority
- secure-storage hardening
- cross-app final parity polish outside necessary shared mobile adjustments

## Tablet Information Architecture

### 1. Overview

Default landing surface.

Shows:

- branch/runtime context
- receiving posture
- count posture
- restock pressure
- expiry risk
- quick drill-down actions

This is the control surface that tells the operator what needs attention first.

### 2. Receiving

Focused receiving execution view for approved PO work and reviewed receipt submission.

### 3. Count

Focused blind-count and review posture.

### 4. Restock

Focused replenishment and backroom-to-shelf task posture.

### 5. Expiry

Focused lot review and write-off approval posture.

### 6. Scan

A utility section for branch lookup and scanner diagnostics, not the default landing screen.

### 7. Runtime

Session, device, scanner, and hub posture with sign-out and unpair controls.

## UI Direction

The tablet should look like a calm, modern operations console:

- strong sectional layout instead of button lists
- large but disciplined touch targets
- compact operational metrics
- quiet surfaces with high contrast
- clear top context strip and left navigation rail

It should feel related to the rest of the suite, but optimized for landscape inventory use.

## Testing

Add failing-first coverage for:

- tablet destination semantics
- overview-model derivation from receiving/count/restock/expiry/runtime state
- shell-mode default destination behavior
- runtime-context expectations for tablet profiles

## Deferred Follow-Ups

This slice should not silently absorb the rest of the deferred backlog. The following remain separate release-critical work after tablet productization:

- mobile secure-storage hardening review
- final mobile empty/error/loading-state polish
- final cross-app visual parity audit
