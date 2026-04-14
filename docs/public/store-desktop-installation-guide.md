# Store Desktop Installation Guide

Updated: 2026-04-15

## Goal

Install the packaged Store Desktop runtime and bring it to an approved, usable branch state.

## Before Installation

Confirm:

- the tenant and first branch already exist
- the target Windows machine is intended for branch use
- the owner has owner-web access
- the installer came from the approved release channel

If you are the operator publishing installers, use [../runbooks/store-desktop-packaging-distribution.md](../runbooks/store-desktop-packaging-distribution.md).

## Install The Packaged App

1. run the approved Windows installer
2. open Store Desktop
3. note the installation/device identity shown by the packaged runtime

On first launch, the app may appear unbound or pending. That is expected.

## Approve The Device Claim

In owner-web:

1. open the branch device approval area
2. locate the pending packaged device claim
3. confirm the machine is the correct branch terminal
4. approve the claim into a branch device record

After approval, issue the branch staff activation for the target staff member.

## Complete Staff Activation

On the packaged desktop:

1. redeem the activation code while online
2. complete local branch sign-in setup as prompted
3. confirm the runtime opens successfully for the branch

If the runtime is intended to act as the branch hub, keep the machine stable and available for branch-local connectivity.

## After Activation

Confirm:

- branch identity is correct
- release profile is correct
- print/scanner configuration is correct if used
- runtime health is normal

## Common Failure Modes

- `claim still pending`
  - owner approval has not completed
- `activation denied`
  - wrong activation code, wrong device, expired activation, or branch/runtime policy denial
- `commercial access blocked`
  - tenant is in grace or suspended posture
- `runtime degraded after sign-in`
  - branch hub/runtime or sync posture needs review

If needed, continue to [troubleshooting-guide.md](./troubleshooting-guide.md).
