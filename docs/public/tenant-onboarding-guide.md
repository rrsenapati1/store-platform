# Tenant Onboarding Guide

Updated: 2026-04-15

## Goal

This guide takes a new tenant from account creation to a usable first branch.

## Before You Start

You should already have:

- a tenant created by the Store operator team
- the owner invitation or owner sign-in link
- branch business details ready
- at least one Windows machine intended for Store Desktop

## Step 1: Owner Sign-In

Open the owner sign-in link from the Store operator team and complete the owner sign-in flow.

When successful, owner-web should show your tenant and first-branch setup posture.

## Step 2: Create The First Branch

In owner-web, complete first-branch setup with:

- branch name
- GST/business details as applicable
- branch location details

The branch must exist before staff/device activation can complete.

## Step 3: Add Staff

In owner-web, create the first staff records needed for runtime use.

Recommended minimum:

- one branch manager or primary owner-side operator
- one cashier/runtime user for the first terminal

The packaged desktop runtime uses approved-device activation plus local branch sign-in; it does not rely on a normal staff web-login flow.

## Step 4: Install Store Desktop

Install the packaged Store Desktop app on the first branch machine.

The packaged runtime will show an installation identity / claim posture rather than becoming active immediately.

Continue with [store-desktop-installation-guide.md](./store-desktop-installation-guide.md) for the detailed device flow.

## Step 5: Approve The First Device

In owner-web:

1. open the branch device area
2. review the pending packaged device claim
3. approve the device into the branch
4. issue the branch staff activation

The branch staff member then completes packaged desktop activation on that machine.

## Step 6: Verify Runtime Readiness

Before starting real branch operations, confirm:

- branch device is approved
- staff activation completed successfully
- Store Desktop shows the expected branch/runtime posture
- printer/scanner configuration is ready if used

## After Onboarding

Once the first branch is active, use:

- [owner-web-operations-guide.md](./owner-web-operations-guide.md) for owner-side workflows
- [troubleshooting-guide.md](./troubleshooting-guide.md) if activation or runtime posture is blocked

## When To Contact Support

Contact support if:

- the owner invitation no longer works
- branch setup cannot complete
- device claims never appear in owner-web
- packaged desktop activation is denied and you cannot identify the cause locally
- commercial suspension/grace posture blocks onboarding unexpectedly
