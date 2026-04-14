from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MutationConflictResult:
    accepted: bool
    conflict: bool
    next_version: int


def resolve_mutation_conflict(*, client_version: int, server_version: int) -> MutationConflictResult:
    if client_version < server_version:
        return MutationConflictResult(accepted=False, conflict=True, next_version=server_version)
    return MutationConflictResult(accepted=True, conflict=False, next_version=server_version + 1)


def build_pull_response(records: list[dict[str, object]]) -> dict[str, object]:
    ordered = sorted(records, key=lambda item: int(item["version"]))
    cursor = int(ordered[-1]["version"]) if ordered else 0
    return {"cursor": cursor, "records": ordered}
