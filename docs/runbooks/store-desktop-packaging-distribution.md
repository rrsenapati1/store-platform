# Store Desktop Packaging And Distribution

## Scope

This runbook covers the first Windows packaging contract for `apps/store-desktop/`:

- explicit release profiles,
- signed Tauri updater artifacts,
- NSIS installer output,
- static update-manifest publication,
- rollback posture.

This runbook does not cover hosted CI or CDN automation. It assumes the operator is building on Windows with access to the required signing inputs.

## Release Profiles

The packaged desktop build reads a bundled release profile selected at build time with:

- `STORE_DESKTOP_RELEASE_PROFILE=dev`
- `STORE_DESKTOP_RELEASE_PROFILE=staging`
- `STORE_DESKTOP_RELEASE_PROFILE=prod`

Optional build-time overrides:

- `STORE_DESKTOP_RELEASE_CONTROL_PLANE_BASE_URL`
- `STORE_DESKTOP_RELEASE_UPDATER_ENDPOINT`
- `STORE_DESKTOP_RELEASE_UPDATER_PUBLIC_KEY`

Public installers should not rely on target-machine environment overrides after installation. The bundled profile is the release truth.

## Required Signing Inputs

Tauri updater artifacts require:

- `TAURI_SIGNING_PRIVATE_KEY`
- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` (optional)

Without these values, release builds must fail before `tauri build`.

## Build A Release Installer

From the repo root:

```powershell
$env:TAURI_SIGNING_PRIVATE_KEY = "C:\secure\store-desktop.key"
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = ""
$env:STORE_DESKTOP_RELEASE_UPDATER_PUBLIC_KEY = "minisign-public-key"
node scripts/build-store-desktop-release.mjs --profile staging
```

The wrapper runs:

- `npm run tauri:build --workspace @store/store-desktop -- --bundles nsis`

Artifacts land under:

- `apps/store-desktop/src-tauri/target/release/bundle/nsis/`

Important outputs:

- `Store Runtime_<version>_x64-setup.exe`
- matching `.sig` file

## Generate The Static Update Manifest

After the installer is uploaded to the chosen channel location, generate the manifest consumed by the packaged updater:

```powershell
node scripts/generate-store-desktop-update-manifest.mjs `
  --version 0.1.0 `
  --url https://updates.staging.store.korsenex.local/store-runtime/0.1.0/Store%20Runtime_0.1.0_x64-setup.exe `
  --signature-file apps/store-desktop/src-tauri/target/release/bundle/nsis/Store Runtime_0.1.0_x64-setup.exe.sig `
  --output .\dist\store-runtime\staging\latest.json `
  --notes-file .\release-notes\store-runtime-0.1.0.md
```

Publish `latest.json` to the same channel origin configured in the release profile.

For `CP-024`, keep staging and prod artifacts separated in managed object storage. A safe starting contract is:

- `staging`
  - bucket or prefix: `store-platform-staging/desktop/staging/`
- `prod`
  - bucket or prefix: `store-platform-prod/desktop/prod/`

Do not publish both channels into the same prefix.

## Operator Validation

Before publishing a channel update:

1. Install the previous packaged version.
2. Confirm the packaged shell shows the expected release environment and control-plane origin.
3. Confirm the matching deployed control plane passes `verify_deployed_control_plane.py`.
4. Use the `Release channel` section to check for updates.
5. Confirm the runtime reports the pending version from the target channel.
6. Install the update and verify the app restarts on the new version.

## Rollback Posture

Rollback is channel-based:

1. Re-publish the previously trusted installer and matching `.sig`.
2. Re-point the channel manifest `latest.json` to that trusted version.
3. If the bundled release profile disallows downgrade updates, treat rollback as a manual reinstall for already-upgraded desktops.
4. Record the rollback reason and affected version in release notes.

For the first public-release slice, rollback is operationally supported through installer and manifest replacement. Fully automated downgrade orchestration is out of scope.
