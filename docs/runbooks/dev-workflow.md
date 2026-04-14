# Store Development Workflow

Updated: 2026-04-13

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

## Control-Plane Local Run

From `services/control-plane-api/`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose -f compose.yaml up -d postgres
alembic upgrade head
uvicorn store_control_plane.main:create_app --factory --reload --app-dir .
```

Production and shared development should use Korsenex `jwks` mode.

`stub` mode is only for tests and isolated local fallback.
