from __future__ import annotations

from pydantic import BaseModel


class AuthorityBoundaryResponse(BaseModel):
    control_plane_service: str
    legacy_service: str
    cutover_phase: str
    legacy_write_mode: str
    migrated_domains: list[str]
    legacy_remaining_domains: list[str]
    shutdown_criteria: list[str]
    shutdown_steps: list[str]

