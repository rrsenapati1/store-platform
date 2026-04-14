# V2 Launch Program Rewrite Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the Store ledger and canonical docs so the repo targets a broader `V2 launch` program instead of the smaller public-release endgame.

**Architecture:** This is a documentation-governance change, not a product-code change. The work should keep completed `CP-*` history intact, reinterpret `CP-028` as the transition point, add a new `V2-*` task family, and align the canonical docs so they describe the same launch target and defer omnichannel scope explicitly.

**Tech Stack:** Markdown docs, repo governance docs, ripgrep/PowerShell verification, git

---

### Task 1: Rewrite The Task Ledger Around The V2 Program

**Files:**
- Modify: `docs/TASK_LEDGER.md`
- Reference: `docs/superpowers/specs/2026-04-15-v2-launch-program-design.md`

- [ ] **Step 1: Write the failing ledger assertions**

Run:

```powershell
rg -n "V2-001|V2-010|post-V2|omnichannel" docs/TASK_LEDGER.md
```

Expected: no matches, because the current ledger still ends at `CP-028`.

- [ ] **Step 2: Rewrite the ledger structure**

Update `docs/TASK_LEDGER.md` to:

- keep `CP-001` through `CP-027` unchanged as completed history
- rewrite `CP-028` as the transition task from the smaller launch target to the V2 launch program
- add a new `V2-*` task block with these top-level tasks:
  - `V2-001` Runtime surfaces
  - `V2-002` Barcode and device input
  - `V2-003` Advanced hardware
  - `V2-004` Store operations depth
  - `V2-005` Customer and commercial features
  - `V2-006` Staff and branch controls
  - `V2-007` Reporting and decision support
  - `V2-008` Vertical extensions
  - `V2-009` Hardening and scale
  - `V2-010` V2 launch readiness and cutover
- add a clearly marked post-V2 future-work section for omnichannel/e-commerce items

- [ ] **Step 3: Run the ledger assertions again**

Run:

```powershell
rg -n "V2-001|V2-010|post-V2|omnichannel" docs/TASK_LEDGER.md
```

Expected: matches for the new V2 task block and the future-work section.

- [ ] **Step 4: Commit the ledger rewrite**

```powershell
git add docs/TASK_LEDGER.md
git commit -m "docs: rewrite ledger for v2 launch program"
```

### Task 2: Align Canonical Docs To The V2 Launch Target

**Files:**
- Modify: `docs/PROJECT_CONTEXT.md`
- Modify: `docs/STORE_CANONICAL_BLUEPRINT.md`
- Reference: `docs/superpowers/specs/2026-04-15-v2-launch-program-design.md`

- [ ] **Step 1: Write the failing canonical-doc assertions**

Run:

```powershell
rg -n "V2 launch|mobile store app|inventory tablet|customer display|omnichannel" docs/PROJECT_CONTEXT.md docs/STORE_CANONICAL_BLUEPRINT.md
```

Expected: missing or incomplete matches, because the current canonical docs still describe the smaller launch endgame.

- [ ] **Step 2: Update `PROJECT_CONTEXT.md`**

Revise the product/delivery sections so they describe:

- V2 as the active launch target
- the broadened physical-retail scope
- the V2 capability families at a high level
- omnichannel/e-commerce as explicitly deferred future work

- [ ] **Step 3: Update `STORE_CANONICAL_BLUEPRINT.md`**

Revise the blueprint so it describes:

- the V2 enterprise physical-retail suite endgame
- the broadened runtime/device/hardware/commercial/vertical scope
- the fact that V2 still preserves the same architectural authority rules
- omnichannel as outside the current launch boundary

- [ ] **Step 4: Run the canonical-doc assertions again**

Run:

```powershell
rg -n "V2 launch|mobile store app|inventory tablet|customer display|omnichannel" docs/PROJECT_CONTEXT.md docs/STORE_CANONICAL_BLUEPRINT.md
```

Expected: clear matches in both files showing the new target/product boundary.

- [ ] **Step 5: Commit the canonical-doc alignment**

```powershell
git add docs/PROJECT_CONTEXT.md docs/STORE_CANONICAL_BLUEPRINT.md
git commit -m "docs: align canonical docs with v2 launch target"
```

### Task 3: Update Entry Points And Historical Record

**Files:**
- Modify: `docs/DOCS_INDEX.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Write the failing entrypoint assertions**

Run:

```powershell
rg -n "V2 launch|V2 program|future work" docs/DOCS_INDEX.md docs/WORKLOG.md
```

Expected: no V2 program framing yet.

- [ ] **Step 2: Update `DOCS_INDEX.md`**

Add or adjust references so contributors can find:

- the V2 program direction
- the revised ledger
- the canonical docs that now define the V2 target

- [ ] **Step 3: Update `WORKLOG.md`**

Add a dated entry describing:

- the V2 launch-program pivot
- the ledger rewrite
- the canonical-doc realignment
- the fact that omnichannel is now explicitly deferred

- [ ] **Step 4: Run the entrypoint assertions again**

Run:

```powershell
rg -n "V2 launch|V2 program|future work" docs/DOCS_INDEX.md docs/WORKLOG.md
```

Expected: clear matches describing the transition.

- [ ] **Step 5: Commit the entrypoint/history updates**

```powershell
git add docs/DOCS_INDEX.md docs/WORKLOG.md
git commit -m "docs: document v2 launch program transition"
```

### Task 4: Full Verification And Final Publish

**Files:**
- Modify: none
- Verify: `docs/TASK_LEDGER.md`
- Verify: `docs/PROJECT_CONTEXT.md`
- Verify: `docs/STORE_CANONICAL_BLUEPRINT.md`
- Verify: `docs/DOCS_INDEX.md`
- Verify: `docs/WORKLOG.md`

- [ ] **Step 1: Run diff hygiene**

Run:

```powershell
git diff --check
```

Expected: no whitespace or patch-format issues.

- [ ] **Step 2: Run final doc consistency checks**

Run:

```powershell
rg -n "V2-001|V2-010|post-V2|omnichannel" docs/TASK_LEDGER.md
rg -n "V2 launch|mobile store app|inventory tablet|customer display|omnichannel" docs/PROJECT_CONTEXT.md docs/STORE_CANONICAL_BLUEPRINT.md
rg -n "V2 launch|V2 program|future work" docs/DOCS_INDEX.md docs/WORKLOG.md
```

Expected: all commands return matches consistent with the V2 program rewrite.

- [ ] **Step 3: Review git status before final publish**

Run:

```powershell
git status --short --branch
```

Expected: only the intended doc files are modified.

- [ ] **Step 4: Commit the final verification pass if needed**

If any final wording changes were needed during verification:

```powershell
git add docs/TASK_LEDGER.md docs/PROJECT_CONTEXT.md docs/STORE_CANONICAL_BLUEPRINT.md docs/DOCS_INDEX.md docs/WORKLOG.md
git commit -m "docs: finalize v2 launch program rewrite"
```

- [ ] **Step 5: Push the completed rewrite**

```powershell
git push origin main
```
