# Store Docs Index

Updated: 2026-04-13

## Start Here

Read the smallest useful set.

### Always Read

1. `PROJECT_CONTEXT.md`
2. `DOCS_INDEX.md`
3. `context/MODULE_MAP.md`

### Then Choose by Task

- Architecture, data model, auth, tenancy, or control-plane changes:
  - `STORE_CANONICAL_BLUEPRINT.md`
- API route or payload change:
  - `API_CONTRACT_MATRIX.md`
- Reset program status or future work:
  - `TASK_LEDGER.md`
- Recent implementation history:
  - `WORKLOG.md`
- Handoff between contributors:
  - `HANDOFF_TEMPLATE.md`
- Local setup and verification:
  - `runbooks/dev-workflow.md`
- Approved reset design:
  - `superpowers/specs/2026-04-13-control-plane-reset-m1-design.md`

## Canonical Root Docs

Root `docs/` contains canonical docs only:

- `DOCS_INDEX.md`
- `PROJECT_CONTEXT.md`
- `STORE_CANONICAL_BLUEPRINT.md`
- `API_CONTRACT_MATRIX.md`
- `TASK_LEDGER.md`
- `WORKLOG.md`
- `HANDOFF_TEMPLATE.md`

## Supporting Docs

- `context/`
  - codebase module map and ownership boundaries
- `runbooks/`
  - local workflow and operational commands
- `superpowers/specs/`
  - approved architecture and milestone design specs

## Governance Rules

1. All planning, architecture, implementation, and handoff docs live under `docs/`.
2. Root-doc sprawl is not allowed; supporting material belongs under `context/`, `runbooks/`, or `superpowers/specs/`.
3. Any architecture or product-direction change must update `STORE_CANONICAL_BLUEPRINT.md` and `PROJECT_CONTEXT.md` in the same patch.
4. Any API contract change must update `API_CONTRACT_MATRIX.md` in the same patch.
5. Any significant code change must update at least one of:
   - `WORKLOG.md`
   - `TASK_LEDGER.md`
   - `PROJECT_CONTEXT.md`
   - `API_CONTRACT_MATRIX.md`
6. The task ledger is the authoritative backlog for planned reset milestones.
