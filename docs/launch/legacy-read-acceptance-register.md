# Legacy Read Acceptance Register

Updated: 2026-04-15

This register records any explicitly accepted residual dependency on the legacy retail API at launch time.

## Current Expected State

The current control-plane authority boundary expects:

- `legacy_remaining_domains = []`
- migrated writes blocked by `cutover`

So the preferred state for launch is:

- no accepted legacy reads

## Accepted Exceptions

At the time of writing, there are no accepted residual legacy-read dependencies for launch.

If a residual read must be accepted later, add one entry per dependency with:

- area:
- legacy endpoint/service:
- customer impact:
- rationale for temporary acceptance:
- owner:
- target removal release:

## Launch Rule

If this file contains any active exception entries, the release candidate must not be described as “full legacy retirement” in launch communications.
