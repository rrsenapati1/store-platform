# Store Desktop Upgrade And Recovery

Updated: 2026-04-15

## Normal Update Path

Store Desktop uses explicit release profiles and signed updater artifacts.

For normal update flow:

1. confirm the branch is on the intended release channel
2. check the release/update posture from the packaged runtime
3. apply the pending update
4. restart the runtime if required
5. confirm the new version and branch posture after restart

For operator-side release publishing, use [../runbooks/store-desktop-packaging-distribution.md](../runbooks/store-desktop-packaging-distribution.md).

## When Reinstall Is Appropriate

Reinstall only when:

- the packaged runtime is damaged or missing files
- the updater cannot recover the current installation safely
- support instructs you to replace the installed build with a known-good version

Reinstall is not the first response to ordinary branch/runtime errors.

## Recovery Checks After Update Or Reinstall

After an update or reinstall, verify:

- the runtime shows the correct release environment
- branch identity is still correct
- approval/binding posture is still correct
- local sign-in/runtime unlock still works
- print/scanner diagnostics are healthy if used

## Rollback Guidance

If a newly published version must be rolled back:

- operators should re-point the release/update channel to the previous trusted installer and signature
- already updated machines may require manual reinstall depending on downgrade posture

This rollback path is operator-controlled. It is not fully automated.

## When To Escalate

Escalate if:

- the packaged runtime cannot start after update
- the release profile appears wrong for the environment
- the runtime loses approval/binding unexpectedly
- recovery requires repeated reinstall without stabilizing the branch
