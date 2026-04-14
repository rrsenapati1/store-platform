# Troubleshooting Guide

Updated: 2026-04-15

## Start With These Details

Before troubleshooting, collect:

- tenant name
- branch name
- desktop release version if the issue is on Store Desktop
- screenshot of the error
- whether the issue is owner-web or Store Desktop

## Device Claim Is Still Pending

Symptoms:

- packaged Store Desktop does not become active
- owner-web still shows a pending claim

Check:

1. the device claim was approved in owner-web
2. the correct branch device was approved
3. the branch was already created before approval

If the claim never appears in owner-web, contact support.

## Activation Is Denied

Symptoms:

- packaged desktop rejects the activation code

Check:

1. the code has not expired
2. the code was issued for the same device
3. the target staff user is active for the branch
4. the tenant is not commercially blocked

If the denial message still does not make sense, contact support with the screenshot and device identity.

## Billing/Commercial Access Is Blocked

Symptoms:

- owner-web shows grace/suspension posture
- runtime sign-in/activation is blocked by commercial state

Check:

1. whether the tenant is in `TRIALING`, `GRACE`, or `SUSPENDED`
2. whether recurring billing recovery was already completed

If payment/provider state looks inconsistent, contact support.

## Runtime Is Degraded

Symptoms:

- Store Desktop shows degraded branch/runtime posture
- sync/runtime section reports problems

Check:

1. whether the branch hub is online
2. whether spoke/hub connectivity is healthy
3. whether there are pending replay/conflict items
4. whether print/scanner diagnostics are failing

## Update Or Upgrade Problems

Symptoms:

- pending update does not install
- packaged runtime does not restart cleanly after update

Check:

1. release channel is correct
2. the updater sees the expected pending version
3. reinstall only if normal update cannot recover the app

See [store-desktop-upgrade-and-recovery.md](./store-desktop-upgrade-and-recovery.md).

## When To Contact Support

Contact support if:

- the issue blocks onboarding or branch runtime and local checks do not resolve it
- the device claim or activation flow behaves inconsistently
- grace/suspension posture looks wrong
- runtime degradation persists after the obvious local checks
- offline continuity replay requires operator review and you do not know how to proceed
