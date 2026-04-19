# Store Development Workflow

Updated: 2026-04-19

## Current Verification Commands

From repo root:

```powershell
npm run test
npm run build
npm run typecheck
python -m pytest services/api/tests -q
python -m pytest services/control-plane-api/tests -q
```

For the new control plane, prefer the runbook-grade verifier in [control-plane-verification.md](./control-plane-verification.md) instead of assembling those commands by hand.
For the legacy shutdown boundary, use [legacy-authority-cutover.md](./legacy-authority-cutover.md) instead of flipping write modes ad hoc.

## Milestone 1 Expectations

During the control-plane reset:

1. Update docs first when architecture or contracts change.
2. Keep the new control-plane service side-by-side with the legacy retail API.
3. Do not mix domain migration into Milestone 1 onboarding work.
4. Keep backend entrypoints thin and modular.

## Working Rule

If a code change alters onboarding, auth, tenancy, branch setup, or memberships:

- update `docs/PROJECT_CONTEXT.md`
- update `docs/STORE_CANONICAL_BLUEPRINT.md` if the architecture changed
- update `docs/API_CONTRACT_MATRIX.md` if routes or payloads changed
- update `docs/WORKLOG.md`

## Milestone 1 Immediate Build Target

The next implementation target is:

- `services/control-plane-api/`
- `apps/platform-admin/` onboarding flow
- `apps/owner-web/` onboarding flow

The legacy retail API remains in place until later milestones.

## Local Infra

Required for the real V2 app surfaces:

- Postgres only
- no Redis for this repo's normal local app workflow
- no extra containers beyond Postgres for day-to-day frontend and control-plane development
- compose file: `services/control-plane-api/compose.yaml`
- local Postgres container: `store-control-plane-postgres`
- local Postgres URL: `postgresql://postgres:postgres@127.0.0.1:54321/store_control_plane`

Optional local extras:

- Android emulator or physical Android device for `apps/store-mobile`
- Tauri desktop shell if you want the packaged/native `store-desktop` flow instead of the browser shell
- object storage credentials only for backup, release-evidence, and retention workflows

## Control-Plane Local Run

From `services/control-plane-api/`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose -f compose.yaml up -d postgres
alembic upgrade head
uvicorn store_control_plane.main:create_app --factory --reload --host 127.0.0.1 --port 18000 --app-dir .
```

Recommended local API URL:

- [http://127.0.0.1:18000](http://127.0.0.1:18000)

Run the operations worker in a second terminal from repo root:

```powershell
python services/control-plane-api/scripts/run_operations_worker.py
```

Seed the local demo tenant, branch, cashier, device, and product from repo root:

```powershell
npm run dev:seed-local-demo
```

## App Startup Commands

From repo root:

Platform Admin:

```powershell
npm run dev:platform-admin
```

- URL: [http://127.0.0.1:15174](http://127.0.0.1:15174)
- Production-style sign-in requires `VITE_KORSENEX_AUTHORIZE_URL` in the app environment
- Seeded local bootstrap:
  [http://127.0.0.1:15174/#stub_sub=platform-1&stub_email=admin@store.local&stub_name=Platform%20Admin](http://127.0.0.1:15174/#stub_sub=platform-1&stub_email=admin@store.local&stub_name=Platform%20Admin)

Owner Web:

```powershell
npm run dev:owner-web
```

- URL: [http://127.0.0.1:15173](http://127.0.0.1:15173)
- Production-style sign-in requires `VITE_KORSENEX_AUTHORIZE_URL` in the app environment
- Seeded local bootstrap:
  [http://127.0.0.1:15173/#stub_sub=owner-1&stub_email=owner@acme.local&stub_name=Acme%20Owner](http://127.0.0.1:15173/#stub_sub=owner-1&stub_email=owner@acme.local&stub_name=Acme%20Owner)

Store Desktop browser shell:

```powershell
npm run dev:store-desktop
```

- URL: [http://127.0.0.1:15172](http://127.0.0.1:15172)
- Seeded local bootstrap:
  [http://127.0.0.1:15172/#stub_sub=cashier-1&stub_email=cashier@acme.local&stub_name=Counter%20Cashier](http://127.0.0.1:15172/#stub_sub=cashier-1&stub_email=cashier@acme.local&stub_name=Counter%20Cashier)
- Browser shell is for local UI verification only; production operator access belongs to the packaged desktop activation flow

Store Desktop native Tauri shell:

```powershell
npm run dev:store-desktop:tauri
```

Store Mobile:

```powershell
cd apps/store-mobile
.\gradlew.bat installDebug
```

`store-mobile` is Android-only. You need either:

- a running Android emulator, or
- a connected physical Android device with USB debugging enabled

## Auth And Session Notes

Web control surfaces:

- `owner-web` and `platform-admin` now expect Korsenex redirect-style sign-in in normal environments
- set `VITE_KORSENEX_AUTHORIZE_URL` to the web sign-in entry URL for the environment you are testing
- the `#stub_*` bootstrap links above remain development-only helpers; production entry should not rely on pasted tokens or hash bootstrap

Store Desktop:

- packaged desktop remains device-bound
- first-run operator access is `Activate this terminal`
- subsequent launches are `Unlock this terminal` when local PIN posture is present
- explicit runtime sign-out clears the live session but keeps approved-device posture so the terminal can be unlocked again instead of fully reactivated
- revoked or expired runtime sessions now surface explicit recovery posture instead of generic bootstrap errors

Store Mobile:

- pairing and runtime session state now persist locally on device restart
- `Sign out` clears the live runtime session while keeping the paired device record
- `Unpair` clears both pairing and runtime session state
- expired sessions fall back to a recovery posture that requires a fresh activation or explicit unpair

## Notes

- The web and browser-shell dev servers proxy `/v1/*` to `http://127.0.0.1:18000` by default.
- The `#stub_*` bootstrap values are consumed by the app on load and then removed from the browser URL.
- For `store-desktop`, the seeded bootstrap signs in the cashier identity. Attendance and cashier opening still follow the real runtime workflow inside the app.
- For `store-mobile`, runtime session persistence is stored locally on device for development/runtime resume. Treat emulator/device state as persistent until you explicitly sign out or uninstall the app.

Production and shared development should use Korsenex `jwks` mode.

`stub` mode is only for tests and isolated local fallback.
