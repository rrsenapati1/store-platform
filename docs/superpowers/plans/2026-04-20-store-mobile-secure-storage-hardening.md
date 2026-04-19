# Store Mobile Secure Storage Hardening Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace plain mobile pairing/session persistence with encrypted storage by default and make any fallback posture explicit in the runtime UI.

**Architecture:** Add a storage bootstrap layer that selects encrypted preferences when available and a bounded plain-preferences fallback when not. Keep pairing/session repositories unchanged by continuing to consume the `StoreMobileKeyValueStore` interface, and thread storage posture into runtime status rendering.

**Tech Stack:** Kotlin, Android SharedPreferences, AndroidX Security Crypto, existing mobile runtime repositories, Android unit tests.

---

### Task 1: Add storage posture and encrypted/fallback bootstrap selection

**Files:**
- Create: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobileSecureStorage.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/runtime/StoreMobilePreferences.kt`
- Modify: `apps/store-mobile/app/build.gradle.kts`
- Create: `apps/store-mobile/app/src/test/java/com/store/mobile/runtime/StoreMobileSecureStorageTest.kt`

- [ ] Write failing tests for encrypted-selection and fallback posture.
- [ ] Run the focused storage tests and confirm they fail.
- [ ] Implement the secure-storage bootstrap and dependency wiring.
- [ ] Re-run the focused storage tests and confirm they pass.
- [ ] Commit.

### Task 2: Surface storage posture in the runtime shell and docs

**Files:**
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/StoreMobileApp.kt`
- Modify: `apps/store-mobile/app/src/main/java/com/store/mobile/ui/runtime/RuntimeStatusScreen.kt`
- Modify: `apps/store-mobile/app/src/test/java/com/store/mobile/ui/runtime/RuntimeStatusScreenTest.kt`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] Write failing runtime-status tests for storage posture visibility.
- [ ] Run the focused runtime tests and confirm they fail.
- [ ] Thread storage posture through the app root and runtime screen.
- [ ] Re-run the focused tests and confirm they pass.
- [ ] Run full mobile verification, then commit and merge.
