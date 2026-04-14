# Store Product Overview

Updated: 2026-04-15

## What Store Is

Store is a multi-tenant retail platform designed for India-first branch operations with a packaged desktop runtime and a control-plane backend.

At a release-consumer level, the product has three main surfaces:

- `platform-admin`
  - used by the Store operator team to create and manage tenant accounts
- `owner-web`
  - used by tenant owners to manage branches, staff, devices, catalog, purchasing, billing/compliance, and commercial lifecycle
- `Store Desktop`
  - used in-branch for cashier/runtime work, printing, scanning, branch-hub operations, and bounded offline continuity

## What A New Tenant Should Expect

The normal first-use sequence is:

1. Store operator creates the tenant and sends the owner invite.
2. Tenant owner signs in and completes first-branch setup.
3. Tenant owner creates staff and approves the first packaged Store Desktop device claim.
4. Staff activates the approved desktop and signs in with the branch-runtime flow.
5. Branch starts normal runtime operations.

For the detailed tenant flow, continue to [tenant-onboarding-guide.md](./tenant-onboarding-guide.md).

## What Owner-Web Is For

Owner-web is the main business control surface for a tenant owner. It is where the owner manages:

- branch setup
- staff directory and memberships
- branch device approvals
- catalog and inventory controls
- purchasing and supplier workflows
- billing/compliance posture
- subscription/grace/suspension recovery

For day-to-day owner actions, continue to [owner-web-operations-guide.md](./owner-web-operations-guide.md).

## What Store Desktop Is For

Store Desktop is the packaged branch runtime. Depending on branch setup, it can act as:

- the primary cashier runtime
- the approved branch hub for spoke devices
- the local print/scanner surface
- the bounded offline continuity surface when cloud connectivity is lost

For installation and activation, continue to [store-desktop-installation-guide.md](./store-desktop-installation-guide.md).

## Where To Go Next

- New tenant setup: [tenant-onboarding-guide.md](./tenant-onboarding-guide.md)
- Owner daily operations: [owner-web-operations-guide.md](./owner-web-operations-guide.md)
- Desktop install and activation: [store-desktop-installation-guide.md](./store-desktop-installation-guide.md)
- Desktop update/recovery: [store-desktop-upgrade-and-recovery.md](./store-desktop-upgrade-and-recovery.md)
- Recovery and backup expectations: [backup-and-recovery-guide.md](./backup-and-recovery-guide.md)
- Common issues: [troubleshooting-guide.md](./troubleshooting-guide.md)
