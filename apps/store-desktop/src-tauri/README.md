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
- `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml runtime_cache -- --nocapture`

## Runtime Home

- `STORE_RUNTIME_HOME`
  - optional override for the native runtime-cache directory
  - if unset, the shell uses `%LOCALAPPDATA%\\StoreRuntime` on Windows and falls back to a repo-local `.store-runtime/` directory otherwise

## Cache Contract

- the SQLite cache stores only the `store.runtime-cache.v1` snapshot
- the snapshot must remain `CONTROL_PLANE_ONLY`
- malformed or incompatible snapshots are deleted instead of being treated as authority
- the web shell can still fall back to browser storage, but the packaged shell prefers native SQLite through Tauri commands
