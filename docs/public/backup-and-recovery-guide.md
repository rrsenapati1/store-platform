# Backup And Recovery Guide

Updated: 2026-04-15

## What This Guide Covers

This guide explains the release-consumer view of Store recovery.

Store uses:

- control-plane backend backups and restore procedures owned by operators
- packaged branch runtimes that can continue through bounded offline continuity in some scenarios

## What Tenants Should Expect

- Control-plane backups are handled by the Store operator team.
- Store Desktop can continue certain bounded runtime actions locally when the cloud is unavailable, but it is not a substitute for full backend recovery.
- Recovery of tenant/account/commercial state remains a control-plane responsibility.

## If The Cloud Is Unavailable

Branch behavior depends on the runtime state:

- some checkout-critical flows may continue through bounded offline continuity
- queued replay/conflict posture must be allowed to reconcile after connectivity returns
- not every branch action is available offline

If cloud availability is lost for an extended time, contact support with:

- tenant name
- branch name
- current desktop release version
- screenshots of runtime continuity/degradation posture

## If A Desktop Machine Fails

Use the packaged desktop recovery flow:

1. replace or repair the machine
2. reinstall the approved Store Desktop build
3. approve/bind the new device if required
4. complete activation again for the new branch machine

## Operator-Controlled Recovery

If you are part of the operator/admin team, use the dedicated runbooks:

- [../runbooks/control-plane-backup-restore.md](../runbooks/control-plane-backup-restore.md)
- [../runbooks/control-plane-production-deployment.md](../runbooks/control-plane-production-deployment.md)

This public guide is intentionally high-level; it does not replace the operator recovery runbooks.
