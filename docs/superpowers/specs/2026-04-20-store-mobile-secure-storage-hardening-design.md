# Store Mobile Secure Storage Hardening Design

Date: 2026-04-20
Owner: Codex
Status: Approved by standing user instruction to continue without further review

## Goal

Harden persisted mobile pairing and runtime session state so the public-release mobile runtime no longer stores them in plain app preferences without explicit posture visibility.

## Problem

`store-mobile` currently persists hub manifest, paired device, and runtime session state through plain `SharedPreferences`.

That is acceptable for local development, but not for a serious public release because:

- session tokens and device-binding context are persisted unencrypted
- there is no runtime visibility into whether secure storage is actually active
- fallback behavior is implicit instead of explicit

## Chosen Model

- use encrypted shared preferences as the default persistence backend on Android
- if encrypted storage cannot be created, fall back to plain preferences only as a bounded recovery path
- surface the active storage posture in the runtime UI so operators and testers can detect insecure fallback immediately
- keep repository contracts intact; this is a storage-factory and posture slice, not a repository redesign

## Scope

### In Scope

- encrypted Android key-value-store factory
- explicit storage posture model
- runtime status visibility for encrypted vs fallback storage
- tests for preference-selection behavior and runtime posture rendering

### Out Of Scope

- backend auth changes
- biometric unlock
- broader MDM/device-attestation work

## Testing

Add failing-first coverage for:

- encrypted store selection when available
- fallback posture when encrypted initialization fails
- runtime status text reflecting storage posture
