# Release Consumer Known Issues

Updated: 2026-04-15

## Purpose

Track the first-release support posture for issues customers/support are likely to encounter.

## Current Known-Issue Themes

### Browser Preview Is Not A Production Runtime Sign-In Surface

- browser preview may still exist for dev/test workflows
- production branch sign-in should use packaged Store Desktop activation and runtime unlock

Support response:

- route the customer to packaged Store Desktop, not browser preview, for real branch use

### Store Desktop Update Publication Is Still Operator-Managed

- GitHub Actions can build signed installers, but update-manifest publication is still a manual operator step

Support response:

- if a customer expects an update that is not appearing, confirm the release was fully promoted to the final channel, not just built in CI

### Runtime Continuity Is Bounded

- offline continuity exists, but it is not unlimited branch autonomy
- replay/conflict posture may require operator review

Support response:

- collect branch/runtime screenshots and escalate if replay posture is unclear

### Commercial Lifecycle Blocks Are Intentional

- `GRACE` and `SUSPENDED` posture may intentionally restrict owner/runtime behavior

Support response:

- verify whether the commercial state is correct before treating the block as a product bug
