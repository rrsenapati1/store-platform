# Packaging And Distribution Design

## Context

`CP-022` is the first public-release packaging slice for Store Desktop. The packaged runtime now has:

- approved device claim-and-bind,
- packaged runtime auth and local continuity,
- branch-hub local relay and offline sale continuity,
- packaged hardware integration.

What it does not have yet is a release contract. The current Tauri shell still behaves like a local-development app:

- `tauri.conf.json` has `bundle.active = false`,
- there is no updater plugin,
- there is no signed-installer flow,
- the packaged control-plane origin still defaults to `http://127.0.0.1:8000` unless a process-level environment override is present,
- there is no documented Windows release or rollback procedure.

That is not acceptable for public release. `CP-022` must make the packaged runtime distributable, environment-safe, and updateable without widening infrastructure beyond the current repo.

## Chosen Approach

Use a Windows-first packaging contract built around:

1. signed NSIS installer builds,
2. runtime-selected release profiles for `dev`, `staging`, and `prod`,
3. Tauri updater integration using static JSON manifests per channel,
4. explicit release scripts and a Windows deployment runbook.

This keeps the packaged app environment-aware without relying on ad hoc machine environment variables after installation. It also gives the public-release path a stable update mechanism and rollback posture while staying compatible with the current repository and deployment model.

## Scope

Included in `CP-022`:

- Windows packaged installer bundling via Tauri.
- Runtime release-profile loading for packaged builds.
- Distinct `dev`, `staging`, and `prod` packaged profiles.
- Updater plugin integration with runtime-configured endpoint and public key.
- Static updater-manifest generation from signed release artifacts.
- Packaged-runtime shell and UI posture for release environment and updater health.
- Release build scripts and publish-manifest script.
- Windows packaging and rollback documentation.

Out of scope for this slice:

- macOS or Linux distribution.
- Full CI or hosted release automation.
- Code-signing certificate procurement or notarization outside repo documentation.
- Production infrastructure for artifact hosting.
- Forced background auto-update installation.

## Architecture

### 1. Release Profile Boundary

The packaged runtime gains an explicit release profile. A release profile defines:

- release environment: `dev`, `staging`, or `prod`,
- control-plane base URL,
- updater endpoint URL,
- updater public key,
- whether local control-plane override is allowed.

The app must stop assuming localhost in packaged release builds. Instead, the build pipeline selects a release profile and the native shell loads that profile at runtime from packaged resources.

For development shells:

- `tauri dev` and local testing may still resolve localhost defaults,
- process-level overrides remain allowed where explicitly enabled by the selected profile.

For signed release installers:

- the packaged resource is the source of truth,
- environment drift on the target machine does not silently redirect production traffic.

### 2. Native Updater Boundary

The packaged runtime integrates Tauri’s updater plugin with runtime configuration:

- updater endpoint comes from the selected release profile,
- updater public key comes from the selected release profile,
- update checks use channel-appropriate static JSON manifests,
- the shell exposes update posture to the React app through explicit commands.

This keeps updater configuration aligned with the chosen release environment and avoids hard-coding one endpoint for every build.

Updater behavior for this slice is intentionally explicit:

- the runtime can check for updates,
- it can download and install a discovered update,
- it exposes actionable status and errors,
- rollback stays operational through publishing an older signed version and allowing downgrade checks when the release policy explicitly permits it.

### 3. Installer And Artifact Contract

Windows distribution will use NSIS as the first-class installer target. The Tauri bundle configuration should:

- enable bundling,
- generate updater artifacts and signatures,
- emit a versioned setup executable,
- preserve the normal Tauri bundle layout under `src-tauri/target/release/bundle/`.

Release scripts will wrap `tauri build` so the operator does not have to remember low-level environment variables or output paths. The script should:

- select the release profile,
- validate signing-key inputs,
- run the Tauri build,
- stage the produced installer and signature,
- generate the channel manifest JSON consumed by the updater.

### 4. Static Channel Manifests

Each release channel publishes a static updater manifest. The manifest includes:

- version,
- notes,
- publication date,
- platform entry for `windows-x86_64`,
- installer URL,
- generated signature content.

The repo will include a manifest-generation script so release artifacts can be staged consistently for `dev`, `staging`, and `prod`. This avoids inventing a dynamic update service inside `CP-022`.

### 5. Runtime Shell And UI Posture

The packaged runtime shell should expose release posture alongside the existing shell identity:

- release environment,
- effective control-plane base URL,
- updater endpoint,
- whether updater public key is configured,
- last update check result,
- pending update version if present,
- last updater error if present.

The React desktop app should render that posture in a dedicated release or updater section with actions to:

- check for updates,
- install a pending update when one is available.

Browser runtime continues to show neutral or unavailable updater posture. Updater actions are packaged-runtime only.

## Error Handling

Packaging and updater flows must fail closed and visibly:

- missing release profile in a packaged build:
  - shell reports `invalid_profile`,
  - packaged runtime does not silently fall back to localhost.
- missing updater public key or updater endpoint:
  - shell reports update configuration as unavailable,
  - update actions remain disabled.
- missing signing private key during release build:
  - release script fails before invoking Tauri build.
- malformed manifest generation inputs:
  - publish script fails before writing channel manifest output.
- update check transport failure:
  - runtime records bounded error text,
  - current session remains usable.

## Testing Strategy

Native shell:

- release-profile loading and override rules,
- packaged shell status reporting for release posture,
- updater command behavior when configuration is missing or present.

Desktop app:

- runtime shell adapter parsing new release fields,
- updater section rendering,
- check-for-update and install-action posture in packaged mode,
- neutral posture in browser mode.

Release tooling:

- manifest-generation script produces valid static JSON from a signed installer and `.sig`,
- release build script validates required inputs before invoking Tauri.

Verification:

- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
- tooling smoke checks using `--help` or targeted script fixtures

## Rollout

This slice establishes the first real Store Desktop distribution contract:

- signed Windows installer output,
- profile-driven environment separation,
- updater-ready packaged runtime,
- documented publish and rollback workflow.

If hosted automation is added later, it can consume the same release profile and static-manifest contract without rewriting the packaged runtime itself.
