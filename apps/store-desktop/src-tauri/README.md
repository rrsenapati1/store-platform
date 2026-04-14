# Store Desktop Native Shell

This package is the first native packaged-runtime foundation for `apps/store-desktop/`.

## Scope

- Tauri shell for the existing React desktop UI
- native SQLite-backed runtime-cache bridge
- explicit cache-only persistence boundary
- no backend authority transfer away from the control plane

## Commands

- `npm run tauri:dev --workspace @store/store-desktop`
- `npm run tauri:check --workspace @store/store-desktop`
- `npm run tauri:build:release --workspace @store/store-desktop -- --profile staging`
- `npm run tauri:manifest --workspace @store/store-desktop -- --version 0.1.0 --url https://updates.example/store-runtime-setup.exe --signature-file .\src-tauri\target\release\bundle\nsis\store-runtime-setup.exe.sig --output .\dist\latest.json`
- `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml runtime_cache -- --nocapture`

## Runtime Home

- `STORE_RUNTIME_HOME`
  - optional override for the native runtime-cache directory
  - if unset, the shell uses `%LOCALAPPDATA%\\StoreRuntime` on Windows and falls back to a repo-local `.store-runtime/` directory otherwise

## Release Profiles

- `STORE_DESKTOP_RELEASE_PROFILE`
  - build-time profile selector for `dev`, `staging`, or `prod`
- `STORE_DESKTOP_RELEASE_CONTROL_PLANE_BASE_URL`
  - optional build-time override for the packaged control-plane origin
- `STORE_DESKTOP_RELEASE_UPDATER_ENDPOINT`
  - optional build-time override for the packaged updater feed
- `STORE_DESKTOP_RELEASE_UPDATER_PUBLIC_KEY`
  - optional build-time override for the updater verification key

Packaged release builds should use the bundled profile as the environment source of truth. Local machine overrides are intended only for explicitly development-safe profiles.

## Cache Contract

- the SQLite cache stores only the `store.runtime-cache.v1` snapshot
- the snapshot must remain `CONTROL_PLANE_ONLY`
- malformed or incompatible snapshots are deleted instead of being treated as authority
- the web shell can still fall back to browser storage, but the packaged shell prefers native SQLite through Tauri commands

## Packaging Contract

- Windows-first NSIS bundle output is enabled in `tauri.conf.json`
- updater artifacts are signed through Tauri’s updater key flow
- the packaged shell now exposes release environment and updater posture through the native shell bridge
- full packaging and rollback steps live in [docs/runbooks/store-desktop-packaging-distribution.md](../../../docs/runbooks/store-desktop-packaging-distribution.md)
