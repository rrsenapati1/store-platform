# Owner-Web Operations Guide

Updated: 2026-04-15

## What Owner-Web Covers

Owner-web is the tenant owner control surface for Store.

Use it for:

- branch setup and branch device approvals
- staff directory management
- catalog and inventory control workflows
- purchasing/receiving and supplier finance workflows
- compliance and billing posture
- tenant subscription recovery when a tenant is in grace or suspended

## Daily Owner Checklist

Typical owner-side checks:

1. review branch/runtime health
2. review pending staff/device actions
3. review inventory, purchasing, and finance posture
4. review compliance/export posture if applicable
5. review commercial lifecycle posture if the tenant is near grace or suspension

## Device And Runtime Actions

Use owner-web to:

- review pending packaged device claims
- approve the correct branch devices
- issue branch staff activation for packaged Store Desktop

Do not treat browser preview flows as production runtime sign-in. Production branch runtime should use the packaged desktop activation path.

## Commercial Lifecycle Actions

If the tenant is:

- `TRIALING`
  - complete recurring subscription setup before trial expiry
- `ACTIVE`
  - continue normal operations
- `GRACE`
  - recover billing quickly before suspension
- `SUSPENDED`
  - resolve billing/subscription state before expecting normal owner/runtime access

If billing posture is unclear, see [troubleshooting-guide.md](./troubleshooting-guide.md).

## Operator Notes

- Owner-web is the right place for tenant/business control.
- Store Desktop is the right place for branch runtime/cashier activity.
- Platform-admin is reserved for the Store operator team, not normal tenant operations.

## Next References

- New branch runtime setup: [store-desktop-installation-guide.md](./store-desktop-installation-guide.md)
- Desktop update/recovery: [store-desktop-upgrade-and-recovery.md](./store-desktop-upgrade-and-recovery.md)
- Troubleshooting: [troubleshooting-guide.md](./troubleshooting-guide.md)
